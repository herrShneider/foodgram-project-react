from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import mixins, serializers, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .serializers import (IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, ShoppingCartReadSerializer,
                          ShoppingCartWriteSerializer, TagSerializer,
                          UserSerializer, UserProfileSerializer, )
from config import URL_PROFILE_PREF, URL_SET_PASSWORD
from recipes.models import FavoriteRecipe, Ingredient, IngredientRecipe, Recipe, ShoppingCart, Subscription, Tag, TagRecipe, User

HTTP_METHODS = ('get', 'post', 'patch', 'delete')
URL_SHOPPING_CART = 'shopping_cart'


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы администратора с users."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    # lookup_field = 'username'
    # filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    http_method_names = ('get', 'post',)
    # search_fields = ('username',)

    def get_serializer_context(self):
        """Передаёт объекта запроса в контекст сериализатора."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path=URL_PROFILE_PREF,
    )
    def get_users_profile(self, request):
        """Обрабатывает GET запросы при обращению к профайлу."""
        return Response(UserProfileSerializer(request.user).data)

    @action(
        detail=False,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path=URL_SET_PASSWORD,
    )
    def set_password(self, request):
        """Обрабатывает POST запрос на изменение пароля."""

        current_user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        for field_name in ('current_password', 'new_password'):
            if request.data.get(field_name) is None:
                raise ValidationError(
                    {
                        f'{field_name}': [
                            'Обязательное поле.'
                        ]
                    }
                )
        user = authenticate(
            username=current_user.email,
            password=current_password
        )
        if user is not None:
            serializer = UserProfileSerializer(
                user,
                data={'password': new_password},
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({'message': 'Пароль успешно изменен'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': 'Неверный текущий пароль'}, status=status.HTTP_401_UNAUTHORIZED)


class RecipeViewSet(viewsets.ModelViewSet):

    http_method_names = HTTP_METHODS
    serializer_class = RecipeReadSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def get_serializer_context(self):
        """Передаёт объекта запроса в контекст сериализатора."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        return Recipe.objects.prefetch_related('tags')

    def create(self, request, *args, **kwargs):
        serializer = RecipeWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ingredients_data = serializer.validated_data.pop('ingredients')
        tags_data = serializer.validated_data.pop('tags')
        recipe = Recipe.objects.create(author=self.request.user, **serializer.validated_data)
        for ingredient_data in ingredients_data:
            IngredientRecipe.objects.create(
                ingredient=ingredient_data['id'],
                recipe=recipe,
                amount=ingredient_data['amount']
            )
        recipe.tags.set(tags_data)
        serializer = RecipeReadSerializer(instance=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        serializer = RecipeWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ingredients_data = serializer.validated_data.pop('ingredients')
        tags_data = serializer.validated_data.pop('tags')
        get_object_or_404(Recipe, pk=self.kwargs.get('pk'))
        Recipe.objects.filter(pk=self.kwargs.get('pk')).update(**serializer.validated_data)
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('pk'))
        IngredientRecipe.objects.filter(recipe=recipe).delete()
        for ingredient_data in ingredients_data:
            IngredientRecipe.objects.create(
                ingredient=ingredient_data['id'],
                recipe=recipe,
                amount=ingredient_data['amount']
            )
        recipe.tags.set(tags_data)
        serializer = RecipeReadSerializer(instance=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # @action(
    #     detail=False,
    #     methods=('post', 'delete'),
    #     permission_classes=(IsAuthenticated,),
    #     url_path=URL_SHOPPING_CART,
    # )
    # def add_delete_recipe_to_shopping_cart(self):
    #     print('add_delete_recipe_to_shopping_cart')
    #     recipe = get_object_or_404(Recipe, pk=self.kwargs.get('pk'))
    #     if self.request.method == 'POST':
    #         serializer = ShoppingCartSerializer(data={'user': self.request.user.pk, 'recipe': recipe.pk})
    #         serializer.is_valid(raise_exception=True)
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     instance = get_object_or_404(ShoppingCart, user=self.request.user, recipe=recipe)
    #     instance.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class ShoppingCartViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):

    serializer_class = ShoppingCartWriteSerializer
    queryset = ShoppingCart.objects.all()
    http_method_names = ('post', 'delete')
    pagination_class = None
    lookup_field = 'recipe_id'

    def get_recipe(self):
        return get_object_or_404(Recipe, pk=self.kwargs.get('recipe_id'))

    def create(self, request, *args, **kwargs):
        recipe = self.get_recipe()
        serializer = ShoppingCartWriteSerializer(
            data={'user': request.user.pk, 'recipe': recipe.pk},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = ShoppingCartReadSerializer(instance=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
