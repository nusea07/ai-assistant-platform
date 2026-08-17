from pathlib import Path

import torch
import open_clip
from PIL import Image


MODEL_ID = "hf-hub:apple/MobileCLIP-S1-OpenCLIP"

device = "cuda" if torch.cuda.is_available() else "cpu"


model = None
preprocess = None


def load_model():
    """
    Загружает MobileCLIP-S1 только при первом использовании.
    """

    global model
    global preprocess

    if model is not None and preprocess is not None:
        return model, preprocess

    print("Loading MobileCLIP-S1...")

    loaded_model, _, loaded_preprocess = (
        open_clip.create_model_and_transforms(
            MODEL_ID
        )
    )

    loaded_model = loaded_model.to(device)
    loaded_model.eval()

    model = loaded_model
    preprocess = loaded_preprocess

    print(
        f"MobileCLIP-S1 loaded on: {device}"
    )

    return model, preprocess


def create_image_embedding(
    image_path: str,
):
    """
    Превращает изображение в нормализованный embedding.
    """

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    current_model, current_preprocess = (
        load_model()
    )

    image = Image.open(
        image_path
    ).convert("RGB")

    image_tensor = (
        current_preprocess(image)
        .unsqueeze(0)
        .to(device)
    )

    with torch.no_grad():

        embedding = (
            current_model.encode_image(
                image_tensor
            )
        )

        embedding = (
            embedding
            / embedding.norm(
                dim=-1,
                keepdim=True,
            )
        )

    return embedding.cpu()


if __name__ == "__main__":

    print(
        f"Device: {device}"
    )

    load_model()

    print(
        "MobileCLIP embedding service loaded successfully."
    )