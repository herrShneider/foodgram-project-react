import io

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from django.contrib.auth import authenticate
from django.http import FileResponse
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from . import permissions
from .filters import IngredientSetFilter, RecipeSetFilter
from .permissions import IsAuthorAdminOrReadOnly, IsAuthorOrIsAdmin
from .serializers import (FavoriteRecipeReadSerializer, FavoriteRecipeWriteSerializer,
                          IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, ShoppingCartReadSerializer,
                          ShoppingCartWriteSerializer, SubscribeReadSerializer,
                          SubscribeWriteSerializer, TagSerializer,
                          UserCreateSerializer, UserSerializer, )
from config import URL_PROFILE_PREF, URL_SET_PASSWORD
from recipes.models import FavoriteRecipe, Ingredient, IngredientRecipe, Recipe, ShoppingCart, Subscription, Tag, User

HTTP_METHODS = ('get', 'post', 'patch', 'delete')
URL_SHOPPING_CART = 'shopping_cart'
URL_DOWNLOAD_SHOPPING_CART = 'download_shopping_cart'


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы администратора с users."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ('get', 'post',)
    permission_classes = (AllowAny,)
    # lookup_field = 'username'
    # filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    filter_backends = (DjangoFilterBackend,)
    # filterset_fields = ('tags',)
    # search_fields = ('username',)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

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
        return Response(UserSerializer(request.user).data)

    @action(
        detail=False,
        methods=('post',),
        permission_classes=(permissions.IsAuthorOrIsAdmin,),
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
            serializer = UserSerializer(
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
            return Response({'error': 'Неверный текущий пароль'}, status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ModelViewSet):

    http_method_names = HTTP_METHODS
    serializer_class = RecipeReadSerializer
    permission_classes = (IsAuthorAdminOrReadOnly, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeSetFilter

    def get_serializer_context(self):
        """Передаёт объекта запроса в контекст сериализатора."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        return Recipe.objects.prefetch_related('tags')

    # def list(self, request, *args, **kwargs):
    #     queryset = self.get_queryset()
    #     serializer = self.get_serializer(queryset, many=True)
    #     print(serializer.data)
    #     print(len(serializer.data))
    #     print(type(serializer.data))
    #     for item in serializer.data:
    #         print(item)
    #         print(type(item))
    #     return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        print('def create')
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
        serializer = RecipeReadSerializer(instance=recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        print('def update')
        serializer = RecipeWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ingredients_data = serializer.validated_data.pop('ingredients')
        tags_data = serializer.validated_data.pop('tags')
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('pk'))
        # Проверка прав. Django получает объект get_object_or_404 раньше
        # чем срабатывает метод update, поэтому не вызывается has_object_permission
        self.check_object_permissions(request, recipe)
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
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path=URL_DOWNLOAD_SHOPPING_CART
    )
    def download_shopping_cart(self, request):
        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        buf = io.BytesIO()
        canvas_for_pdf = Canvas(buf)
        canvas_for_pdf.setFont('Arial', 12)
        textob = canvas_for_pdf.beginText(40, 780)
        lines = []
        lines.append('Shopping cart:')
        lines.append('')
        shopping_carts = request.user.shopping_carts.all()
        # __in: это оператор фильтрации, который позволяет указать список
        recipes = Recipe.objects.filter(
            shopping_carts__in=shopping_carts
        )
        #  Создаем queryset ингредиентов, из которых состоят рецепты.
        #  Используем distinct(), чтобы убедиться, что каждый ингредиент
        #  возвращается только один раз.
        ingredients = Ingredient.objects.filter(
            recipes__in=recipes
        ).distinct()
        for ingredient in ingredients:
            total_amount = IngredientRecipe.objects.filter(
                recipe__in=recipes,
                ingredient=ingredient
            ).aggregate(total_amount=Sum('amount'))['total_amount']
            lines.append(f'{ingredient.name} - {total_amount}')

        for line in lines:
            textob.textLines(line)

        canvas_for_pdf.drawText(textob)
        canvas_for_pdf.showPage()
        canvas_for_pdf.save()
        buf.seek(0)
        pdf_file = buf
        return FileResponse(
            pdf_file,
            as_attachment=True,
            filename='shopping_cart.pdf'
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    # filter_backends = (DjangoFilterBackend,)
    pagination_class = None
    # filterset_class = IngredientSetFilter


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    pagination_class = None
    filterset_class = IngredientSetFilter


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

    # def get_recipe(self):
    #     return get_object_or_404(Recipe, pk=self.kwargs.get('recipe_id'))

    def create(self, request, *args, **kwargs):
        try:
            recipe = Recipe.objects.get(pk=self.kwargs.get('recipe_id'))
        except Recipe.DoesNotExist:
            raise ValidationError('Рецепта не существует.')
        # recipe = self.get_recipe()
        serializer = ShoppingCartWriteSerializer(
            data={'user': request.user.pk, 'recipe': recipe.pk},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = ShoppingCartReadSerializer(instance=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('recipe_id'))
        try:
            instance = ShoppingCart.objects.get(user=request.user, recipe=recipe.pk)
        except ShoppingCart.DoesNotExist:
            raise ValidationError('Этого рецепта нет в списке покупок.')
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
        # return super().destroy(request, *args, **kwargs)


class FavoriteRecipeViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):

    serializer_class = FavoriteRecipeWriteSerializer
    queryset = ShoppingCart.objects.all()
    http_method_names = ('post', 'delete')
    pagination_class = None
    lookup_field = 'recipe_id'

    # def get_recipe(self):
    #     return get_object_or_404(Recipe, pk=self.kwargs.get('recipe_id'))

    def create(self, request, *args, **kwargs):
        try:
            recipe = Recipe.objects.get(pk=self.kwargs.get('recipe_id'))
        except Recipe.DoesNotExist:
            raise ValidationError('Рецепта не существует.')
        # recipe = self.get_recipe()
        serializer = FavoriteRecipeWriteSerializer(
            data={'user': request.user.pk, 'recipe': recipe.pk},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = FavoriteRecipeReadSerializer(instance=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=self.kwargs.get('recipe_id'))
        try:
            instance = FavoriteRecipe.objects.get(user=request.user, recipe=recipe.pk)
        except FavoriteRecipe.DoesNotExist:
            raise ValidationError('Этого рецепта не в избранном.')
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    def get_user_subscribed_to(self):
        return get_object_or_404(User, pk=self.kwargs.get('user_id'))

    def create(self, request, *args, **kwargs):
        user_subscribed_to = self.get_user_subscribed_to()
        serializer = SubscribeWriteSerializer(
            data={'subscriber': request.user.pk, 'subscription': self.kwargs.get('user_id')},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = SubscribeReadSerializer(instance=user_subscribed_to, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = Subscription.objects.get(subscriber=request.user, subscription=self.get_user_subscribed_to().pk)
        except Subscription.DoesNotExist:
            raise ValidationError('Подписки не существует.')
        # instance = get_object_or_404(Subscription, subscriber=request.user, subscription=self.kwargs.get('user_id'))
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsListViewSet(generics.ListAPIView):
    serializer_class = SubscribeReadSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('get',)
    pagination_class = LimitOffsetPagination
    # filter_backends = (DjangoFilterBackend,)
    # filterset_class = SubscriptionsSetFilter

    def get_serializer_context(self):
        """Передаёт объекта запроса в контекст сериализатора."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        """Возвращает queryset пользователей, на которых подписан текущий пользователь."""
        subscribed_to_users = User.objects.filter(subscription_subscribed_to__subscriber=self.request.user)
        return subscribed_to_users
