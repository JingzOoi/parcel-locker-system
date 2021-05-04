from picamera import PiCamera
import numpy as np


class Imagetaker:

    WIDTH_PX, HEIGHT_PX = (2144, 1440)

    @staticmethod
    def take_image():
        camera = PiCamera()
        camera.resolution = (Imagetaker.WIDTH_PX, Imagetaker.HEIGHT_PX)
        # camera.framerate = 30
        # camera.shutter_speed = 6000000
        # camera.iso = 100
        img = np.empty((Imagetaker.HEIGHT_PX, Imagetaker.WIDTH_PX, 3), dtype=np.uint8)
        camera.capture(img, "bgr")
        return img
