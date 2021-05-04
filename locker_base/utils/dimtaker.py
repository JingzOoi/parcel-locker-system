from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import numpy as np
import imutils
import cv2
from PIL import Image, ImageEnhance


class Dimtaker:

    """Dimension taker. Supply with image. Values/parameters are set to suit my needs."""

    PX_PER_METRIC = None
    FILTER_RATIO = 1/4

    PROCESS_ROTATION_ANGLE = 179
    PROCESS_CROP_COORDINATES = (80, 0, 720, 446)  # left, top, right, bottom. is a rect, so no need for x, y for every point.

    def __init__(self, orig_image: np.ndarray, process: bool = False):
        self.image = orig_image if not process else Dimtaker.__process(orig_image)
        self.drawn_image = None  # get_object_dimensions() needs to be run at least once for this to take up a value.
        self.obj_dict = {}

    @classmethod
    def from_path(cls, file_path, process=False):
        return cls(cv2.imread(file_path), process)

    @staticmethod
    def convert_from_cv2_to_image(img: np.ndarray) -> Image:
        return Image.fromarray(img)

    @staticmethod
    def convert_from_image_to_cv2(img: Image) -> np.ndarray:
        return np.asarray(img)

    @staticmethod
    def __process(orig_image: np.ndarray):
        # rotate, crop, and enhance image. all parameters are subject to change depending on my requirements.
        processed_image = imutils.rotate(orig_image, angle=Dimtaker.PROCESS_ROTATION_ANGLE)
        # starting this line, pillow is used. take note to convert array, which cv2 uses, to image file, which is used by pil, and vice versa.
        processed_image = Dimtaker.convert_from_cv2_to_image(processed_image)
        # processed_image = img.rotate(176) <- rotation done on this step looks terrible, for some reason.
        processed_image = processed_image.crop(Dimtaker.PROCESS_CROP_COORDINATES)
        processed_image = ImageEnhance.Sharpness(processed_image).enhance(2)  # i honestly have no idea if this has a big enough effect.
        # process back to numpy array
        img_numpy = Dimtaker.convert_from_image_to_cv2(processed_image)
        # Dimtaker.save_image(img_numpy, "image.jpg")
        return img_numpy

    @staticmethod
    def show_image(image: np.ndarray, scale=1.0):
        """Shows a supplied image and waits for a keypress. Will block the rest of the code, so use this for debugging only."""
        cv2.imshow("Image", imutils.resize(image.copy(), int(image.shape[1]*scale)))
        cv2.waitKey(0)

    @staticmethod
    def save_image(image: np.ndarray, filename: str):
        try:
            cv2.imwrite(filename, image)
            return True
        except:
            return False

    @staticmethod
    def midpoint(point_A, point_B):
        """Calculates the midpoint between two points."""
        return ((point_A[0] + point_B[0]) * 0.5, (point_A[1] + point_B[1]) * 0.5)

    @staticmethod
    def detect_edges(image: np.ndarray):
        edged = cv2.Canny(image, 30, 50)
        edged = cv2.dilate(edged, None, iterations=2)
        edged = cv2.erode(edged, None, iterations=1)
        return edged

    @staticmethod
    def get_height():
        """
        TODO: get the height of the parcel from the ultrasonic sensor.
        Option 1: ping the wirelessly connected ultrasonic sensor node through MQTT. This is considered because I don't have the suitable resistors needed to directly connect the sensor to the Pi. The file needed to flash the ESP is the .yaml file. This may be dangerous, since MQTT may be blocking, and this needs to publish and wait for results. Do not do this if possible.
        Option 2: get the wired ultrasonic sensor to return the height by pinging it directly.
        """

        pass

    def get_object_dimensions(self, reference_width=24, offset=0):
        # TODO: integrate with ultrasonic sensor to get height of object.
        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        edged = cv2.Canny(gray, 30, 50)
        edged = cv2.dilate(edged, None, iterations=2)
        edged = cv2.erode(edged, None, iterations=1)
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        (cnts, _) = contours.sort_contours(cnts)
        cnts = [c for c in cnts if cv2.contourArea(c) > 1500]
        orig = self.image.copy()
        obj_count = 0
        for c in cnts:
            box = cv2.minAreaRect(c)
            box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
            box = np.array(box, dtype="int")
            box = perspective.order_points(box)
            (tl, tr, br, bl) = box
            (tltrX, tltrY) = Dimtaker.midpoint(tl, tr)
            (blbrX, blbrY) = Dimtaker.midpoint(bl, br)
            (tlblX, tlblY) = Dimtaker.midpoint(tl, bl)
            (trbrX, trbrY) = Dimtaker.midpoint(tr, br)
            dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
            dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))
            if dA/dB > Dimtaker.FILTER_RATIO and dB/dA > Dimtaker.FILTER_RATIO:
                for (x, y) in box:
                    cv2.circle(orig, (int(x), int(y)), 5, (0, 0, 255), -1)
                cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)
                # if the pixels per metric has not been initialized, then
                # compute it as the ratio of pixels to supplied metric
                # (in this case, mm)
                if Dimtaker.PX_PER_METRIC is None:
                    Dimtaker.PX_PER_METRIC = dB / reference_width

                # compute the size of the object
                dimA = dA / Dimtaker.PX_PER_METRIC
                dimB = dB / Dimtaker.PX_PER_METRIC

                mp = Dimtaker.midpoint((tltrX, tltrY), (blbrX, blbrY))

                # draw the object sizes on the image
                cv2.putText(orig, f"{dimB:.1f}mm", (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                cv2.putText(orig, f"{dimA:.1f}mm", (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                if obj_count:
                    cv2.putText(orig, f"{obj_count}", (int(mp[0]), int(mp[1])), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 3)
                    self.obj_dict[obj_count] = {"width": dimB, "length": dimA}
            obj_count += 1

        self.drawn_image = orig
        return self.obj_dict


if __name__ == "__main__":
    dimtaker = Dimtaker.from_path("resources/image2.jpg", process=True)
    print(dimtaker.get_object_dimensions())
    Dimtaker.show_image(dimtaker.drawn_image)
