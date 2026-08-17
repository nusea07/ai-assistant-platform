from pathlib import Path
import pickle
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.append(str(PROJECT_ROOT))


from core.image_embedding_service import create_image_embedding


PRODUCT_IMAGES_DIR = (
    PROJECT_ROOT
    / "clients"
    / "dofamin"
    / "product_images"
)

VISUAL_INDEX_DIR = (
    PROJECT_ROOT
    / "data"
    / "visual_index"
)

OUTPUT_FILE = (
    VISUAL_INDEX_DIR
    / "dofamin_embeddings.pkl"
)


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def build_visual_index():

    print("\n========================================")
    print("BUILDING DOFAMIN VISUAL INDEX")
    print("========================================\n")

    if not PRODUCT_IMAGES_DIR.exists():
        raise FileNotFoundError(
            f"Product images folder not found: "
            f"{PRODUCT_IMAGES_DIR}"
        )

    VISUAL_INDEX_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    visual_index = []

    product_folders = [
        folder
        for folder in PRODUCT_IMAGES_DIR.iterdir()
        if folder.is_dir()
    ]

    if not product_folders:
        raise ValueError(
            "No product folders found."
        )

    print(
        f"Products found: "
        f"{len(product_folders)}"
    )

    print()

    for product_folder in product_folders:

        article = product_folder.name

        print(
            f"Processing article: {article}"
        )

        image_files = [
            file
            for file in product_folder.iterdir()
            if (
                file.is_file()
                and file.suffix.lower()
                in SUPPORTED_EXTENSIONS
            )
        ]

        if not image_files:

            print(
                "  No images found. Skipping."
            )

            continue

        for image_file in image_files:

            print(
                f"  -> {image_file.name}"
            )

            try:

                embedding = (
                    create_image_embedding(
                        str(image_file)
                    )
                )

                visual_index.append(
                    {
                        "article": article,
                        "image_path": str(
                            image_file.relative_to(
                                PROJECT_ROOT
                            )
                        ),
                        "embedding": embedding,
                    }
                )

            except Exception as error:

                print(
                    f"  ERROR: {error}"
                )

        print()

    if not visual_index:
        raise ValueError(
            "No image embeddings were created."
        )

    with open(
        OUTPUT_FILE,
        "wb",
    ) as file:

        pickle.dump(
            visual_index,
            file,
        )

    print(
        "========================================"
    )

    print(
        "VISUAL INDEX CREATED SUCCESSFULLY"
    )

    print(
        f"Embeddings created: "
        f"{len(visual_index)}"
    )

    print(
        "Saved to:"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "========================================\n"
    )


if __name__ == "__main__":
    build_visual_index()