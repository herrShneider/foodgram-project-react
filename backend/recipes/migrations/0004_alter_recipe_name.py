# Generated by Django 3.2.16 on 2024-05-12 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20240512_1343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='name',
            field=models.CharField(max_length=60, unique=True, verbose_name='Название'),
        ),
    ]