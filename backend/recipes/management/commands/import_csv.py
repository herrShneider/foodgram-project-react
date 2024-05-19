import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag

csv_files = {
    'ingredients.csv': Ingredient,
    'tags.csv': Tag,
}


class Command(BaseCommand):

    def handle(self, *args, **options):
        """Функция валидации полей и импорта."""
        for csv_file_name, model in csv_files.items():
            try:
                with open(
                        f'data_for_test/{csv_file_name}',
                        'r',
                        encoding='utf-8'
                ) as csvfile:
                    rows = list(csv.DictReader(csvfile))
            except FileNotFoundError:
                self.stdout.write(
                    self.style.ERROR(
                        f'Файл {csv_file_name} не найден.'
                    )
                )
                continue
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Ошибка при чтении файла {csv_file_name}: {e}'
                    )
                )
                continue
            for row in rows:
                try:
                    item, created = model.objects.get_or_create(**row)
                    item.full_clean()
                    item.save()
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Запись для модели {model.__name__} '
                                f'добавлена: {row}'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Запись для модели {model.__name__} '
                                f'уже существует: {row}'
                            )
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'Ошибка при создании объекта '
                            f'{model.__name__}: {e}'
                        )
                    )
                    continue
