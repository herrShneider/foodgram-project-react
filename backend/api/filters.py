from django_filters import ModelMultipleChoiceFilter
from django_filters.rest_framework import BooleanFilter, CharFilter, FilterSet

from recipes.models import Ingredient, Recipe, Tag


class IngredientSetFilter(FilterSet):

    name = CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeSetFilter(FilterSet):

    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
        label='tags',
    )
    is_in_shopping_cart = BooleanFilter(
        method='filter_by_is_in_shopping_cart'
    )
    is_favorited = BooleanFilter(
        method='filter_by_is_favorited'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_in_shopping_cart', 'is_favorited')

    def filter_by_is_in_shopping_cart(self, queryset, name, value):
        print('queryset', queryset)
        if self.request.user.is_authenticated and value:
            return queryset.filter(shoppingcarts__user=self.request.user)
        return queryset

    def filter_by_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset
