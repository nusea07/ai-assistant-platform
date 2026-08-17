import tempfile
from pathlib import Path

import requests


def download_image(image_url: str) -> str:
    """
    Скачивает изображение по URL
    и сохраняет его во временный файл.

    Возвращает путь к локальному файлу.
    """

    response = requests.get(
        image_url,
        timeout=30,
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type",
        "",
    )

    if "png" in content_type:
        suffix = ".png"

    elif "webp" in content_type:
        suffix = ".webp"

    else:
        suffix = ".jpg"

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    )

    temp_file.write(
        response.content
    )

    temp_file.close()

    return str(
        Path(temp_file.name)
    )