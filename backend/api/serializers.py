import base64

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.timezone import now
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Favorite, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Subscription, Tag, User)
from recipes.validators import (validate_amount, validate_cooking_time,
                                validate_image)
from rest_framework import serializers

#
# class MyUserCreateSerializer(UserCreateSerializer):
#
#     class Meta:
#         model = User
#         fields = (
#             'email', 'id', 'username', 'first_name',
#             'last_name', 'password',
#         )
#         extra_kwargs = {
#             'password': {'write_only': True}
#         }


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


class ImageDecodedField(serializers.ImageField):
    """
    Декодирует строку из base64 и возвращает объект-обертку
     для дальнейшего сохранения в виде файла.
    """

    def to_internal_value(self, image):
        """Разбивает по ;base64, на заголовок и строковый код картинки."""

        if not image:
            return None
        if isinstance(image, str) and image.startswith('data:image'):
            header, imagestr = image.split(';base64,')
            extension = header.split('/')[-1]
            str_now_time = str(now().time())
            filename = f'image_{str_now_time}.{extension}'
            image = ContentFile(base64.b64decode(imagestr), name=filename)
        return super().to_internal_value(image)


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
    author = FoodgramUserSerializer(read_only=True, )
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
            return Favorite.objects.filter(
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

    def validate(self, data):
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
        return data


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
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Это рецепт уже добавлен в список покупок.'
            )
        ]


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
        model = Favorite
        fields = '__all__'
        read_only_fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже в избранном.'
            )
        ]


class FavoriteRecipeReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


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


class SubscribeReadSerializer(FoodgramUserSerializer):

    recipes = FavoriteRecipeReadSerializer(
        read_only=True,
        many=True
    )
    recipes_count = serializers.SerializerMethodField()

    class Meta(FoodgramUserSerializer.Meta):
        model = User
        fields = FoodgramUserSerializer.Meta.fields + ('recipes', 'recipes_count',)

    def get_recipes_count(self, author):
        return Recipe.objects.filter(author=author).count()

    def to_representation(self, author):
        """Обрабатывает ?recipes_limit= из url."""
        result_dict = super().to_representation(author)
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
