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


class PartialObject:
    """
    A representation of an object seen by the camera through edge processing.

    This class is a collection of attributes and methods that is used to determine certain things about the objects in the image, and takes advantage of certain built-in methods provided by Python for easy readibility.
    Expect to see calculations based on points on an image.
    """

    FILTER_RATIO = 1/4

    def __init__(self, contour: np.ndarray):
        """
        When initialized, four points of the box are supplied. Each of the parameters should be an array with 2 items, value for x-pos and y-pos.
        """
        self.contour_area = cv2.contourArea(contour)

        box = cv2.minAreaRect(contour)
        box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
        box = np.array(box, dtype="int")
        self.box = perspective.order_points(box)

        (top_left, top_right, bottom_right, bottom_left) = self.box
        self.box_tuple = (top_left, top_right, bottom_right, bottom_left)
        upper_midpoint = PartialObject.midpoint(top_left, top_right)
        bottom_midpoint = PartialObject.midpoint(bottom_left, bottom_right)
        left_midpoint = PartialObject.midpoint(top_left, bottom_left)
        right_midpoint = PartialObject.midpoint(top_right, bottom_right)
        self.pixel_length = dist.euclidean(upper_midpoint, bottom_midpoint)
        self.pixel_width = dist.euclidean(left_midpoint, right_midpoint)

        self.actual_length = None
        self.actual_width = None

    @staticmethod
    def midpoint(point_A, point_B):
        """Calculates the midpoint between two points."""
        return ((point_A[0] + point_B[0]) * 0.5, (point_A[1] + point_B[1]) * 0.5)

    @staticmethod
    def scale_to_distance(p_length_to_measure, dist, p_length_of_reference, full_dist, a_length_of_reference):
        """Calculate the actual length based on the depth of field. See white paper for calculation."""
        return ((p_length_to_measure*dist)/(p_length_of_reference*full_dist))*a_length_of_reference

    @staticmethod
    def scale_to_reference(p_length_to_measure, p_length_of_reference, a_length_of_reference):
        """Calculate the actual length based on the ratio of actual length vs pixel length."""
        return ((p_length_to_measure)/(p_length_of_reference))*a_length_of_reference

    def draw(self, img, label=True):
        cv2.drawContours(img, [self.box.astype("int")], -1, (0, 255, 0), 2)
        if label:
            assert self.actual_length and self.actual_width, "Actual length or actual width of object is not calculated!"
            upper = PartialObject.midpoint(self.box_tuple[0], self.box_tuple[1])
            righter = PartialObject.midpoint(self.box_tuple[1], self.box_tuple[2])
            upper_offset = (int(upper[0]), int(upper[1]-15))
            righter_offset = (int(righter[0]+15), int(righter[1]))
            cv2.putText(img, f"{self.actual_width:.1f}mm", upper_offset, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(img, f"{self.actual_length:.1f}mm", righter_offset, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)


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
    def detect_edges(image: np.ndarray):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        edged = cv2.Canny(gray, 25, 50)
        edged = cv2.dilate(edged, None, iterations=2)
        edged = cv2.erode(edged, None, iterations=1)
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        (cnts, _) = contours.sort_contours(cnts)
        return cnts

    @classmethod
    def init_height_sensor(cls):
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(Dimtaker.DISTANCE_TRIG_PIN, GPIO.OUT)
        GPIO.setup(Dimtaker.DISTANCE_ECHO_PIN, GPIO.IN)
        if not cls.DISTANCE_FULL:
            cls.DISTANCE_FULL = cls.take_distance()

    @staticmethod
    def take_distance(init: bool = False):
        if init:
            GPIO.cleanup()
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(Dimtaker.DISTANCE_TRIG_PIN, GPIO.OUT)
            GPIO.setup(Dimtaker.DISTANCE_ECHO_PIN, GPIO.IN)
            GPIO.output(Dimtaker.DISTANCE_TRIG_PIN, True)
        sleep(0.00001)
        GPIO.output(Dimtaker.DISTANCE_TRIG_PIN, False)
        while not GPIO.input(Dimtaker.DISTANCE_ECHO_PIN):
            start = time()
        while GPIO.input(Dimtaker.DISTANCE_ECHO_PIN):
            end = time()

        sig_time = end-start

        distance = sig_time / 0.0000058  # mm

        return distance

    @staticmethod
    def take_dimension_scale(img, full_distance=300, draw=False):
        cnts = Dimtaker.detect_edges(img)
        po_list = [PartialObject(c) for c in cnts]
        # assumes the partial object on the top left corner is always going to be the fiducial.
        fiducial = po_list.pop(0)
        fiducial.actual_length = 24
        fiducial.actual_width = 24
        # uses a "greedy" filter to get the largest object in the partial object list, ignoring any other stuff such as reflections. if the camera is properly calibrated, this approach shouldn't cause any problems.
        parcel = sorted(po_list, key=lambda po: po.contour_area, reverse=True)[0]
        height = Dimtaker.take_distance(init=True)
        parcel.actual_length = parcel.scale_to_distance(
            parcel.pixel_length,
            height,
            fiducial.pixel_length,
            full_distance,
            fiducial.actual_length
        )
        parcel.actual_width = parcel.scale_to_distance(
            parcel.pixel_width,
            height,
            fiducial.pixel_width,
            full_distance,
            fiducial.actual_width
        )
        a_height = full_distance - height
        if draw:
            img_copy = img.copy()
            parcel.draw(img_copy)
            Imagetaker.save_image(img_copy, "dimension_scale.jpg")
        return {"length": parcel.actual_length, "width": parcel.actual_width, "height": a_height}

    @staticmethod
    def take_dimension_ratio(img, full_distance=300, draw=False):
        cnts = Dimtaker.detect_edges(img)
        po_list = [PartialObject(c) for c in cnts]
        fiducial = po_list.pop(0)
        fiducial.actual_length = 24
        fiducial.actual_width = 24
        parcel = sorted(po_list, key=lambda po: po.contour_area, reverse=True)[0]
        parcel.actual_length = parcel.scale_to_reference(parcel.pixel_length, fiducial.pixel_length, fiducial.actual_length)
        parcel.actual_width = parcel.scale_to_reference(parcel.pixel_width, fiducial.pixel_width, fiducial.actual_width)
        if draw:
            img_copy = img.copy()
            parcel.draw(img_copy)
            Imagetaker.save_image(img_copy, "dimension_ratio.jpg")
        height = Dimtaker.take_distance(init=True)
        a_height = full_distance - height
        return {"length": parcel.actual_length, "width": parcel.actual_width, "height": a_height}


if __name__ == "__main__":
    print(Dimtaker.take_object_dimensions(Imagetaker.load_image("from_camera.jpg")))
    # Dimtaker.save_image(dimtaker.drawn_image, "test.jpg")
