import logging
from utils.construct import construct_logger
from cv2 import QRCodeDetector
from .imagetaker import Imagetaker

qr_logger = construct_logger(file_path="logs/qrtaker.log")
console_log_handler = logging.StreamHandler()
console_log_handler.setLevel(logging.INFO)
console_log_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
qr_logger.addHandler(console_log_handler)


class QRtaker:
    @staticmethod
    def take_qr(img):
        qr_logger.info("Reading QR information from image.")
        detector = QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)
        if bbox is not None:
            qr_logger.info(f"Obtained data: {data}")
            return data
        else:
            qr_logger.warning("No QR code was found from the image.")
            return None


if __name__ == "__main__":
    print(QRtaker.take_qr(Imagetaker.take_image()))
