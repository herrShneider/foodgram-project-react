import re

from django.core.exceptions import ValidationError

from config import (COOK_TIME_MAX_VALUE, COOK_TIME_MIN_VALUE,
                    TAG_COLOR_VALID_PATTERN, URL_PROFILE_PREF,
                    USERNAME_VALID_PATTERN)


def validate_username_via_regex(username):
    invalid_characters = re.sub(USERNAME_VALID_PATTERN, '', username)
    if invalid_characters:
        invalid_characters = "".join(set(invalid_characters))
        raise ValidationError(
            f'В username найдены недопустимые символы '
            f'{invalid_characters}'
        )

    return username


def validate_not_me(username):
    if username == URL_PROFILE_PREF:
        raise ValidationError(
            f'Использовать имя "{URL_PROFILE_PREF}" в '
            f'качестве username запрещено.'
        )

    return username


def validate_hex_color(value):
    if not re.match(TAG_COLOR_VALID_PATTERN, value):
        raise ValidationError(
            'Введите действительный шестнадцатеричный код цвета.'
        )


def validate_amount(amount):
    if amount < 1:
        raise ValidationError('Колличество не может быть меньше 1.')
    return amount


def validate_image(image):
    if not image:
        raise ValidationError(
            'Создание рецепта без картинки - невозможно.'
        )
    return image


def validate_cooking_time(cooking_time):
    if cooking_time < COOK_TIME_MIN_VALUE:
        raise ValidationError(
            f'Время приготовления не может быть меньше {COOK_TIME_MIN_VALUE}.'
        )
    elif cooking_time > COOK_TIME_MAX_VALUE:
        raise ValidationError(
            f'Время приготовления не может быть больше {COOK_TIME_MAX_VALUE}.'
        )
    return cooking_time
