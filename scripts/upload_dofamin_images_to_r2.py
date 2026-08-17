import mimetypes
import os
import sys
from pathlib import Path

import boto3
from dotenv import load_dotenv


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent

sys.path.append(
    str(PROJECT_ROOT)
)


load_dotenv(
    PROJECT_ROOT / ".env"
)


PRODUCT_IMAGES_DIR = (
    PROJECT_ROOT
    / "clients"
    / "dofamin"
    / "product_images"
)


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


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def check_environment():

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
            "Missing environment variables: "
            + ", ".join(missing)
        )


def create_r2_client():

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


def get_content_type(
    file_path: Path,
):

    content_type, _ = (
        mimetypes.guess_type(
            file_path.name
        )
    )

    if content_type:
        return content_type

    return (
        "application/octet-stream"
    )


def upload_images():

    print(
        "\n========================================"
    )

    print(
        "UPLOAD DOFAMIN IMAGES TO R2"
    )

    print(
        "========================================\n"
    )

    check_environment()

    if not PRODUCT_IMAGES_DIR.exists():

        raise FileNotFoundError(
            f"Product images folder "
            f"not found: "
            f"{PRODUCT_IMAGES_DIR}"
        )

    s3 = create_r2_client()

    uploaded = 0
    failed = 0

    product_folders = sorted(
        [
            folder
            for folder
            in PRODUCT_IMAGES_DIR.iterdir()
            if folder.is_dir()
        ],
        key=lambda folder: (
            folder.name
        ),
    )

    print(
        f"Products found: "
        f"{len(product_folders)}"
    )

    print()

    for product_folder in (
        product_folders
    ):

        article = (
            product_folder.name
        )

        print(
            f"Article: {article}"
        )

        image_files = sorted(
            [
                file
                for file
                in product_folder.iterdir()
                if (
                    file.is_file()
                    and file.suffix.lower()
                    in SUPPORTED_EXTENSIONS
                )
            ],
            key=lambda file: (
                file.name
            ),
        )

        if not image_files:

            print(
                "  No images found."
            )

            print()

            continue

        for image_file in (
            image_files
        ):

            # ==================================
            # R2 OBJECT KEY
            #
            # Example:
            #
            # 34368/photo.webp
            # ==================================

            object_key = (
                f"{article}/"
                f"{image_file.name}"
            )

            try:

                content_type = (
                    get_content_type(
                        image_file
                    )
                )

                print(
                    f"  -> Uploading "
                    f"{object_key}"
                )

                s3.upload_file(
                    str(
                        image_file
                    ),
                    R2_BUCKET_NAME,
                    object_key,
                    ExtraArgs={
                        "ContentType": (
                            content_type
                        )
                    },
                )

                uploaded += 1

            except Exception as error:

                failed += 1

                print(
                    f"  ERROR: "
                    f"{error}"
                )

        print()

    print(
        "========================================"
    )

    print(
        "UPLOAD FINISHED"
    )

    print(
        f"Uploaded: {uploaded}"
    )

    print(
        f"Failed: {failed}"
    )

    print(
        "========================================\n"
    )


if __name__ == "__main__":

    upload_images()