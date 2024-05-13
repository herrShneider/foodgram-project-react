from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from config import (DESCRIPTION_MAX_LENGTH, EMAIL_FIELD_LENGTH,
                    FIRST_NAME_LENGTH, LAST_NAME_LENGTH, NAME_MAX_LENGTH,
                    PASSWORD_LENGTH, SLUG_MAX_LENGTH, TAG_COLOR_MAX_LENGTH,
                    TEXT_LIMIT, USERNAME_LENGTH)
from recipes.validators import (validate_amount, validate_cooking_time,
                                validate_hex_color, validate_image,
                                validate_not_me, validate_username_via_regex)


class User(AbstractUser):

    ADMIN = 'admin'
    USER = 'user'
    CHOICES = [
        (ADMIN, 'Администратор'),
        (USER, 'Пользователь'),
    ]

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
    password = models.CharField(
        max_length=PASSWORD_LENGTH,
        verbose_name='Пароль',
    )
    role = models.CharField(
        max_length=max(len(role) for role, _ in CHOICES),
        choices=CHOICES,
        default=USER,
        blank=True,
        verbose_name='Пользовательская роль',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', ]

    class Meta:

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_staff


class Subscription(models.Model):

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription_as_subscriber',
        verbose_name='Подписчик',
    )
    subscription = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription_subscribed_to',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('subscriber', 'subscription'),
                name='Ограничение повторной подписки',
            ),
        )

    def __str__(self):
        return f'{self.subscriber} подписан на {self.subscription}'

    def clean(self):
        if self.subscriber == self.subscription:
            raise ValidationError('Нельзя подписаться на самого себя.')


class Tag(models.Model):

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
        verbose_name='Слаг',
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
        return f'{self.name} {self.measurement_unit}'[:TEXT_LIMIT]


class Recipe(models.Model):

    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
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
        validators=(validate_image,)
    )
    text = models.TextField(
        verbose_name='Описание',
        max_length=DESCRIPTION_MAX_LENGTH,
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=(validate_cooking_time,),
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
        validators=(validate_amount,)
    )

    class Meta:
        verbose_name = 'ИнгредиентРецепт'
        verbose_name_plural = 'ИнгредиентыРецепты'
        default_related_name = 'ingredientsrecipes'
        constraints = (
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='Ограничение повторного добавления ингредиента к рецепту',
            ),
        )

    def __str__(self):
        return f'{self.recipe} {self.ingredient} {self.amount}'[:TEXT_LIMIT]


class TagRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тэг',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('tag', 'recipe'),
                name='Ограничение повторного добавления тэга к рецепту',
            ),
        )

    def __str__(self):
        return f'{self.tag} {self.recipe}'


class ShoppingCart(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Юзер',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_carts'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='Ограничение повторного добавления в список покупок',
            ),
        )


class FavoriteRecipe(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Юзер',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'favorite_recipes'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='Ограничение повторного добавления рецепта в избранное',
            ),
        )
