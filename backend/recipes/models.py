from colorfield.fields import ColorField
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from config import (AMOUNT_MAX_VALUE, AMOUNT_MIN_VALUE, COOK_TIME_MAX_VALUE,
                    COOK_TIME_MIN_VALUE, EMAIL_FIELD_LENGTH, FIRST_NAME_LENGTH,
                    LAST_NAME_LENGTH, NAME_MAX_LENGTH, SLICE_STR_METHOD_LIMIT,
                    SLUG_MAX_LENGTH, TAG_COLOR_MAX_LENGTH, USERNAME_LENGTH)
from recipes.validators import validate_not_me, validate_username_via_regex


class User(AbstractUser):

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name', )

    email = models.EmailField(
        max_length=EMAIL_FIELD_LENGTH,
        unique=True,
        verbose_name='Электронная почта',
    )
    username = models.CharField(
        max_length=USERNAME_LENGTH,
        unique=True,
        validators=(validate_not_me, validate_username_via_regex),
        verbose_name='Никнэйм',
    )
    first_name = models.CharField(
        max_length=FIRST_NAME_LENGTH,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=LAST_NAME_LENGTH,
        verbose_name='Фамилия',
    )

    class Meta:

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.get_full_name()


class Subscription(models.Model):

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription_as_subscriber',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription_as_author',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'

    def clean(self):
        if self.subscriber == self.author:
            raise ValidationError('Нельзя подписаться на самого себя.')
        if Subscription.objects.filter(
                subscriber=self.subscriber,
                author=self.author
        ).exists():
            raise ValidationError('Эта подписка уже существует.')
        return super().save(self)


class Tag(models.Model):

    name = models.CharField(
        verbose_name='Название',
        max_length=NAME_MAX_LENGTH,
        unique=True,
    )
    color = ColorField(
        verbose_name='Цвет',
        max_length=TAG_COLOR_MAX_LENGTH,
        help_text='Шестнадцатеричный код цвета, например, #49B64E.',
        unique=True,
    )
    slug = models.SlugField(
        verbose_name='Слаг',
        unique=True,
        max_length=SLUG_MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self):
        return self.name[:SLICE_STR_METHOD_LIMIT]


class Ingredient(models.Model):

    name = models.CharField(
        verbose_name='Название',
        max_length=NAME_MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=NAME_MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='Unique_name_measurement_unit',
            ),
        )

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'[:SLICE_STR_METHOD_LIMIT]


class Recipe(models.Model):

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиенты',
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=NAME_MAX_LENGTH,
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/images/',
        default=None,
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(
            MinValueValidator(
                COOK_TIME_MIN_VALUE,
                message=f'Значение должно быть больше {COOK_TIME_MIN_VALUE}'
            ),
            MaxValueValidator(
                COOK_TIME_MAX_VALUE,
                message=f'Значение должно быть меньше {COOK_TIME_MAX_VALUE}'
            ),
        )
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        default_related_name = 'recipes'

    def __str__(self):
        return f'{self.name} {self.author}'


class IngredientRecipe(models.Model):

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=(
            MinValueValidator(
                AMOUNT_MIN_VALUE,
                message=f'Значение должно быть больше {AMOUNT_MIN_VALUE}'
            ),
            MaxValueValidator(
                AMOUNT_MAX_VALUE,
                message=f'Значение должно быть меньше {AMOUNT_MAX_VALUE}'
            ),
        )
    )

    class Meta:
        verbose_name = 'ИнгредиентРецепт'
        verbose_name_plural = 'ИнгредиентыРецепты'
        default_related_name = 'ingredientsrecipes'
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='Unique_ingredient_recipe',
            ),
        )

    def __str__(self):
        return (f'{self.recipe} {self.ingredient} '
                f'{self.amount}')[:SLICE_STR_METHOD_LIMIT]


class UserRecipeModel(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        default_related_name = '%(class)ss'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(app_label)s_%(class)s_unique_constraint',
            ),
        )

    def __str__(self):
        return f'{self._meta.verbose_name} {self.user} {self.recipe}'


class ShoppingCart(UserRecipeModel):

    class Meta(UserRecipeModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'


class Favorite(UserRecipeModel):

    class Meta(UserRecipeModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
