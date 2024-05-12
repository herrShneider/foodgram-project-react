# Generated by Django 3.2.16 on 2024-05-12 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_auto_20240508_0043'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='favoriterecipe',
            constraint=models.UniqueConstraint(fields=('user', 'recipe'), name='Ограничение повторного добавления рецепта в избранное'),
        ),
        migrations.AddConstraint(
            model_name='ingredientrecipe',
            constraint=models.UniqueConstraint(fields=('ingredient', 'recipe'), name='Ограничение повторного добавления ингредиента к рецепту'),
        ),
        migrations.AddConstraint(
            model_name='shoppingcart',
            constraint=models.UniqueConstraint(fields=('user', 'recipe'), name='Ограничение повторного добавления рецепта в список покупок'),
        ),
        migrations.AddConstraint(
            model_name='subscription',
            constraint=models.UniqueConstraint(fields=('subscriber', 'subscription'), name='Ограничение повторной подписки'),
        ),
        migrations.AddConstraint(
            model_name='tagrecipe',
            constraint=models.UniqueConstraint(fields=('tag', 'recipe'), name='Ограничение повторного добавления тэга к рецепту'),
        ),
    ]
