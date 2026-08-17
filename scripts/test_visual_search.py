from pathlib import Path
import sys


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent

sys.path.append(
    str(PROJECT_ROOT)
)


from core.visual_search_service import (
    search_similar_products,
)

from core.vision_service import (
    verify_product_with_vision,
)


TEST_IMAGE = (
    PROJECT_ROOT
    / "test_images"
    / "test.jpg"
)


def main():

    print(
        "\n========================================"
    )

    print(
        "DOFAMIN VISUAL SEARCH + VISION TEST"
    )

    print(
        "========================================"
    )

    if not TEST_IMAGE.exists():

        print(
            f"Test image not found: "
            f"{TEST_IMAGE}"
        )

        return

    # ==========================================
    # STEP 1 — CLIP
    # ==========================================

    print(
        "\nSTEP 1: CLIP SEARCH"
    )

    candidates = (
        search_similar_products(
            image_path=str(
                TEST_IMAGE
            ),
            top_k=3,
        )
    )

    print(
        "\nTOP-3 CANDIDATES:\n"
    )

    for position, candidate in enumerate(
        candidates,
        start=1,
    ):

        similarity = (
            candidate[
                "similarity"
            ]
            * 100
        )

        print(
            f"{position}. "
            f"Article: "
            f"{candidate['article']}"
        )

        print(
            f"   Similarity: "
            f"{similarity:.2f}%"
        )

        print(
            f"   Image: "
            f"{candidate['matched_image']}"
        )

        print()

    # ==========================================
    # STEP 2 — VISION
    # ==========================================

    print(
        "\nSTEP 2: VISION VERIFICATION"
    )

    result = (
        verify_product_with_vision(
            query_image_path=str(
                TEST_IMAGE
            ),
            candidates=candidates,
        )
    )

    print(
        "\n========================================"
    )

    print(
        "FINAL RESULT"
    )

    print(
        "========================================"
    )

    print(
        f"Result: "
        f"{result['result']}"
    )

    print(
        f"Article: "
        f"{result['article']}"
    )

    print(
        "========================================\n"
    )


if __name__ == "__main__":
    main()