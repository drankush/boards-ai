"""
BOARDS-AI — Image Utilities
============================
Creates a tiled image collage from base64-encoded case images.
Mirrors the exact logic from the production ``cloud_case.py``.
"""

import base64
import io

from PIL import Image


def process_images(images: list[dict]) -> tuple[str | None, str]:
    """
    Build a tiled collage from a list of image dicts.

    Parameters
    ----------
    images : list[dict]
        Each dict must have ``"base64"`` (data-URI string) and ``"caption"``.

    Returns
    -------
    tuple[str | None, str]
        (collage_base64_data_uri, concatenated_captions)
    """
    if not images:
        return None, "No images available"

    num_images = len(images)
    if num_images <= 3:
        rows, cols = 1, num_images
    elif num_images <= 6:
        rows, cols = 2, 3
    else:
        rows, cols = 3, 3  # Max 9 images

    max_height = 500
    images_pil = []
    for img in images[:9]:
        b64_str = img["base64"]
        # Strip the data-URI prefix if present
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        images_pil.append(Image.open(io.BytesIO(base64.b64decode(b64_str))))

    # Resize maintaining aspect ratio
    resized_images: list[Image.Image] = []
    max_width = 0
    for im in images_pil:
        ratio = max_height / im.height
        width = int(im.width * ratio)
        resized_images.append(im.resize((width, max_height), Image.LANCZOS))
        max_width = max(max_width, width)

    # Create collage with dark background (#1A1C21)
    collage_width = max_width * cols
    collage_height = max_height * rows
    collage = Image.new("RGB", (collage_width, collage_height), (26, 28, 33))
    for idx, im in enumerate(resized_images):
        x = (idx % cols) * max_width
        y = (idx // cols) * max_height
        collage.paste(im, (x, y))

    # Encode to base64
    buf = io.BytesIO()
    collage.save(buf, format="JPEG")
    img_b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    captions = ". ".join(
        f"The image {i + 1} shows {images[i]['caption']}"
        for i in range(min(9, len(images)))
    )
    return img_b64, captions
