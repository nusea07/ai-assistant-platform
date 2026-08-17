from pathlib import Path
import sys


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent

sys.path.append(
    str(PROJECT_ROOT)
)


from core.product_recognition_service import (
    recognize_product,
)


TEST_IMAGE = (
    PROJECT_ROOT
    / "test_images"
    / "test.jpg"
)


def main():

    print("\n========================================")
    print("DOFAMIN PRODUCT RECOGNITION TEST")
    print("========================================\n")

    if not TEST_IMAGE.exists():

        print(
            f"Test image not found: "
            f"{TEST_IMAGE}"
        )

        return

    article = recognize_product(
        image_path=str(TEST_IMAGE)
    )

    print("\n========================================")
    print("FINAL PRODUCT")
    print("========================================")

    if article:

        print(
            f"Recognized article: {article}"
        )

    else:

        print(
            "Product was not recognized."
        )

    print("========================================\n")


if __name__ == "__main__":
    main()