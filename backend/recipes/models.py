from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.core.validators import MaxValueValidator
from django.db import models

from config import (COOKING_TIME_MAX_VALUE, DESCRIPTION_MAX_LENGTH, EMAIL_FIELD_LENGTH, FIRST_NAME_LENGTH,
                    LAST_NAME_LENGTH, NAME_MAX_LENGTH,
                    PASSWORD_LENGTH, SLUG_MAX_LENGTH,
                    TAG_COLOR_MAX_LENGTH, TEXT_LIMIT, USERNAME_LENGTH)

from recipes.validators import validate_hex_color, validate_not_me, validate_username_via_regex


class User(AbstractUser):
    """Модель кастомного юзера."""

    ADMIN = 'admin'
    USER = 'user'
    CHOICES = [
        (ADMIN, 'Администратор'),
        (USER, 'Пользователь'),
    ]

    email = models.EmailField(
        max_length=EMAIL_FIELD_LENGTH,
        unique=True
    )
    username = models.CharField(
        max_length=USERNAME_LENGTH,
        unique=True,
        validators=(validate_not_me, validate_username_via_regex),
    )
    first_name = models.CharField(
        max_length=FIRST_NAME_LENGTH,
    )
    last_name = models.CharField(
        max_length=LAST_NAME_LENGTH,
    )
    password = models.CharField(
        max_length=PASSWORD_LENGTH,
    )
    role = models.CharField(
        'Пользовательская роль',
        max_length=max(len(role) for role, _ in CHOICES),
        choices=CHOICES,
        default=USER,
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', ]

    class Meta:

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        """Возвращает 'Имя Фамилия' при попытке распечатать ."""
        return f'{self.first_name} {self.last_name}'

    @property
    def is_admin(self):
        """Клиент администратор."""
        return self.role == self.ADMIN or self.is_staff

    def save(self, *args, **kwargs):
        if self.password:
            # validate_password(self.password, user=self)  # проходит 500 ошибка а не 400
            self.set_password(self.password)
        super().save(*args, **kwargs)


class Subscription(models.Model):
    """Класс подписок."""

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_as_subscriber'
    )
    subscription = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_subscribed_to'
    )


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        verbose_name='Название',
        max_length=NAME_MAX_LENGTH,
        unique=True,
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=TAG_COLOR_MAX_LENGTH,
        help_text='Шестнадцатеричный код цвета, например, #49B64E.',
        unique=True,
        validators=(validate_hex_color,),
    )
    slug = models.SlugField(
        verbose_name='slug',
        max_length=SLUG_MAX_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ('name',)

    def __str__(self):
        return self.name[:TEXT_LIMIT]


class Ingredient(models.Model):
    """Модель ингридиентов."""

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

    def __str__(self):
        return self.name[:TEXT_LIMIT]


class Recipe(models.Model):
    """Класс рецептов."""

    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
        verbose_name='Теги',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
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

    text = models.TextField(
        verbose_name='Описание',
        max_length=DESCRIPTION_MAX_LENGTH,
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MaxValueValidator(
                COOKING_TIME_MAX_VALUE,
                f'Время приготовления не может быть больше {COOKING_TIME_MAX_VALUE} минут.'
            )
        ],
        verbose_name='Время приготовления',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        default_related_name = 'recipes'

    def __str__(self):
        return self.name[:TEXT_LIMIT]


class IngredientRecipe(models.Model):
    """Промежуточная таблица для добавления колличества."""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
    )

    class Meta:
        verbose_name = 'ИнгредиентРецепт'
        verbose_name_plural = 'ИнгредиентыРецепты'
        default_related_name = 'ingredientsrecipes'

    def __str__(self):
        return f'{self.recipe} {self.ingredient} {self.amount}'[:TEXT_LIMIT]


class TagRecipe(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.tag} {self.recipe}'

# class Recipe(models.Model):
#     """Класс рецептов."""
#
#     tags = models.ManyToManyField(
#         Tag,
#         related_name='recipes'
#     )
#     author = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#     )
#     ingredients = models.ManyToManyField(
#         Ingredient,
#         through='IngredientRecipe',
#         related_name='recipes',
#     )
#     name = models.CharField(
#         verbose_name='Название',
#         max_length=NAME_MAX_LENGTH,
#     )
#     image = models.ImageField(
#         upload_to='recipes/images/',
#         default=None,
#     )
#     text = models.TextField(
#         verbose_name='Описание',
#         max_length=DESCRIPTION_MAX_LENGTH,
#     )
#     cooking_time = models.PositiveSmallIntegerField(
#         validators=[
#             MaxValueValidator(
#                 COOKING_TIME_MAX_VALUE,
#                 f'Время приготовления не может быть больше {COOKING_TIME_MAX_VALUE} минут.'
#             )
#         ],
#         verbose_name='Время приготовления',
#     )
#     pub_date = models.DateTimeField(
#         auto_now_add=True,
#         verbose_name='Дата публикации',
#     )
#
#     class Meta:
#         verbose_name = 'Рецепт'
#         verbose_name_plural = 'Рецепты'
#         ordering = ('-pub_date',)
#         default_related_name = 'recipes'
#
#     def __str__(self):
#         return self.name[:TEXT_LIMIT]


class FavoriteRecipe(models.Model):
    """Класс Избранных рецептов."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    favorite_recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipes'
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(models.Model):
    """Класс Списка покупок."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    shopping_cart = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_carts'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

