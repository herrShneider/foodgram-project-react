from rest_framework import serializers

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag, TagRecipe, User


class UserSerializer(serializers.ModelSerializer):
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


class IngredientRecipeSerializer(serializers.ModelSerializer):

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


class RecipeListRetrieveSerializer(serializers.ModelSerializer):
    """Сериализатор для неаутентифицированного юзера."""

    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(many=True)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def to_representation(self, instance):
        result_dict = super().to_representation(instance)
        result_dict['ingredients'] = IngredientRecipeSerializer(instance.ingredientsrecipes.all(), many=True).data
        return result_dict


class RecipeListRetrieveAuthSerializer(serializers.ModelSerializer):
    """Сериализатор для аутентифицированного юзера."""

    tags = TagSerializer(many=True)
    # ingredients = IngredientRecipeSerializer(many=True)
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def to_representation(self, instance):
        result_dict = super().to_representation(instance)
        result_dict['ingredients'] = IngredientRecipeSerializer(instance.ingredientsrecipes.all(), many=True).data
        return result_dict


class RecipeCreateUpdateIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        # source='id',
        # read_only=True,
    )
    # amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')
        # read_only_fields = ('recipe',)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    ingredients = RecipeCreateUpdateIngredientSerializer(
        many=True,
    )

    class Meta:
        model = Recipe
        exclude = ('pub_date',)
        read_only_fields = ('author',)

    def create(self, validated_data):
        print('validated_data', validated_data)
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            IngredientRecipe.objects.create(
                ingredient=ingredient_data['id'],
                recipe=recipe,
                amount=ingredient_data['amount']
            )
            # print('ingredient_data', ingredient_data)
            # # Получаем объект ингредиента, который вернул сериалайзер
            # ingredient = ingredient_data.pop('id')
            # print('ingredient=', ingredient, type(ingredient))
            # amount = ingredient_data.pop('amount')
            # print('amount=', amount)
            # IngredientRecipe.objects.create(ingredient=ingredient, recipe=recipe, amount=amount)
        recipe.tags.set(tags_data)
        return recipe

    # def update(self, instance, validated_data):
    #     pass

    # def to_representation(self, instance):
    #     result_dict = super().to_representation(instance)
    #     result_dict['tags'] = TagSerializer(instance.tags.all(), many=True).data
    #     result_dict['ingredients'] = IngredientRecipeSerializer(instance.ingredientsrecipes.all(), many=True).data
    #     return result_dict

    def to_representation(self, instance):
        result_dict = super().to_representation(instance)
        result_dict['ingredients'] = IngredientRecipeSerializer(instance.ingredientsrecipes.all(), many=True).data
        return result_dict


