from pathlib import Path
import pickle
import sys


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent


sys.path.append(
    str(
        PROJECT_ROOT
    )
)


from core.image_embedding_service import (
    create_image_embedding,
)


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

    print(
        "\n========================================"
    )

    print(
        "BUILDING DOFAMIN VISUAL INDEX"
    )

    print(
        "========================================\n"
    )

    # ==========================================
    # CHECK PRODUCT IMAGE DIRECTORY
    # ==========================================

    if not PRODUCT_IMAGES_DIR.exists():

        raise FileNotFoundError(
            f"Product images folder "
            f"not found: "
            f"{PRODUCT_IMAGES_DIR}"
        )

    # ==========================================
    # CREATE OUTPUT DIRECTORY
    # ==========================================

    VISUAL_INDEX_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    visual_index = []

    # ==========================================
    # GET PRODUCT FOLDERS
    # ==========================================

    product_folders = sorted(
        [
            folder
            for folder
            in PRODUCT_IMAGES_DIR.iterdir()
            if folder.is_dir()
        ],
        key=lambda folder: folder.name,
    )

    if not product_folders:

        raise ValueError(
            "No product folders found."
        )

    print(
        f"Products found: "
        f"{len(product_folders)}"
    )

    print()

    # ==========================================
    # PROCESS PRODUCTS
    # ==========================================

    for product_folder in product_folders:

        article = (
            product_folder.name
        )

        print(
            f"Processing article: "
            f"{article}"
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
            key=lambda file: file.name,
        )

        if not image_files:

            print(
                "  No images found. "
                "Skipping."
            )

            print()

            continue

        # ======================================
        # PROCESS EACH IMAGE
        # ======================================

        for image_file in image_files:

            print(
                f"  -> {image_file.name}"
            )

            try:

                embedding = (
                    create_image_embedding(
                        str(
                            image_file
                        )
                    )
                )

                # ==================================
                # IMPORTANT:
                # always save POSIX-style path
                #
                # clients/dofamin/...
                #
                # NOT:
                #
                # clients\\dofamin\\...
                # ==================================

                relative_image_path = (
                    image_file
                    .relative_to(
                        PROJECT_ROOT
                    )
                    .as_posix()
                )

                visual_index.append(
                    {
                        "article": (
                            article
                        ),
                        "image_path": (
                            relative_image_path
                        ),
                        "embedding": (
                            embedding
                        ),
                    }
                )

            except Exception as error:

                print(
                    f"  ERROR: "
                    f"{error}"
                )

        print()

    # ==========================================
    # CHECK RESULTS
    # ==========================================

    if not visual_index:

        raise ValueError(
            "No image embeddings "
            "were created."
        )

    # ==========================================
    # SAVE INDEX
    # ==========================================

    with open(
        OUTPUT_FILE,
        "wb",
    ) as file:

        pickle.dump(
            visual_index,
            file,
        )

    # ==========================================
    # SUCCESS
    # ==========================================

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