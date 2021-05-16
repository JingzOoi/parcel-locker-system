from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import numpy as np
import imutils
import cv2
from PIL import Image, ImageEnhance
import RPi.GPIO as GPIO
from time import time, sleep
from .imagetaker import Imagetaker


class Dimtaker:

    """Dimension taker. Supply with image. Values/parameters are set to suit my needs."""

    PX_PER_METRIC = None
    FILTER_RATIO = 1/4
    REFERENCE_WIDTH = 24  # mm

    DISTANCE_FULL = None  # mm
    DISTANCE_TRIG_PIN = 4
    DISTANCE_ECHO_PIN = 18

    @classmethod
    def from_path(cls, file_path, process=False):
        return cls(cv2.imread(file_path), process)

    @classmethod
    def from_camera(cls, process=False):
        img = Imagetaker.take_image()
        return cls(img, process)

    @staticmethod
    def midpoint(point_A, point_B):
        """Calculates the midpoint between two points."""
        return ((point_A[0] + point_B[0]) * 0.5, (point_A[1] + point_B[1]) * 0.5)

    @staticmethod
    def _midpoint_check(point, box):
        """Checks if the midpoint of an object is in a box. Box parameter is a tuple with array values with length 2. tuple length 4: tl, tr, bl, br"""
        point_x, point_y = point
        tl, tr, bl, br = box

        more_than_x = sum([tl[0], bl[0]])/2
        less_than_x = sum([tr[0], br[0]])/2
        more_than_y = sum([tl[1], tr[1]])/2
        less_than_y = sum([bl[1], br[1]])/2
        if point_x >= more_than_x and point_x <= less_than_x and point_y >= more_than_y and point_y <= less_than_y:
            return False
        return True

    @staticmethod
    def detect_edges(image: np.ndarray):
        edged = cv2.Canny(image, 25, 50)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)
        return edged

    @classmethod
    def init_height_sensor(cls):
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(Dimtaker.DISTANCE_TRIG_PIN, GPIO.OUT)
        GPIO.setup(Dimtaker.DISTANCE_ECHO_PIN, GPIO.IN)
        if not cls.DISTANCE_FULL:
            cls.DISTANCE_FULL = cls.take_height()

    @staticmethod
    def take_height():
        GPIO.output(Dimtaker.DISTANCE_TRIG_PIN, True)
        sleep(0.00001)
        GPIO.output(Dimtaker.DISTANCE_TRIG_PIN, False)
        while not GPIO.input(Dimtaker.DISTANCE_ECHO_PIN):
            start = time()
        while GPIO.input(Dimtaker.DISTANCE_ECHO_PIN):
            end = time()

        sig_time = end-start

        distance = sig_time / 0.0000058  # mm

        return (Dimtaker.DISTANCE_FULL - distance) if Dimtaker.DISTANCE_FULL else distance

    @staticmethod
    def __calculate_length_based_on_depth(p1, h1, p0, h0, l0):
        """
        returns l1 from all the parameters given. Refer to white paper. I know this is a superficial function. Don't @ me.
        l0: the actual length of the side to measure on the parcel.
        p1: the pixel distance of the side to measure on the parcel.
        h1: the distance from the sensor to the top of the parcel.
        p0: the pixel distance of the side to measure on the fiducial.
        h0: the distance from the sensor to the platform surface.
        l0: the actual length of the side to measure on the fiducial.
        """
        return (p1*h1*l0)/(p0*h0)

    @staticmethod
    def take_object_dimensions(image: np.ndarray, reference_width=None, save: bool = False, height=True):
        # TODO: integrate with ultrasonic sensor to get height of object.
        obj_dict = {}
        reference_width = Dimtaker.REFERENCE_WIDTH if reference_width is None else reference_width
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        edged = cv2.Canny(gray, 25, 50)
        edged = cv2.dilate(edged, None, iterations=2)
        edged = cv2.erode(edged, None, iterations=1)
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        (cnts, _) = contours.sort_contours(cnts)
        cnts = [c for c in cnts if cv2.contourArea(c) > 1500]
        orig = image.copy()
        ref_fiducial = {"awidth": 0, "pwidth": reference_width}
        for num, c in enumerate(cnts):
            box = cv2.minAreaRect(c)
            box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
            box = np.array(box, dtype="int")
            box = perspective.order_points(box)
            (tl, tr, br, bl) = box
            (tltrX, tltrY) = Dimtaker.midpoint(tl, tr)
            (blbrX, blbrY) = Dimtaker.midpoint(bl, br)
            (tlblX, tlblY) = Dimtaker.midpoint(tl, bl)
            (trbrX, trbrY) = Dimtaker.midpoint(tr, br)
            length = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))  # calculates distance between two points
            width = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))
            if length/width > Dimtaker.FILTER_RATIO and width/length > Dimtaker.FILTER_RATIO:
                for (x, y) in box:
                    cv2.circle(orig, (int(x), int(y)), 5, (0, 0, 255), -1)
                cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)
                # if the pixels per metric has not been initialized, then
                # compute it as the ratio of pixels to supplied metric
                # (in this case, mm)
                if not Dimtaker.PX_PER_METRIC:
                    Dimtaker.PX_PER_METRIC = width / reference_width

                if not ref_fiducial["width"]:
                    ref_fiducial["width"] = width

                # compute the size of the object
                dimA = length / Dimtaker.PX_PER_METRIC
                dimB = width / Dimtaker.PX_PER_METRIC

                mp = Dimtaker.midpoint((tltrX, tltrY), (blbrX, blbrY))

                # draw the object sizes on the image
                cv2.putText(orig, f"{dimB:.1f}mm", (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(orig, f"{dimA:.1f}mm", (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                if num:
                    cv2.putText(orig, f"{num}", (int(mp[0]), int(mp[1])), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 5)
                    num = {"width": dimB, "length": dimA}
                if save:
                    Imagetaker.save_image(orig, "Dimtaker_take_object_dimensions.jpg")

        if len(obj_dict) >= 1 and height:
            obj_dict["height"] = Dimtaker.take_height()
        return obj_dict


if __name__ == "__main__":
    print(Dimtaker.take_object_dimensions(Imagetaker.load_image("from_camera.jpg")))
    # Dimtaker.save_image(dimtaker.drawn_image, "test.jpg")
