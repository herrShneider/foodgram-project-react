from django.db.models import Subquery, OuterRef
from django_filters.rest_framework import BooleanFilter, CharFilter, FilterSet, NumberFilter

from recipes.models import FavoriteRecipe, Ingredient, Recipe, ShoppingCart, User


class IngredientSetFilter(FilterSet):

    name = CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeSetFilter(FilterSet):

    author__id = NumberFilter(
        field_name='author',
        lookup_expr='exact'
    )
    tags = CharFilter(
        method='filter_by_tags'
    )
    is_in_shopping_cart = BooleanFilter(
        method='filter_by_is_in_shopping_cart'
    )
    is_favorited = BooleanFilter(
        method='filter_by_is_favorited'
    )

    class Meta:
        model = Recipe
        # fields = ('author', 'tags', 'is_in_shopping_cart', 'is_favorited')
        fields = ('author', 'tags', 'is_in_shopping_cart', 'is_favorited')

    def filter_by_tags(self, queryset, name, value):
        # Получаем значения tags из URL и подставляем в фильтр
        return queryset.filter(tags__slug__in=self.request.query_params.getlist('tags'))

    def filter_by_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            shoppingcart_recipes = ShoppingCart.objects.filter(user=self.request.user)
            return queryset.filter(shopping_carts__in=shoppingcart_recipes)
        return queryset

    def filter_by_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            favorited_recipes = FavoriteRecipe.objects.filter(user=self.request.user)
            return queryset.filter(favorite_recipes__in=favorited_recipes)
        return queryset
