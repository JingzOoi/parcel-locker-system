from utils.dimtaker import Dimtaker
from utils.qrtaker import QRtaker
from utils.imagetaker import Imagetaker
from time import sleep


# on startup

print(f"[BOOT] Starting up...")

# calibrate

print(f"[BOOT] Initializing height sensor...", end=" ")
Dimtaker.init_height_sensor()
print(f"Done. Height sensor default: {Dimtaker.DISTANCE_FULL}")

# go into infinite loop trying to detect a height change
# i'll add a user interface if i have time to, use pygame or something idk

while True:
    try:
        if Dimtaker.take_height() >= Dimtaker.DISTANCE_FULL/10:
            grace_time = 5
            print(f"[MAIN] Object detected. Giving {grace_time} seconds of grace time.")
            sleep(grace_time)
            print("[MAIN] Taking QR information...")
            img = Imagetaker.take_image(process=True)
            qr = QRtaker.take_qr(img)
            if qr:
                print(f"[MAIN] QR information obtained: {qr}. Taking object dimensions...")
                print(Dimtaker.take_object_dimensions(img))
            else:
                print(f"[MAIN] QR information not found!")
            print("[MAIN] Operation complete. Resetting...")
            sleep(10)
            print("[MAIN] Waiting for next object...")
        sleep(2)
    except KeyboardInterrupt:
        print(f"[EXIT] Shutting down.")
        # TODO: save config if applicable
        exit(0)
