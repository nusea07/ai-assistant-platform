from pathlib import Path
import pickle

import torch

from core.image_embedding_service import create_image_embedding


PROJECT_ROOT = Path(__file__).resolve().parent.parent

VISUAL_INDEX_FILE = (
    PROJECT_ROOT
    / "data"
    / "visual_index"
    / "dofamin_embeddings.pkl"
)


def load_visual_index():

    if not VISUAL_INDEX_FILE.exists():
        raise FileNotFoundError(
            f"Visual index not found: {VISUAL_INDEX_FILE}"
        )

    with open(
        VISUAL_INDEX_FILE,
        "rb",
    ) as file:

        visual_index = pickle.load(file)

    return visual_index


def search_similar_products(
    image_path: str,
    top_k: int = 3,
):

    print("\nCreating embedding for test image...")

    query_embedding = create_image_embedding(
        image_path
    )

    visual_index = load_visual_index()

    print(
        f"Comparing with "
        f"{len(visual_index)} catalog images..."
    )

    # Здесь будем хранить лучший результат
    # для каждого артикула.
    product_scores = {}

    for item in visual_index:

        article = item["article"]

        catalog_embedding = item[
            "embedding"
        ]

        similarity = torch.sum(
            query_embedding
            * catalog_embedding
        ).item()

        current_best = product_scores.get(
            article
        )

        if (
            current_best is None
            or similarity
            > current_best["similarity"]
        ):

            product_scores[article] = {
                "article": article,
                "similarity": similarity,
                "matched_image": item[
                    "image_path"
                ],
            }

    results = sorted(
        product_scores.values(),
        key=lambda item: item["similarity"],
        reverse=True,
    )

    return results[:top_k]