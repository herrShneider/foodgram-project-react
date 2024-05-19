from django.db.models import BooleanField, Count, Exists, OuterRef, Sum, Value
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views as djoser_views
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientSetFilter, RecipeSetFilter
from api.permissions import IsAuthorOrReadCreate
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeReadSerializer, RecipeWriteSerializer,
                             ShoppingCartSerializer, SubscribeReadSerializer,
                             SubscribeWriteSerializer, TagSerializer)
from config import HTTP_METHODS, URL_DOWNLOAD_SHOPPING_CART
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Subscription, Tag, User)


class FoodgramUserViewSet(djoser_views.UserViewSet):

    queryset = User.objects.all().annotate(recipes_count=Count('recipes'))
    http_method_names = ('get', 'post', 'delete')
    filter_backends = (DjangoFilterBackend,)

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions'
    )
    def get_subscriptions(self, request):
        authors = User.objects.filter(
            subscription_as_author__subscriber=request.user
        ).annotate(recipes_count=Count('recipes'))
        page = self.paginate_queryset(authors)
        serializer = SubscribeReadSerializer(
            page,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe'
    )
    def to_subscribe(self, request, id=None):
        data = {'subscriber': request.user.id, 'author': id}
        serializer = SubscribeWriteSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @to_subscribe.mapping.delete
    def to_unsubscribe(self, request, id=None):
        if Subscription.objects.filter(
                subscriber=request.user,
                author=id
        ).exists():
            Subscription.objects.get(
                subscriber=request.user,
                author=id
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


def is_exists(model, user):
    if user.is_authenticated:
        return Exists(model.objects.filter(user=user, recipe=OuterRef('pk')))
    return Value(False, output_field=BooleanField())


class RecipeViewSet(viewsets.ModelViewSet):

    http_method_names = HTTP_METHODS
    permission_classes = (IsAuthorOrReadCreate,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeSetFilter

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def get_queryset(self):
        user = self.request.user
        return (Recipe.objects
                .select_related('author')
                .prefetch_related('tags', 'ingredients')
                .annotate(is_favorited=is_exists(Favorite, user))
                .annotate(is_in_shopping_cart=is_exists(ShoppingCart, user)))

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
        ingredients = (IngredientRecipe.objects
                       .filter(recipe__shoppingcarts__user=request.user)
                       .values('ingredient__name',
                               'ingredient__measurement_unit')
                       .annotate(total_amount=Sum('amount'))
                       .order_by('ingredient__name'))
        for item in ingredients:
            lines.append(f'{item["ingredient__name"]} - {item["total_amount"]}'
                         f'{item["ingredient__measurement_unit"]}')
        content = '\n'.join(lines)
        response = HttpResponse(content, content_type="text/plain")
        response['Content-Disposition'] = (
            'attachment; filename=Shopping cart.txt'
        )
        return response

    @staticmethod
    def write_down_the_recipe(serializer_class, request, pk):
        data = {'user': request.user.id, 'recipe': pk}
        serializer = serializer_class(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='favorite'
    )
    def add_to_favorite(self, request, pk=None):
        return self.write_down_the_recipe(FavoriteSerializer, request, pk)

    @add_to_favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        if Favorite.objects.filter(user=request.user, recipe=pk).exists():
            Favorite.objects.get(user=request.user, recipe=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart'
    )
    def add_to_shopping_cart(self, request, pk=None):
        return self.write_down_the_recipe(ShoppingCartSerializer, request, pk)

    @add_to_shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        if ShoppingCart.objects.filter(user=request.user, recipe=pk).exists():
            ShoppingCart.objects.get(user=request.user, recipe=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


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
