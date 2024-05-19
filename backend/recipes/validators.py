import re

from django.core.exceptions import ValidationError

from config import URL_PROFILE_PREF, USERNAME_VALID_PATTERN


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


def validate_image(image):
    if not image:
        raise ValidationError(
            'Создание рецепта без картинки - невозможно.'
        )
    return image
