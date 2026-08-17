from pathlib import Path

import torch
import open_clip
from PIL import Image


MODEL_NAME = "ViT-B-32"
PRETRAINED = "laion2b_s34b_b79k"


device = "cuda" if torch.cuda.is_available() else "cpu"


model, _, preprocess = open_clip.create_model_and_transforms(
    MODEL_NAME,
    pretrained=PRETRAINED,
)

model = model.to(device)
model.eval()


def create_image_embedding(image_path: str):
    """
    Превращает изображение в embedding-вектор.

    image_path:
        путь к изображению

    return:
        torch.Tensor с нормализованным embedding
    """

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = Image.open(image_path).convert("RGB")

    image_tensor = preprocess(image)

    image_tensor = image_tensor.unsqueeze(0)

    image_tensor = image_tensor.to(device)

    with torch.no_grad():

        embedding = model.encode_image(
            image_tensor
        )

        embedding = embedding / embedding.norm(
            dim=-1,
            keepdim=True,
        )

    return embedding.cpu()


if __name__ == "__main__":

    print(
        f"Device: {device}"
    )

    print(
        "Image embedding service loaded successfully."
    )