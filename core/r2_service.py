import os

import boto3
from dotenv import load_dotenv


load_dotenv()


R2_ACCESS_KEY_ID = os.getenv(
    "R2_ACCESS_KEY_ID"
)

R2_SECRET_ACCESS_KEY = os.getenv(
    "R2_SECRET_ACCESS_KEY"
)

R2_ENDPOINT = os.getenv(
    "R2_ENDPOINT"
)

R2_BUCKET_NAME = os.getenv(
    "R2_BUCKET_NAME"
)


def check_r2_configuration():
    """
    Проверяет наличие настроек R2.
    """

    missing = []

    if not R2_ACCESS_KEY_ID:
        missing.append(
            "R2_ACCESS_KEY_ID"
        )

    if not R2_SECRET_ACCESS_KEY:
        missing.append(
            "R2_SECRET_ACCESS_KEY"
        )

    if not R2_ENDPOINT:
        missing.append(
            "R2_ENDPOINT"
        )

    if not R2_BUCKET_NAME:
        missing.append(
            "R2_BUCKET_NAME"
        )

    if missing:
        raise ValueError(
            "Missing R2 environment variables: "
            + ", ".join(missing)
        )


def create_r2_client():
    """
    Создаёт S3-compatible клиент для Cloudflare R2.
    """

    check_r2_configuration()

    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=(
            R2_ACCESS_KEY_ID
        ),
        aws_secret_access_key=(
            R2_SECRET_ACCESS_KEY
        ),
        region_name="auto",
    )


def normalize_object_key(
    image_path: str,
):
    """
    Превращает старый локальный путь:

    clients/dofamin/product_images/34368/photo.webp

    в R2 object key:

    34368/photo.webp
    """

    normalized = str(
        image_path
    ).replace(
        "\\",
        "/",
    )

    prefix = (
        "clients/dofamin/"
        "product_images/"
    )

    if normalized.startswith(
        prefix
    ):
        normalized = normalized[
            len(prefix):
        ]

    return normalized.lstrip("/")


def generate_presigned_image_url(
    image_path: str,
    expires_in: int = 900,
):
    """
    Создаёт временный URL для чтения изображения.

    expires_in:
        время жизни URL в секундах.

        900 = 15 минут.
    """

    object_key = normalize_object_key(
        image_path
    )

    s3 = create_r2_client()

    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": R2_BUCKET_NAME,
            "Key": object_key,
        },
        ExpiresIn=expires_in,
    )

    return url