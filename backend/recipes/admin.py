from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from .models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                     Subscription, Tag, User)

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
        'display_role',
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
        'role',
        'is_superuser',
        'is_staff',
        'is_active',
        'date_joined',
    )

    def display_role(self, user):
        return user.role

    display_role.short_description = 'Роль'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
        'slug',
    )


class IngredientInline(admin.TabularInline):
    model = Ingredient.recipes.through
    extra = 0


class TagInline(admin.TabularInline):
    model = Tag.recipes.through
    extra = 0


class RecipeAdminForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if not self.data.get('ingredientsrecipes-0-ingredient'):
            raise forms.ValidationError('Поле ингредиента не может быть пустым.')
        if not self.data.get('ingredientsrecipes-0-amount'):
            raise forms.ValidationError('Поле колличества ингредиента не может быть пустым.')
        if not self.data.get('tagrecipe_set-0-tag'):
            raise forms.ValidationError('Поле тэга не может быть пустым.')
        return cleaned_data


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    form = RecipeAdminForm
    inlines = [
        IngredientInline,
        TagInline,
    ]
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

    @admin.display(description='Добавлено в избранное, раз')
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
