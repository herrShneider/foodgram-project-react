from django.contrib.auth import authenticate
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
# from django.shortcuts import get_object_or_404
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
# from djoser.views import UserViewSet

from .serializers import IngredientSerializer, RecipeCreateUpdateSerializer, RecipeListRetrieveAuthSerializer, RecipeListRetrieveSerializer, TagSerializer, UserSerializer, UserProfileSerializer
from config import URL_PROFILE_PREF, URL_SET_PASSWORD
from recipes.models import FavoriteRecipe, Ingredient, Recipe, ShoppingCart, Subscription, Tag, TagRecipe, User

HTTP_METHODS = ('get', 'post', 'patch', 'delete')


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы администратора с users."""

    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    # lookup_field = 'username'
    # filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    http_method_names = ('get', 'post',)
    # search_fields = ('username',)

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

    def get_queryset(self):
        queryset = User.objects.all().annotate(
            is_subscribed=Exists(Subscription.objects.filter(
                subscriber=self.request.user,
                subscription=OuterRef('pk'),
            )),
        )
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    http_method_names = HTTP_METHODS
    # serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def get_serializer_class(self):
        # if self.action == 'list' or self.action == 'retrieve':
        if self.request.method == 'GET':
            if self.request.user.is_authenticated:
                return RecipeListRetrieveAuthSerializer
            return RecipeListRetrieveSerializer
        return RecipeCreateUpdateSerializer

    # def get_recipe(self):
    #     """Возвращает объект рецепта."""
    #     return get_object_or_404(
    #         Recipe,
    #         pk=self.kwargs.get('recipe_id'),
    #     )

    def get_queryset(self):
        recipe_queryset = Recipe.objects.prefetch_related('tags')

        if self.request.user.is_authenticated:
            return recipe_queryset.annotate(
                is_favorited=Exists(FavoriteRecipe.objects.filter(
                    user=self.request.user,
                    favorite_recipe=OuterRef('pk'),
                )),
                is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                    user=self.request.user,
                    shopping_cart=OuterRef('pk'),
                )),
            )
        return recipe_queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
