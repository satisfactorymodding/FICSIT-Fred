from typing import IO

from PIL import Image, ImageEnhance
from pytesseract import image_to_string, TesseractError

from fred.libraries.common import new_logger

logger = new_logger(__name__)


def read(file: IO):
    try:
        image = Image.open(file)
        ratio = 2160 / image.height
        if ratio > 1:
            image = image.resize((round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS)
        try:
            enhancer_contrast = ImageEnhance.Contrast(image)

            image = enhancer_contrast.enhance(2)
            enhancer_sharpness = ImageEnhance.Sharpness(image)
            image = enhancer_sharpness.enhance(10)
        except ValueError as e:
            logger.warning("Failed to enhance contrast.")
            logger.exception(e)

        image_text = image_to_string(image)
        logger.info("OCR returned the following data:\n" + image_text)
        return image_text

    except TesseractError as oops:
        logger.error(f"OCR error!")
        logger.exception(oops)
        return ""
