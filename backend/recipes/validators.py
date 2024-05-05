import re

from django.core.exceptions import ValidationError

from config import TAG_COLOR_VALID_PATTERN, URL_PROFILE_PREF, USERNAME_VALID_PATTERN


def validate_username_via_regex(username):
    """Валидация поля username."""
    invalid_characters = re.sub(USERNAME_VALID_PATTERN, '', username)
    if invalid_characters:
        invalid_characters = "".join(set(invalid_characters))
        raise ValidationError(
            f'В username найдены недопустимые символы '
            f'{invalid_characters}'
        )

    return username


def validate_not_me(username):
    """Функция-валидатор. Проверяет, что username != me."""
    if username == URL_PROFILE_PREF:
        raise ValidationError(
            f'Использовать имя "{URL_PROFILE_PREF}" в '
            f'качестве username запрещено.'
        )

    return username


def validate_hex_color(value):
    if not re.match(TAG_COLOR_VALID_PATTERN, value):
        raise ValidationError('Введите действительный шестнадцатеричный код цвета.')


# def validate_ingredients(ingredients):
#     print(ingredients)
#     print('KUKUKUKU')
#     print(type(ingredients))
#     if True:
#         raise ValidationError(
#             f'Использовать имя  в '
#             f'качестве username запрещено.'
#         )
#
#     return ingredients
