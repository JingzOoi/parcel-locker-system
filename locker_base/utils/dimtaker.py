from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import numpy as np
import imutils
import cv2


class Dimtaker:

    """Dimension taker. Supply with image."""

    PX_PER_METRIC = None
    FILTER_RATIO = 1/4

    def __init__(self, orig_image, process=False):
        self.image = orig_image if not process else Dimtaker.__process(orig_image)
        self.drawn_image = None
        self.obj_dict = {}

    @classmethod
    def from_path(cls, file_path, process=False):
        return cls(cv2.imread(file_path), process)

    @staticmethod
    def __process(orig_image):
        # TODO: process images (rotate, sharpen, trim)
        return orig_image

    @staticmethod
    def show_image(image, scale=1.0):
        """Shows a supplied image and waits for a keypress. Will block the rest of the code, so use this for debugging only."""
        cv2.imshow("Image", imutils.resize(image.copy(), int(image.shape[1]*scale)))
        cv2.waitKey(0)

    @staticmethod
    def midpoint(point_A, point_B):
        """Calculates the midpoint between two points."""
        return ((point_A[0] + point_B[0]) * 0.5, (point_A[1] + point_B[1]) * 0.5)

    @staticmethod
    def detect_edges(image):
        edged = cv2.Canny(image, 30, 50)
        edged = cv2.dilate(edged, None, iterations=2)
        edged = cv2.erode(edged, None, iterations=1)
        return edged

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
    dimtaker = Dimtaker.from_path("images/image_edited.jpg")
    obj_dict = dimtaker.get_object_dimensions()
