import unittest

from utils.dimtaker import Dimtaker
from utils.imagetaker import Imagetaker
from utils.qrtaker import QRtaker


class LockerBaseTestCase(unittest.TestCase):
    def test_qr(self):
        img = Imagetaker.take_image(process=True, save=True)
        data = QRtaker.take_qr(img)
        self.assertEqual(data, "")

    def test_dim(self):
        Dimtaker.DISTANCE_FULL = 279
        img = Imagetaker.take_image(process=True, save=True)
        dim = Dimtaker.take_dimension_scale(img=img, full_distance=Dimtaker.DISTANCE_FULL, draw=True)
        actual = {
            "length": 105,
            "width": 150,
            "height": 80
        }
        self.assertAlmostEqual(dim["length"], actual["length"], places=1)

    def test_height(self):
        distance_full = Dimtaker.take_distance()
        self.assertIsNotNone(distance_full)


if __name__ == "__main__":
    unittest.main()
