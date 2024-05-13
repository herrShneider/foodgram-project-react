import csv

from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Tag

csv_files = [
    'ingredients.csv',
    'tags.csv',
]

csv_fields = {
    'ingredients.csv': ['name', 'measurement_unit'],
    'tags.csv': ['name', 'color', 'slug'],
}

models = {
    'ingredients': Ingredient,
    'tags': Tag,
}


def csv_reader_file(csv_file_name):
    """Функция чтения из файла."""
    with open(
        'data_for_test/' + csv_file_name,
        'r',
        encoding='utf-8'
    )as csvfile:
        csvreader = csv.DictReader(csvfile)
        return list(csvreader)


class Command(BaseCommand):

    def handle(self, *args, **options):
        """Функция валидации полей и импорта."""
        for csv_file_name in csv_files:
            model = csv_file_name.split('.')[0]
            model_class = models.get(model)
            for row in csv_reader_file(csv_file_name):
                if model_class in (Ingredient, Tag):
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
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Не удалось создать запись {model}'
                            )
                        )
                        continue
                    item.full_clean()
                    item.save()
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Не удалось создать запись {model}'
                        )
                    )
                    continue
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Запись для модели {model} добавлена: {row}'
                    )
                )
