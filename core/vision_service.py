import base64
import json
import mimetypes
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent


def image_to_data_url(
    image_path: str,
):
    """
    Превращает локальную картинку
    в data URL для отправки в OpenAI.
    """

    path = Path(
        image_path
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Image not found: {path}"
        )

    mime_type, _ = mimetypes.guess_type(
        path.name
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
    query_image_path:
        фотография клиента

    candidates:
        TOP-кандидаты из visual search

    Возвращает:

        {
            "article": "...",
            "result": "MATCH"
        }

    или:

        {
            "article": None,
            "result": "NO_MATCH"
        }
    """

    if not candidates:

        return {
            "article": None,
            "result": "NO_MATCH",
        }

    content = []

    # ==========================================
    # CANDIDATE ARTICLES
    # ==========================================

    candidate_articles = [
        str(
            candidate["article"]
        )
        for candidate in candidates
    ]

    # ==========================================
    # INSTRUCTIONS
    # ==========================================

    instruction = f"""
You are verifying a product match for
an online fashion store.

The first image is the CUSTOMER IMAGE.

After it, you will receive catalog images
for candidate products.

Candidate articles:

{candidate_articles}

Your task:

1. Compare the customer image with all
   candidate products carefully.

2. Pay attention to:
   - shape
   - material
   - color
   - pattern
   - logos
   - seams
   - handles
   - hardware
   - proportions
   - distinctive details

3. Do NOT choose a candidate only because
   the product category or color is similar.

4. If one candidate clearly represents
   the same product, return its article.

5. If none of the candidates is clearly
   the same product, return NO_MATCH.

Return ONLY valid JSON.

MATCH example:

{{
    "result": "MATCH",
    "article": "49479"
}}

NO MATCH example:

{{
    "result": "NO_MATCH",
    "article": null
}}
"""

    content.append(
        {
            "type": "input_text",
            "text": instruction,
        }
    )

    # ==========================================
    # CUSTOMER IMAGE
    # ==========================================

    content.append(
        {
            "type": "input_text",
            "text": "CUSTOMER IMAGE:",
        }
    )

    content.append(
        {
            "type": "input_image",
            "image_url": image_to_data_url(
                query_image_path
            ),
            "detail": "high",
        }
    )

    # ==========================================
    # CANDIDATES
    # ==========================================

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        article = str(
            candidate[
                "article"
            ]
        )

        # ======================================
        # WINDOWS -> LINUX PATH FIX
        # ======================================

        matched_image = str(
            candidate[
                "matched_image"
            ]
        ).replace(
            "\\",
            "/",
        )

        candidate_image_path = (
            PROJECT_ROOT
            / matched_image
        )

        if not candidate_image_path.exists():

            print(
                "Candidate image not found:"
            )

            print(
                candidate_image_path
            )

            continue

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
                "image_url": (
                    image_to_data_url(
                        str(
                            candidate_image_path
                        )
                    )
                ),
                "detail": "high",
            }
        )

    # ==========================================
    # OPENAI
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

    raw_answer = (
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
            raw_answer
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
    # SECURITY / VALIDATION
    # ==========================================

    returned_article = result.get(
        "article"
    )

    result_type = result.get(
        "result"
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

    if (
        returned_article
        not in candidate_articles
    ):

        print(
            "Vision returned article "
            "outside candidate list."
        )

        return {
            "article": None,
            "result": "NO_MATCH",
        }

    return {
        "article": returned_article,
        "result": "MATCH",
    }