"""Manage - команда для импорта csv-файлов."""

import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag, Recipe

csv_files = [
    'ingredients.csv',
    'tags.csv',
    # 'recipes.csv',
]

csv_fields = {
    'ingredients.csv': ['name', 'measurement_unit'],
    'tags.csv': ['name', 'color', 'slug'],
    'recipes.csv': ['name', 'text', 'cooking_time'],
}

models = {
    'ingredients': Ingredient,
    'tags': Tag,
    'recipes': Recipe,
}


def csv_reader_file(csv_file_name):
    """Функция чтения из файла."""
    with open(
        '../data/' + csv_file_name,
        'r',
        encoding='utf-8'
    )as csvfile:
        csvreader = csv.DictReader(csvfile)
        return list(csvreader)


class Command(BaseCommand):
    """Класс команды."""

    def handle(self, *args, **options):
        """Функция валидации полей и импорта."""
        for csv_file_name in csv_files:
            model = csv_file_name.split('.')[0]
            model_class = models.get(model)
            for row in csv_reader_file(csv_file_name):
                item = None
                if model_class == Ingredient:
                    item = Ingredient(
                        name=row['name'],
                        measurement_unit=row['measurement_unit'],
                    )
                elif model_class == Tag:
                    item = Tag(
                        name=row['name'],
                        color=row['color'],
                        slug=row['slug'],
                    )
                elif model_class == Recipe:
                    item = Recipe(
                        name=row['name'],
                        text=row['text'],
                        cooking_time=row['cooking_time'],
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Не удалось создать запись {model}'
                        )
                    )
                    continue
                item.full_clean()
                item.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Запись для модели {model} добавлена: {row}'
                    )
                )
