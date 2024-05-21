from django.core.exceptions import ValidationError
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from config import (AMOUNT_MAX_VALUE, AMOUNT_MIN_VALUE,
                    COOK_TIME_MAX_VALUE, COOK_TIME_MIN_VALUE)
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
        return (request
                and request.user.is_authenticated
                and request.user.subscription_as_subscriber.filter(
                    author=author
                ).exists())


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
    is_favorited = serializers.BooleanField(default=0)
    is_in_shopping_cart = serializers.BooleanField(default=0)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class IngredientRecipeWriteSerializer(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        min_value=AMOUNT_MIN_VALUE,
        max_value=AMOUNT_MAX_VALUE,
        error_messages={
            'min_value': f'Значение должно быть больше {AMOUNT_MIN_VALUE}',
            'max_value': f'Значение должно быть меньше {AMOUNT_MAX_VALUE}',
        }
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
        min_value=COOK_TIME_MIN_VALUE,
        max_value=COOK_TIME_MAX_VALUE,
        error_messages={
            'min_value': f'Значение должно быть больше {COOK_TIME_MIN_VALUE}',
            'max_value': f'Значение должно быть меньше {COOK_TIME_MAX_VALUE}',
        }
    )

    class Meta:
        model = Recipe
        exclude = ('pub_date',)
        read_only_fields = ('author',)

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise ValidationError(
                {'ingredients': 'Поле ingredients не может быть пустым.'}
            )
        ingredients_ids = [item['id'].id for item in ingredients]
        unique_ingredients_ids = set(ingredients_ids)
        if len(unique_ingredients_ids) < len(ingredients_ids):
            raise ValidationError(
                {'ingredients': 'Вы передали один из тегов дважды.'}
            )
        tags = data.get('tags')
        if not tags:
            raise ValidationError(
                {'tags': 'Поле tags не может быть пустым.'}
            )
        unique_tags = set(tags)
        if len(unique_tags) < len(tags):
            raise ValidationError(
                {'tags': 'Вы передали один из тегов дважды.'}
            )
        return data

    @staticmethod
    def create_ingredient_recipe_object(ingredients_data, recipe):
        ingredient_recipe_data = []
        for ingredient_data in ingredients_data:
            ingredient_recipe_data.append(
                IngredientRecipe(
                    ingredient_id=ingredient_data['id'].id,
                    recipe=recipe,
                    amount=ingredient_data['amount']
                )
            )
        IngredientRecipe.objects.bulk_create(ingredient_recipe_data)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        self.create_ingredient_recipe_object(ingredients_data, recipe)
        recipe.tags.set(tags_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        IngredientRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredient_recipe_object(ingredients_data, instance)
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

    class Meta:
        abstract = True
        fields = ('user', 'recipe')

    def validate(self, data):
        if self.Meta.model.objects.filter(
                user=data['user'],
                recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                {
                    'non_field_errors':
                        f'Уже добавлен в {self.Meta.model._meta.verbose_name}'
                }
            )
        return data

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

    class Meta:

        model = Subscription
        fields = ('subscriber', 'author')
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('subscriber', 'author'),
                message='Эта подписка уже существует.'
            ),
        )

    def validate(self, data):
        subscriber = self.context['request'].user
        if subscriber == data['author']:
            raise serializers.ValidationError(
                {'non_field_errors': 'Нельзя подписаться на самого себя!'}
            )
        return data

    def to_representation(self, instance):
        author = instance.author
        author.recipes_count = author.recipes.all().count()
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
        queryset = author.recipes.all()
        value = request.query_params.get('recipes_limit')
        if value:
            try:
                queryset = queryset[:int(value)]
            except ValueError:
                raise serializers.ValidationError(
                    {'recipes_limit': 'Лимит должен быть целым числом.'}
                )
        return RecipeForFavoriteShoppingCartSubscribeSerializer(
            queryset,
            many=True,
            context=self.context
        ).data
