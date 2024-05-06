import base64

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.timezone import now
from rest_framework import serializers

from recipes.models import (FavoriteRecipe, Ingredient,
                            IngredientRecipe, Recipe,
                            ShoppingCart, Subscription,
                            Tag, User)
from recipes.validators import (validate_amount, validate_cooking_time,
                                validate_image)


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password',
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }


class UserSerializer(UserCreateSerializer):

    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserCreateSerializer.Meta):

        fields = UserCreateSerializer.Meta.fields + ('is_subscribed',)

    def get_is_subscribed(self, user_subscribed_to):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                subscriber=request.user,
                subscription=user_subscribed_to
            ).exists()
        return False


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class ImageDecodedField(serializers.ImageField):
    """
    Декодирует строку из base64 и возвращает объект-обертку
     для дальнейшего сохранения в виде файла.
     """

    def to_internal_value(self, data):
        """Разбивает по ;base64, на заголовок и строковый код картинки."""
        if not data:
            return None
        header, imagestr = data.split(';base64,')
        extension = header.split('/')[-1]
        str_now_time = str(now().time())
        filename = f'image_{str_now_time}.{extension}'
        return ContentFile(
            base64.b64decode(imagestr),
            name=filename
        )


class IngredientRecipeReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = IngredientRecipe
        fields = '__all__'

    def to_representation(self, instance):
        result_dict = super().to_representation(instance)
        del result_dict['id']
        del result_dict['recipe']
        del result_dict['ingredient']
        result_dict['id'] = instance.ingredient.id
        result_dict['name'] = instance.ingredient.name
        result_dict['measurement_unit'] = instance.ingredient.measurement_unit
        result_dict.move_to_end('amount')
        return result_dict


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True,)
    image = ImageDecodedField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def to_representation(self, instance):
        """Изменяет вид поля ingredients в ответе."""
        result_dict = super().to_representation(instance)
        result_dict['ingredients'] = IngredientRecipeReadSerializer(
            instance.ingredientsrecipes.all(),
            many=True
        ).data
        return result_dict

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteRecipe.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user,
                recipe=obj
            ).exists()
        return False


class IngredientRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )
    amount = serializers.IntegerField(
        validators=(validate_amount,)
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
    image = ImageDecodedField(
        validators=(validate_image,)
    )
    cooking_time = serializers.IntegerField(
        validators=(validate_cooking_time,)
    )

    class Meta:
        model = Recipe
        exclude = ('pub_date',)
        read_only_fields = ('author',)

    def validate(self, attrs):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise ValidationError('Поле ingredients не может быть пустым.')
        ingredients_ids = [ingredient['id'] for ingredient in ingredients]
        unique_ingredients_ids = set(ingredients_ids)
        if len(unique_ingredients_ids) < len(ingredients_ids):
            raise ValidationError('Вы передали один из ингредиентов дважды.')
        tags = self.initial_data.get('tags')
        if not tags:
            raise ValidationError('Поле tags не может быть пустым.')
        unique_tags = set(tags)
        if len(unique_tags) < len(tags):
            raise ValidationError('Вы передали один из тегов дважды.')
        return attrs


class ShoppingCartWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
    )

    class Meta:
        model = ShoppingCart
        fields = '__all__'
        read_only_fields = ('user', 'recipe')

    def validate(self, data):
        if self.context['request'].method != 'POST':
            return data
        user = self.context.get('request').user
        recipe = data.get('recipe')
        if ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                'Это рецепт уже добавлен в список покупок.'
            )
        return data


class ShoppingCartReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteRecipeWriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
    )

    class Meta:
        model = FavoriteRecipe
        fields = '__all__'
        read_only_fields = ('user', 'recipe')

    def validate(self, data):
        if self.context['request'].method != 'POST':
            return data
        user = self.context.get('request').user
        recipe = data.get('recipe')
        if FavoriteRecipe.objects.filter(
                user=user,
                recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                'Это рецепт уже добавлен в список покупок.'
            )
        return data


class FavoriteRecipeReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeWriteSerializer(serializers.ModelSerializer):

    subscriber = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    subscription = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )

    class Meta:

        model = Subscription
        fields = ('subscriber', 'subscription')

    def validate_subscription(self, user_subscribed_to):
        subscriber = self.context['request'].user

        if subscriber == user_subscribed_to:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!'
            )

        if subscriber.subscription_as_subscriber.filter(
                subscription=user_subscribed_to
        ):
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )

        return user_subscribed_to


class SubscribeReadSerializer(UserSerializer):

    recipes = FavoriteRecipeReadSerializer(
        read_only=True,
        many=True
    )
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count',)

    def get_recipes_count(self, user_subscribed_to):
        return Recipe.objects.filter(author=user_subscribed_to).count()

    def to_representation(self, user_subscribed_to):
        """Обрабатывает ?recipes_limit= из url."""
        result_dict = super().to_representation(user_subscribed_to)
        request = self.context.get('request')
        if request.query_params.get('recipes_limit'):
            try:
                value = int(request.query_params.get('recipes_limit'))
            except Exception:
                raise serializers.ValidationError(
                    'Лимит рецептов должен быть целым числом.'
                )
            result_dict['recipes'] = result_dict['recipes'][:value]
        return result_dict
