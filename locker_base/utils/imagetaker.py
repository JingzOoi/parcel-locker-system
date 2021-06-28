import logging
from utils.construct import construct_logger
from picamera import PiCamera
import numpy as np
import cv2
from imutils import resize, rotate
import imutils
from PIL import ImageEnhance, Image

image_logger = construct_logger(file_path="logs/imagetaker.log")
console_log_handler = logging.StreamHandler()
console_log_handler.setLevel(logging.INFO)
console_log_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
image_logger.addHandler(console_log_handler)


class Imagetaker:

    WIDTH_PX, HEIGHT_PX = (2144, 1440)

    PROCESS_ROTATION_ANGLE = 180
    PROCESS_CROP_COORDINATES = (3, 35, 2044, 1440)  # left, top, right, bottom. is a rect, so no need for x, y for every point.

    @staticmethod
    def take_image(process: bool = False, save: bool = False) -> np.ndarray:
        image_logger.info("Taking image.")
        camera = PiCamera()
        camera.resolution = (Imagetaker.WIDTH_PX, Imagetaker.HEIGHT_PX)
        img = np.empty((Imagetaker.HEIGHT_PX, Imagetaker.WIDTH_PX, 3), dtype=np.uint8)
        camera.capture(img, "bgr")
        camera.close()
        if process:
            img = Imagetaker.process_image(img)
        if save:
            assert Imagetaker.save_image(img, "from_camera.jpg"), "An error occured while saving the image."
        image_logger.info("Taking image complete.")
        return img

    @staticmethod
    def save_image(image: np.ndarray, filename: str) -> bool:
        image_logger.info("Saving image.")
        try:
            cv2.imwrite(filename, image)
            image_logger.info("Saving image complete.")
            return True
        except Exception as e:
            image_logger.error(e)
            return False

    @staticmethod
    def load_image(filename: str) -> np.ndarray:
        image_logger.info(f"Loading image: {filename}")
        try:
            return cv2.imread(filename)
        except Exception as e:
            image_logger.error(e)
            return None

    @staticmethod
    def show_image(image: np.ndarray, scale=1.0):
        """Shows a supplied image and waits for a keypress. Will block the rest of the code, so use this for debugging only."""
        cv2.imshow("Imagetaker", resize(image.copy(), int(image.shape[1]*scale)))
        cv2.waitKey(0)

    @staticmethod
    def __convert_from_cv2_to_image(img: np.ndarray) -> Image:
        return Image.fromarray(img)

    @staticmethod
    def __convert_from_image_to_cv2(img: Image) -> np.ndarray:
        return np.asarray(img)

    @staticmethod
    def process_image(orig_image: np.ndarray) -> np.ndarray:
        image_logger.info("Processing image.")
        # rotate, crop, and enhance image. all parameters are subject to change depending on my requirements.
        processed_image = imutils.rotate(orig_image, angle=Imagetaker.PROCESS_ROTATION_ANGLE)
        processed_image = Imagetaker.__convert_from_cv2_to_image(processed_image)
        processed_image = processed_image.crop(Imagetaker.PROCESS_CROP_COORDINATES)
        processed_image = ImageEnhance.Sharpness(processed_image).enhance(1.5)  # i honestly have no idea if this has a big enough effect.
        # process back to numpy array
        processed_image = ImageEnhance.Brightness(processed_image).enhance(1.5)
        img_numpy = Imagetaker.__convert_from_image_to_cv2(processed_image)
        image_logger.info("Processing image complete.")
        return img_numpy
