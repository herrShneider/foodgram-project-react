
from config import (HTTP_METHODS, URL_DOWNLOAD_SHOPPING_CART, URL_PROFILE_PREF,
                    URL_SET_PASSWORD)
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views as djoser_views
from recipes.models import (Favorite, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Subscription, Tag, User)
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from . import permissions
from .filters import IngredientSetFilter, RecipeSetFilter
from .permissions import IsAuthorOrReadCreate
from .serializers import (FavoriteRecipeReadSerializer,
                          FavoriteRecipeWriteSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          ShoppingCartReadSerializer,
                          ShoppingCartWriteSerializer, SubscribeReadSerializer,
                          SubscribeWriteSerializer, TagSerializer)


class FoodgramUserViewSet(djoser_views.UserViewSet):

    http_method_names = ('get', 'post',)
    filter_backends = (DjangoFilterBackend,)

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()


class RecipeViewSet(viewsets.ModelViewSet):

    http_method_names = HTTP_METHODS
    serializer_class = RecipeReadSerializer
    permission_classes = (IsAuthorOrReadCreate,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeSetFilter

    def get_serializer_context(self):
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
        recipe = Recipe.objects.create(
            author=self.request.user,
            **serializer.validated_data
        )
        for ingredient_data in ingredients_data:
            IngredientRecipe.objects.create(
                ingredient=ingredient_data['id'],
                recipe=recipe,
                amount=ingredient_data['amount']
            )
        recipe.tags.set(tags_data)
        serializer = RecipeReadSerializer(
            instance=recipe,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        serializer = RecipeWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        ingredients_data = serializer.validated_data.pop('ingredients')
        tags_data = serializer.validated_data.pop('tags')
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('pk'))
        # Проверка прав. Django получает объект get_object_or_404 раньше
        # чем срабатывает метод update, поэтому не
        # вызывается has_object_permission
        self.check_object_permissions(request, recipe)
        if 'image' not in request.data:
            serializer.validated_data['image'] = recipe.image
        for key, value in serializer.validated_data.items():
            setattr(recipe, key, value)
        recipe.save()
        IngredientRecipe.objects.filter(recipe=recipe).delete()
        for ingredient_data in ingredients_data:
            IngredientRecipe.objects.create(
                ingredient=ingredient_data['id'],
                recipe=recipe,
                amount=ingredient_data['amount']
            )
        recipe.tags.set(tags_data)
        serializer = RecipeReadSerializer(instance=recipe)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path=URL_DOWNLOAD_SHOPPING_CART
    )
    def download_shopping_cart(self, request):
        lines = []
        lines.append('Список покупок:')
        lines.append('')
        shopping_carts = request.user.shoppingcarts.all()
        recipes = Recipe.objects.filter(
            shoppingcarts__in=shopping_carts
        )
        ingredients = Ingredient.objects.filter(
            recipes__in=recipes
        ).distinct()
        for ingredient in ingredients:
            total_amount = IngredientRecipe.objects.filter(
                recipe__in=recipes,
                ingredient=ingredient
            ).aggregate(
                total_amount=Sum('amount')
            ).get('total_amount', 0)
            lines.append(f'{ingredient.name} - {total_amount}')

        content = '\n'.join(lines)
        response = HttpResponse(content, content_type="text/plain")
        response['Content-Disposition'] = (
            'attachment; filename=Shopping cart.txt'
        )
        return response


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = None
    filterset_class = IngredientSetFilter


class ShoppingCartFavoriteRecipeViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):

    """Базовый класс для Избранного и Списка покупок."""

    http_method_names = ('post', 'delete')
    pagination_class = None
    lookup_field = 'recipe_id'

    def get_recipe(self):
        return get_object_or_404(
            Recipe,
            pk=self.kwargs.get('recipe_id')
        )

    def create(self, request, *args, **kwargs):
        if not Recipe.objects.filter(
                pk=self.kwargs.get('recipe_id')
        ).exists():
            raise ValidationError('Рецепта не существует.')
        recipe = self.get_recipe()
        serializer = self.serializer_class(
            data={'user': request.user.pk, 'recipe': recipe.pk},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = self.read_serializer_class(
            instance=recipe
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_recipe()
        if not self.actions_model.objects.filter(
                user=request.user,
                recipe=recipe
        ).exists():
            raise ValidationError(self.del_error_messsage)
        self.perform_destroy(
            self.actions_model.objects.get(
                user=request.user,
                recipe=recipe
            )
        )
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class ShoppingCartViewSet(
    ShoppingCartFavoriteRecipeViewSet
):

    serializer_class = ShoppingCartWriteSerializer
    queryset = ShoppingCart.objects.all()

    del_error_messsage = 'Этого рецепта нет в списке покупок.'
    actions_model = ShoppingCart
    read_serializer_class = ShoppingCartReadSerializer


class FavoriteRecipeViewSet(
    ShoppingCartFavoriteRecipeViewSet
):

    serializer_class = FavoriteRecipeWriteSerializer
    queryset = Favorite.objects.all()

    del_error_messsage = 'Этого рецепта нет в избранном.'
    actions_model = Favorite
    read_serializer_class = FavoriteRecipeReadSerializer


class SubscribeViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = SubscribeWriteSerializer
    queryset = Subscription.objects.all()
    permission_classes = (IsAuthenticated,)
    http_method_names = ('post', 'delete')
    pagination_class = None
    lookup_field = 'user_id'

    def get_author(self):
        return get_object_or_404(
            User,
            pk=self.kwargs.get('user_id')
        )

    def create(self, request, *args, **kwargs):
        author = self.get_author()
        serializer = SubscribeWriteSerializer(
            data={
                'subscriber': request.user.pk,
                'author': author.pk
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = SubscribeReadSerializer(
            instance=author,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        author = self.get_author()
        if not Subscription.objects.filter(
                subscriber=request.user,
                author=author
        ).exists():
            raise ValidationError('Подписки не существует.')
        self.perform_destroy(
            Subscription.objects.get(
                subscriber=request.user,
                author=author
            )
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsListViewSet(generics.ListAPIView):
    serializer_class = SubscribeReadSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('get',)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        """
        Возвращает queryset пользователей, на которых подписан
        текущий пользователь.
        """
        subscribed_to_users = User.objects.filter(
            subscription_as_author=self.request.user
        )
        return subscribed_to_users
