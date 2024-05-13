import base64
import csv

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.timezone import now

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag, User

csv_files = [
    'users.csv',
    'recipes.csv',
]

csv_fields = {
    'users.csv': ['email', 'username', 'first_name',
                  'last_name', 'password', 'role'],
    'recipes.csv': ['name', 'text', 'cooking_time'],
}

models = {
    'users': User,
    'recipes': Recipe,
}


def make_image_file(data):
    """Разбивает по ;base64, на заголовок и строковый код картинки."""
    if not data:
        return None
    header, imagestr = data.split(';base64,')
    extension = header.split('/')[-1]
    str_now_time = str(now().time())
    filename = f'image_{str_now_time}.{extension}'
    return ContentFile(
        base64.b64decode(imagestr),
        name=filename
    )


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

    image_string = ('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgM'
                    'AAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAO'
                    'xAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==')

    def handle(self, *args, **options):
        """Функция валидации полей и импорта."""
        for csv_file_name in csv_files:
            model = csv_file_name.split('.')[0]
            model_class = models.get(model)
            for row in csv_reader_file(csv_file_name):
                if model_class == Recipe:
                    tags_queryset = Tag.objects.filter(
                        id__in=row['tags'].split('%')
                    )
                    ingredients_queryset = Ingredient.objects.filter(
                        id__in=row['ingredients'].split('%')
                    )
                    author = User.objects.get(username=row['author'])
                    recipe = Recipe.objects.create(
                        author=author,
                        name=row['name'],
                        image=make_image_file(self.image_string),
                        text=row['text'],
                        cooking_time=row['cooking_time'],
                    )
                    for ingredient_pk in row['ingredients'].split('%'):
                        IngredientRecipe.objects.create(
                            ingredient_id=ingredient_pk,
                            recipe=recipe,
                            amount=row['amount']
                        )
                    recipe.tags.set(tags_queryset)
                    recipe.ingredients.set(ingredients_queryset)
                elif model_class in (User, Ingredient, Tag):
                    item = None
                    if model_class == User:
                        item = User(
                            email=row['email'],
                            username=row['username'],
                            first_name=row['first_name'],
                            last_name=row['last_name'],
                            password=row['password'],
                            role=row['role'],
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
