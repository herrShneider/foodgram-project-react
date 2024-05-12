import base64

from django.core.files.base import ContentFile
from django.utils.timezone import now


def to_internal_value(image: str):
    """Разбивает по ;base64, на заголовок и строковый код картинки."""
    if not image:
        return None
    header, imagestr = image.split(';base64,')
    extension = header.split('/')[-1]
    str_now_time = str(now().time())
    filename = f'image_{str_now_time}.{extension}'
    return ContentFile(
        base64.b64decode(imagestr),
        name=filename
    )