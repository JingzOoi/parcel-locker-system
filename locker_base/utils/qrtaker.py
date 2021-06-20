from cv2 import QRCodeDetector, imread
import cv2
from .imagetaker import Imagetaker


class QRtaker:
    @staticmethod
    def take_qr(img):
        detector = QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)
        return data if bbox is not None else None


if __name__ == "__main__":
    print(QRtaker.take_qr(Imagetaker.take_image()))
