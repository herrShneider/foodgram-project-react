from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Subscription, Tag, User)


class FoodgramUserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta:

        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed',
        )

    def get_is_subscribed(self, author):
        request = self.context['request']
        if request.user.is_authenticated:
            return (request.user.subscription_as_subscriber
                    .filter(author=author).exists())
        return False


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeReadSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(
        source='ingredient.id',
        read_only=True
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(
        many=True,
        read_only=True,
    )
    author = FoodgramUserSerializer(
        read_only=True,
    )
    ingredients = IngredientRecipeReadSerializer(
        source='ingredientsrecipes',
        many=True,
        read_only=True
    )
    image = Base64ImageField()
    #  Не удалось избавиться от SerializerMethodField потому,
    #  что RecipeReadSerializer используется в to_representation
    #  в RecipeWriteSerializer. А там instance передается без
    #  этих полей. Поэтому в этих методах я тольео проверяю есть
    #  ли у объекта Recipe поля если есть - вывожу значение, если
    #  нет - вывожу False.
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def get_is_favorited(self, obj):
        return getattr(obj, 'is_favorited', False)

    def get_is_in_shopping_cart(self, obj):
        return getattr(obj, 'is_in_shopping_cart', False)


class IngredientRecipeWriteSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(
        source='ingredient.id'
    )
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1,
                message='Значение должно быть больше 1'
            ),
            MaxValueValidator(
                32767,
                message='Значение должно быть меньше 32767'
            ),
        )
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = IngredientRecipeWriteSerializer(
        many=True,
    )
    image = Base64ImageField(
        required=True,
        allow_null=False,
        allow_empty_file=False,
    )
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1,
                message='Значение должно быть больше 1'
            ),
            MaxValueValidator(
                32767,
                message='Значение должно быть меньше 32767'
            ),
        )
    )

    class Meta:
        model = Recipe
        exclude = ('pub_date',)
        read_only_fields = ('author',)

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise ValidationError('Поле ingredients не может быть пустым.')
        ingredients_ids = [item['ingredient']['id'] for item in ingredients]
        unique_ingredients_ids = set(ingredients_ids)
        if len(unique_ingredients_ids) < len(ingredients_ids):
            raise ValidationError('Вы передали один из ингредиентов дважды.')
        tags = data.get('tags')
        if not tags:
            raise ValidationError('Поле tags не может быть пустым.')
        unique_tags = set(tags)
        if len(unique_tags) < len(tags):
            raise ValidationError('Вы передали один из тегов дважды.')
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['ingredient']['id']
            ingredient = Ingredient.objects.get(pk=ingredient_id)
            IngredientRecipe.objects.create(
                ingredient=ingredient,
                recipe=recipe,
                amount=ingredient_data['amount']
            )
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        if 'image' not in self.context['request'].data:
            validated_data['image'] = instance.image
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        IngredientRecipe.objects.filter(recipe=instance).delete()
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['ingredient']['id']
            ingredient = Ingredient.objects.get(pk=ingredient_id)
            IngredientRecipe.objects.create(
                ingredient=ingredient,
                recipe=instance,
                amount=ingredient_data['amount']
            )
        instance.tags.set(tags_data)
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeForFavoriteShoppingCartSubscribeSerializer(
    serializers.ModelSerializer
):

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteShoppingCartSerializer(serializers.ModelSerializer):

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
    )

    class Meta:
        abstract = True
        fields = '__all__'
        read_only_fields = ('user', 'recipe')

    def validate(self, data):
        if self.Meta.model.objects.filter(
                user=data['user'],
                recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                f'Объект уже добавлен в {self.Meta.model._meta.verbose_name}'
            )
        return data

    def create(self, validated_data):
        object_to_write = self.Meta.model.objects.create(
            user=validated_data['user'],
            recipe=validated_data['recipe']
        )
        return object_to_write

    def to_representation(self, instance):
        return RecipeForFavoriteShoppingCartSubscribeSerializer(
            instance.recipe,
            context=self.context
        ).data


class FavoriteSerializer(FavoriteShoppingCartSerializer):

    class Meta(FavoriteShoppingCartSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(FavoriteShoppingCartSerializer):

    class Meta(FavoriteShoppingCartSerializer.Meta):
        model = ShoppingCart


class SubscribeWriteSerializer(serializers.ModelSerializer):

    subscriber = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )

    class Meta:

        model = Subscription
        fields = ('subscriber', 'author')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('subscriber', 'author'),
                message='Эта подписка уже существует.'
            )
        ]

    def validate_subscription(self, author):
        subscriber = self.context['request'].user
        if subscriber == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!'
            )
        return author

    def create(self, validated_data):
        subscription = Subscription.objects.create(
            subscriber=validated_data['subscriber'],
            author=validated_data['author']
        )
        return subscription

    def to_representation(self, instance):
        author = instance.author
        author.recipes_count = Recipe.objects.filter(author=author).count()
        return SubscribeReadSerializer(
            author,
            context=self.context
        ).data


class SubscribeReadSerializer(FoodgramUserSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField()

    class Meta(FoodgramUserSerializer.Meta):
        model = User
        fields = (FoodgramUserSerializer.Meta.fields
                  + ('recipes', 'recipes_count',))

    def get_recipes(self, author):
        """Обрабатывает ?recipes_limit= из url."""
        request = self.context['request']
        queryset = Recipe.objects.filter(author=author)
        if request.query_params.get('recipes_limit'):
            try:
                value = int(request.query_params.get('recipes_limit'))
                queryset = queryset[:value]
            except Exception:
                raise serializers.ValidationError(
                    'Лимит рецептов должен быть целым числом.'
                )
        return RecipeForFavoriteShoppingCartSubscribeSerializer(
            queryset,
            many=True,
            context=self.context
        ).data
