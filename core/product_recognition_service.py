from core.visual_search_service import search_similar_products
from core.vision_service import verify_product_with_vision


def recognize_product(
    image_path: str,
):
    """
    Полный pipeline распознавания товара по фотографии.

    Возвращает:
        article товара, например "49479"

    или:
        None
    """

    # ==========================================
    # STEP 1 — CLIP SEARCH
    # ==========================================

    candidates = search_similar_products(
        image_path=image_path,
        top_k=3,
    )

    if not candidates:
        return None

    # ==========================================
    # STEP 2 — VISION VERIFICATION
    # ==========================================

    result = verify_product_with_vision(
        query_image_path=image_path,
        candidates=candidates,
    )

    # ==========================================
    # FINAL RESULT
    # ==========================================

    if result.get("result") != "MATCH":
        return None

    article = result.get("article")

    if not article:
        return None

    return article