import base64
import json
import mimetypes
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from core.r2_service import (
    generate_presigned_image_url,
)


load_dotenv()


client = OpenAI(
    api_key=os.getenv(
        "OPENAI_API_KEY"
    )
)


def image_to_data_url(
    image_path: str,
):
    """
    Превращает локальное изображение клиента
    во временный base64 data URL.

    Это используется для Story image,
    которую мы уже скачали во временный файл.
    """

    path = Path(
        image_path
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Image not found: {path}"
        )

    mime_type, _ = (
        mimetypes.guess_type(
            path.name
        )
    )

    if mime_type is None:
        mime_type = "image/jpeg"

    with open(
        path,
        "rb",
    ) as file:

        encoded = base64.b64encode(
            file.read()
        ).decode(
            "utf-8"
        )

    return (
        f"data:{mime_type};"
        f"base64,{encoded}"
    )


def verify_product_with_vision(
    query_image_path: str,
    candidates: list,
):
    """
    Финальная Vision-проверка.

    Первый image:
        изображение клиента / Story

    Остальные:
        TOP-кандидаты из Cloudflare R2

    Возвращает:

    {
        "result": "MATCH",
        "article": "34368"
    }

    либо:

    {
        "result": "NO_MATCH",
        "article": None
    }
    """

    if not candidates:

        return {
            "article": None,
            "result": "NO_MATCH",
        }

    # ==========================================
    # VALID ARTICLES
    # ==========================================

    candidate_articles = [
        str(
            candidate["article"]
        )
        for candidate in candidates
    ]

    # ==========================================
    # PROMPT
    # ==========================================

    instruction = f"""
You are verifying whether a customer image
matches one of the catalog products.

The first image is the CUSTOMER IMAGE.

After that you will receive candidate
catalog images.

Candidate product articles:

{candidate_articles}

Carefully compare:
- shape
- silhouette
- color
- material
- print
- logo
- seams
- neckline
- sleeves
- hardware
- handles
- proportions
- distinctive design details

Rules:

1. Choose a candidate only when it represents
   the same actual product.

2. Similar category or similar color alone
   is NOT enough.

3. If one candidate clearly matches,
   return MATCH and its article.

4. If none clearly matches,
   return NO_MATCH.

Return ONLY JSON.

Example:

{{
    "result": "MATCH",
    "article": "34368"
}}

or:

{{
    "result": "NO_MATCH",
    "article": null
}}
"""

    content = [
        {
            "type": "input_text",
            "text": instruction,
        },
        {
            "type": "input_text",
            "text": "CUSTOMER IMAGE:",
        },
        {
            "type": "input_image",
            "image_url": (
                image_to_data_url(
                    query_image_path
                )
            ),
            "detail": "high",
        },
    ]

    # ==========================================
    # R2 CANDIDATE IMAGES
    # ==========================================

    added_candidates = []

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        article = str(
            candidate["article"]
        )

        matched_image = str(
            candidate[
                "matched_image"
            ]
        )

        try:

            image_url = (
                generate_presigned_image_url(
                    matched_image,
                    expires_in=900,
                )
            )

        except Exception as error:

            print(
                f"R2 URL error for "
                f"{article}: {error}"
            )

            continue

        print(
            f"R2 candidate loaded: "
            f"{article}"
        )

        content.append(
            {
                "type": "input_text",
                "text": (
                    f"CANDIDATE {index} "
                    f"- ARTICLE {article}:"
                ),
            }
        )

        content.append(
            {
                "type": "input_image",
                "image_url": image_url,
                "detail": "high",
            }
        )

        added_candidates.append(
            article
        )

    # ==========================================
    # NO CANDIDATE IMAGES AVAILABLE
    # ==========================================

    if not added_candidates:

        print(
            "No R2 candidate images "
            "could be loaded."
        )

        return {
            "article": None,
            "result": "NO_MATCH",
        }

    # ==========================================
    # OPENAI VISION
    # ==========================================

    response = client.responses.create(
        model="gpt-5.6",
        input=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )

    raw_answer = (
        response.output_text
        .strip()
    )

    print(
        "\nVision raw answer:"
    )

    print(
        raw_answer
    )

    # ==========================================
    # CLEAN JSON
    # ==========================================

    cleaned_answer = (
        raw_answer
        .replace(
            "```json",
            "",
        )
        .replace(
            "```",
            "",
        )
        .strip()
    )

    try:

        result = json.loads(
            cleaned_answer
        )

    except json.JSONDecodeError:

        print(
            "Vision returned invalid JSON."
        )

        return {
            "article": None,
            "result": "NO_MATCH",
        }

    # ==========================================
    # VALIDATION
    # ==========================================

    result_type = result.get(
        "result"
    )

    returned_article = result.get(
        "article"
    )

    if returned_article is not None:

        returned_article = str(
            returned_article
        )

    if result_type != "MATCH":

        return {
            "article": None,
            "result": "NO_MATCH",
        }

    # Проверяем, что AI не придумал
    # артикул, которого вообще не было
    # среди реально отправленных кандидатов.

    if (
        returned_article
        not in added_candidates
    ):

        print(
            "Vision returned an article "
            "outside the provided candidates."
        )

        return {
            "article": None,
            "result": "NO_MATCH",
        }

    return {
        "article": returned_article,
        "result": "MATCH",
    }