import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from core.client_registry import get_client


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
CLIENTS_DIR = BASE_DIR / "clients"

load_dotenv(ENV_PATH)


# ==========================================================
# OPENAI
# ==========================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("В .env отсутствует OPENAI_API_KEY")


OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6",
)

client = OpenAI(
    api_key=OPENAI_API_KEY
)


# ==========================================================
# CLIENT PROMPT
# ==========================================================

def load_client_prompt(
    client_id: str,
) -> str:
    client_config = get_client(
        client_id
    )

    if client_config is None:
        return ""

    client_folder = client_config[
        "folder"
    ]

    prompt_path = (
        CLIENTS_DIR
        / client_folder
        / "prompt.txt"
    )

    if not prompt_path.exists():
        return ""

    return prompt_path.read_text(
        encoding="utf-8"
    ).strip()


# ==========================================================
# SOURCES FROM WEB SEARCH
# ==========================================================

def extract_sources(
    response,
) -> list[str]:
    sources = []

    for item in response.output:
        if getattr(
            item,
            "type",
            None,
        ) != "message":
            continue

        for content in getattr(
            item,
            "content",
            [],
        ):
            annotations = getattr(
                content,
                "annotations",
                [],
            )

            for annotation in annotations:
                if getattr(
                    annotation,
                    "type",
                    None,
                ) != "url_citation":
                    continue

                url = getattr(
                    annotation,
                    "url",
                    None,
                )

                if (
                    url
                    and url not in sources
                ):
                    sources.append(url)

    return sources


# ==========================================================
# SYSTEM INSTRUCTIONS
# ==========================================================

def build_instructions(
    client_id: str,
) -> str:
    client_config = get_client(
        client_id
    )

    if client_config is None:
        client_name = client_id

    else:
        client_name = client_config[
            "name"
        ]

    custom_prompt = load_client_prompt(
        client_id
    )

    instructions = f"""
Ты AI-консультант бизнеса {client_name}.

Ты общаешься с клиентами в Instagram Direct.

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА:

1. Отвечай на языке клиента.

2. Отвечай естественно, коротко и дружелюбно.
Не пиши слишком длинные сообщения без необходимости.

3. Не говори, что ты ChatGPT, OpenAI,
языковая модель или искусственный интеллект.

4. Никогда не придумывай:
- цены;
- наличие;
- размеры;
- цвета;
- состав;
- расписание;
- адреса;
- условия доставки;
- акции;
- скидки;
- правила возврата;
- другие факты бизнеса.

5. Если в PRODUCT CONTEXT переданы данные товара,
используй именно эти данные как источник истины
для цены, размера, цвета и наличия.

6. Не отвечай на другой вопрос только потому,
что в памяти остался предыдущий товар.

Например:
клиент спрашивает:
"Сколько лет вашему магазину?"

НЕЛЬЗЯ отвечать ценой предыдущего товара.

7. Сначала внимательно пойми,
О ЧЁМ именно спрашивает клиент:
- о товаре;
- о самом бизнесе;
- о доставке;
- об услуге;
- о заказе;
- или задаёт обычный вопрос.

8. Если достоверных данных недостаточно
и интернет-поиск НЕ был предоставлен,
прямо скажи, что точной информации сейчас нет.

9. Если предоставлен интернет-поиск,
используй его только для ответа
на фактический вопрос клиента.

10. Никогда не выдавай предположение
за подтверждённый факт.

11. Не повторяй приветствие в каждом сообщении.

12. Не добавляй цену или характеристики товара,
если клиент их не спрашивал.
"""

    if custom_prompt:
        instructions += f"""

ДОПОЛНИТЕЛЬНЫЕ ПРАВИЛА КЛИЕНТА:

{custom_prompt}
"""

    return instructions.strip()


# ==========================================================
# NORMAL AI RESPONSE
# ==========================================================

def generate_ai_response(
    client_id: str,
    user_message: str,
    product_context: str = "",
    business_context: str = "",
    conversation_context: str = "",
) -> str:

    user_message = (
        user_message or ""
    ).strip()

    if not user_message:
        return ""

    instructions = build_instructions(
        client_id
    )

    input_text = f"""
BUSINESS CONTEXT:
{business_context or "Нет дополнительных данных."}

PRODUCT CONTEXT:
{product_context or "Товар не указан."}

CONVERSATION CONTEXT:
{conversation_context or "Нет дополнительного контекста."}

CURRENT CLIENT MESSAGE:
{user_message}

Ответь только на CURRENT CLIENT MESSAGE.
"""

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=instructions,
            input=input_text,
            max_output_tokens=300,
        )

        answer = (
            response.output_text
            or ""
        ).strip()

        if answer:
            return answer

        return (
            "Мне не удалось сформировать "
            "точный ответ. Лучше уточнить "
            "этот вопрос у сотрудника."
        )

    except Exception as error:
        print(
            f"Ошибка OpenAI API: {error}"
        )

        return (
            "Сейчас не удалось обработать "
            "ваш вопрос автоматически. "
            "Я могу передать его сотруднику."
        )


# ==========================================================
# AI + WEB SEARCH
# ==========================================================

def generate_web_response(
    client_id: str,
    user_message: str,
    business_context: str = "",
    allowed_domains: list[str] | None = None,
) -> str:

    user_message = (
        user_message or ""
    ).strip()

    if not user_message:
        return ""

    instructions = build_instructions(
        client_id
    )

    instructions += """

Ты получил доступ к интернет-поиску.

Найди подтверждение ответа в интернете.

Если надёжного подтверждения нет,
не придумывай ответ.

Предпочитай официальный сайт бизнеса
и официальные источники.
"""

    web_tool = {
        "type": "web_search"
    }

    if allowed_domains:
        web_tool["filters"] = {
            "allowed_domains":
                allowed_domains
        }

    input_text = f"""
BUSINESS CONTEXT:
{business_context or "Нет дополнительных данных."}

QUESTION:
{user_message}

Найди точный подтверждённый ответ.
"""

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=instructions,
            tools=[
                web_tool
            ],
            tool_choice="required",
            input=input_text,
            max_output_tokens=350,
        )

        answer = (
            response.output_text
            or ""
        ).strip()

        sources = extract_sources(
            response
        )

        # Для Instagram добавляем максимум
        # две ссылки на источники.
        if sources:
            visible_sources = sources[:2]

            answer += (
                "\n\nИсточники:\n"
                + "\n".join(
                    visible_sources
                )
            )

        if answer:
            return answer

        return (
            "Мне не удалось найти "
            "подтверждённую информацию. "
            "Лучше уточнить этот вопрос "
            "у сотрудника."
        )

    except Exception as error:
        print(
            f"Ошибка OpenAI Web Search: "
            f"{error}"
        )

        return (
            "Сейчас не удалось проверить "
            "эту информацию. Лучше уточнить "
            "вопрос у сотрудника."
        )