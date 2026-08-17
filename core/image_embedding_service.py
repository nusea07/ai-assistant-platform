from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "mobileclip"
    / "mobileclip-s0-visual.onnx"
)


session = None
input_name = None


def load_model():
    """
    Загружает ONNX vision-модель только при первом использовании.
    """

    global session
    global input_name

    if session is not None:
        return session

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"ONNX model not found: {MODEL_PATH}"
        )

    print("Loading MobileCLIP ONNX model...")

    session = ort.InferenceSession(
        str(MODEL_PATH),
        providers=[
            "CPUExecutionProvider"
        ],
    )

    input_name = session.get_inputs()[0].name

    print("MobileCLIP ONNX model loaded.")
    print(f"Input name: {input_name}")

    return session


def preprocess_image(
    image_path: str,
):
    """
    Подготавливает изображение для MobileCLIP.
    """

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = Image.open(
        image_path
    ).convert("RGB")

    # MobileCLIP обычно работает с 256x256 / 224x224 input.
    # Начинаем с 256 и проверим форму модели ниже.
    image = image.resize(
        (256, 256)
    )

    image_array = np.asarray(
        image,
        dtype=np.float32,
    )

    # [H, W, C] -> [C, H, W]
    image_array = np.transpose(
        image_array,
        (2, 0, 1),
    )

    # Нормализация в диапазон 0..1
    image_array = (
        image_array / 255.0
    )

    # CLIP normalization
    mean = np.array(
        [
            0.48145466,
            0.4578275,
            0.40821073,
        ],
        dtype=np.float32,
    ).reshape(3, 1, 1)

    std = np.array(
        [
            0.26862954,
            0.26130258,
            0.27577711,
        ],
        dtype=np.float32,
    ).reshape(3, 1, 1)

    image_array = (
        image_array - mean
    ) / std

    # [C, H, W] -> [1, C, H, W]
    image_array = np.expand_dims(
        image_array,
        axis=0,
    )

    return image_array.astype(
        np.float32
    )


def create_image_embedding(
    image_path: str,
):
    """
    Превращает изображение
    в нормализованный embedding.
    """

    current_session = load_model()

    image_tensor = preprocess_image(
        image_path
    )

    outputs = current_session.run(
        None,
        {
            input_name: image_tensor
        },
    )

    embedding = outputs[0]

    embedding = np.asarray(
        embedding,
        dtype=np.float32,
    )

    # Если модель вернула лишние измерения
    embedding = embedding.reshape(
        embedding.shape[0],
        -1,
    )

    # L2 normalization
    norm = np.linalg.norm(
        embedding,
        axis=1,
        keepdims=True,
    )

    embedding = (
        embedding
        / np.clip(
            norm,
            1e-12,
            None,
        )
    )

    return embedding


if __name__ == "__main__":

    print(
        "Testing MobileCLIP ONNX model..."
    )

    current_session = load_model()

    print(
        "\nModel inputs:"
    )

    for model_input in (
        current_session.get_inputs()
    ):
        print(
            f"Name: {model_input.name}"
        )
        print(
            f"Shape: {model_input.shape}"
        )
        print(
            f"Type: {model_input.type}"
        )

    print(
        "\nModel outputs:"
    )

    for model_output in (
        current_session.get_outputs()
    ):
        print(
            f"Name: {model_output.name}"
        )
        print(
            f"Shape: {model_output.shape}"
        )
        print(
            f"Type: {model_output.type}"
        )

    print(
        "\nONNX model loaded successfully."
    )