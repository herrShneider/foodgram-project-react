from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, Recipe, ShoppingCart, Subscription,
                     Tag, User)

admin.site.unregister(Group)

admin.site.empty_value_display = 'Не задано'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'id',
        'username',
        'first_name',
        'last_name',
        'recipes_count',
        'subscribers_count',
    )
    list_filter = (
        'email',
        'username',
    )
    fields = (
        'email',
        'username',
        'first_name',
        'last_name',
    )

    @admin.display(description='Кол-во рецептов')
    def recipes_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Кол-во подписчиков')
    def subscribers_count(self, obj):
        return obj.subscription_as_author.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
        'slug',
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    list_filter = (
        'name',
    )


class IngredientInline(admin.TabularInline):
    model = Ingredient.recipes.through
    extra = 0
    min_num = 1


class RecipeAdminForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeAdminForm
    inlines = (
        IngredientInline,
    )
    list_display = (
        'author',
        'name',
        'show_image',
        'text',
        'cooking_time',
        'favorites_count',
        'ingredients_list',
        'tags_list',
    )
    list_filter = (
        'author',
        'name',
        'tags',
    )
    fields = (
        'author',
        'name',
        'image',
        'text',
        'cooking_time',
        'tags',
    )

    @admin.display(description='Картинка')
    def show_image(self, obj):
        return mark_safe(
            f'<img src={obj.image.url} width="80" height="60">'
        )

    @admin.display(description='В избранном, раз')
    def favorites_count(self, obj):
        return obj.favorites.count()

    @admin.display(description='Ингредиенты')
    def ingredients_list(self, obj):
        return list(item.name for item in obj.ingredients.all())

    @admin.display(description='Тэги')
    def tags_list(self, obj):
        return list(item.name for item in obj.tags.all())


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'subscriber',
        'author',
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )


@admin.register(Favorite)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )
