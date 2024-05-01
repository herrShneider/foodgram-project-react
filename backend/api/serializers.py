import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework import serializers

from recipes.models import FavoriteRecipe, Ingredient, IngredientRecipe, Recipe, ShoppingCart, Subscription, Tag, User


class UserSerializer(serializers.ModelSerializer):
    """Базовая модель сериалайзера для модели User."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        """Meta-класс."""

        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password', 'is_subscribed'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(subscriber=request.user, subscription=obj).exists()
        return False


class UserProfileSerializer(serializers.ModelSerializer):
    """Базовая модель сериалайзера для модели User."""

    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        """Meta-класс."""

        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password', 'is_subscribed'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'
####################################################################################################


class ImageDecodedField(serializers.ImageField):
    """Декодирует строку из base64 и возвращает объект-обертку для дальнейшего сохранения в виде файла."""

    def to_internal_value(self, data):
        """Разбивает данные по ;base64, на заголовок и строковый код картинки."""
        header, imagestr = data.split(';base64,')
        extension = header.split('/')[-1]
        str_now_time = str(now().time())
        filename = f'image_{str_now_time}.{extension}'
        return ContentFile(base64.b64decode(imagestr), name=filename)

####################################################################################################


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
        result_dict['ingredients'] = IngredientRecipeReadSerializer(instance.ingredientsrecipes.all(), many=True).data
        return result_dict

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return FavoriteRecipe.objects.filter(user=request.user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        return False


class IngredientRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
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
    image = ImageDecodedField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)
        read_only_fields = ('author',)


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
        """Функция проверки данных."""
        if self.context['request'].method != 'POST':
            return data
        user = self.context.get('request').user
        recipe = data.get('recipe')
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Это рецепт уже добавлен в список покупок.'
            )
        return data


class ShoppingCartReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
