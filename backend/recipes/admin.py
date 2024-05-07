from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import FavoriteRecipe, Ingredient, Recipe, ShoppingCart, Subscription, Tag, User

admin.site.unregister(Group)

admin.site.empty_value_display = 'Не задано'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email',
        'id',
        'username',
        'first_name',
        'last_name',
        'role',
    )
    list_filter = (
        'email',
        'username',
    )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'name',
        'image',
        'text',
        'cooking_time',
        'favorites_count',
    )
    list_filter = (
        'author',
        'name',
        'tags',
    )

    @admin.display(description='Общее число добавлений в избранное')
    def favorites_count(self, obj):
        return obj.favorite_recipes.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit',
    )
    list_filter = (
        'name',
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
        'slug',
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'subscriber',
        'subscription',
    )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
    )