from utils.construct import construct_logger
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
from statistics import median
import logging

dim_logger = construct_logger(file_path="logs/dimtaker.log")
console_log_handler = logging.StreamHandler()
console_log_handler.setLevel(logging.INFO)
console_log_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
dim_logger.addHandler(console_log_handler)


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
    def take_distance() -> float:
        """
        Just takes the distance between the sensor and the closest object. Calculate height of object separately.
        """
        def init_and_measure(init: bool = True):
            if init:
                GPIO.setwarnings(False)
                GPIO.cleanup()
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(Dimtaker.DISTANCE_TRIG_PIN, GPIO.OUT)
                GPIO.setup(Dimtaker.DISTANCE_ECHO_PIN, GPIO.IN)
                GPIO.output(Dimtaker.DISTANCE_TRIG_PIN, False)
                sleep(1)

            GPIO.output(Dimtaker.DISTANCE_TRIG_PIN, False)
            GPIO.output(Dimtaker.DISTANCE_TRIG_PIN, True)
            sleep(0.00001)
            GPIO.output(Dimtaker.DISTANCE_TRIG_PIN, False)
            start = time()
            end = time()

            loop_count = 0
            while not GPIO.input(Dimtaker.DISTANCE_ECHO_PIN):
                start = time()
                if loop_count >= 240000:
                    return None
                loop_count += 1
            while GPIO.input(Dimtaker.DISTANCE_ECHO_PIN):
                end = time()

            sig_time = end-start
            distance = sig_time * 171500  # mm
            return round(distance, 4)

        dim_logger.info("Starting measuring distance attempt.")
        distance_list = []
        for i in range(1, 15):
            dim_logger.info(f"Measuring distance: attempt {i}. Latest: {distance_list[-1] if distance_list else None}")
            dist = init_and_measure(init=True)
            if dist:
                distance_list.append(dist)
        m = median(distance_list)
        dim_logger.info(f"Measuring distance complete, got median of {m}")
        return m

    @staticmethod
    def take_dimension_scale(img, full_distance=300, height_override: int = None, draw=False):
        """New algorithm that takes depth-of-view into consideration."""
        dim_logger.info("Taking dimensions of the scanning platform.")
        cnts = Dimtaker.detect_edges(img)
        po_list = [PartialObject(c) for c in cnts]
        # assumes the partial object on the top left corner is always going to be the fiducial.
        fiducial = po_list.pop(0)
        fiducial.actual_length = 24
        fiducial.actual_width = 24
        # uses a "greedy" filter to get the largest object in the partial object list, ignoring any other stuff such as reflections. if the camera is properly calibrated, this approach shouldn't cause any problems.
        parcel = sorted(po_list, key=lambda po: po.contour_area, reverse=True)[0]
        height = Dimtaker.take_distance() if not height_override else height_override

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
            fiducial.draw(img_copy)
            parcel.draw(img_copy)
            Imagetaker.save_image(img_copy, "dimension_scale.jpg")
        result = {"length": round(parcel.actual_length, 4), "width": round(parcel.actual_width, 4), "height": round(a_height, 4)}
        dim_logger.info(f"Taking dimensions of the scanning platform complete. Results: {result}")
        return result

    @staticmethod
    def take_dimension_ratio(img, full_distance=300, draw=False):
        """Uses the original algorithm."""
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
        height = Dimtaker.take_distance()
        a_height = full_distance - height
        return {"length": parcel.actual_length, "width": parcel.actual_width, "height": a_height}

    @staticmethod
    def test_fit(object_1: dict, object_2: dict) -> bool:
        """
        Can an object fit into another object?
        In theory, there are 4 unique orientations for a cuboid. 
        Object 1 is the parcel, object 2 is the locker unit.
        This part works by test fitting all the orientations of the parcel one by one. If any of the orientations are smaller than the dimensions of the locker unit, then the system determines it to fit. make the offset to be ~-10%.
        This uses a stupidly rudimentary approach that does not depend on actual 3D imaging.

        @param object_1 = dictionary that has 3 key-value pairs: length, width, and height.
        """
        dim_logger.info("Starting test fit attempt.")
        is_fit = False
        locker_length, locker_width, locker_height = object_2["length"]*.85, object_2["width"]*.85, object_2["height"]*.85
        # first of all, determine if length = length, width = width, height = height
        if object_1["length"] < locker_length and object_1["width"] < locker_width and object_1["height"] < locker_height:
            is_fit = True
        elif object_1["width"] < locker_length and object_1["length"] < locker_width and object_1["height"] < locker_height:
            is_fit = True
        elif object_1["height"] < locker_length and object_1["width"] < locker_width and object_1["length"] < locker_height:
            is_fit = True
        elif object_1["height"] < locker_length and object_1["length"] < locker_width and object_1["width"] < locker_height:
            is_fit = True
        dim_logger.info(f"Test fit attempts returned {is_fit}.")
        return is_fit
