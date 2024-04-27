"""Manage - команда для импорта json-файлов."""

import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient

json_files = [
    'ingredients.json',
]

models = {
    'ingredients': Ingredient,
}


def json_reader_file(json_file_name):
    """Функция чтения из json-файла и перевода в python-объект."""
    with open(
        '../data/' + json_file_name,
        'r',
        encoding='utf-8'
    )as jsonfile:
        data = json.load(jsonfile)
        print(data)
        return data


class Command(BaseCommand):
    """Класс команды."""

    def handle(self, *args, **options):
        """Функция валидации полей и импорта."""
        for json_file_name in json_files:
            model = json_file_name.split('.')[0]
            model_class = models.get(model)
            for row in json_reader_file(json_file_name):
                item = None
                if model_class == Ingredient:
                    item = Ingredient(
                        name=row['name'],
                        measurement_unit=row['measurement_unit'],
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
