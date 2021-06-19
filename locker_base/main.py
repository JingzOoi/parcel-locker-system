from utils.dimtaker import Dimtaker
from utils.qrtaker import QRtaker
from utils.imagetaker import Imagetaker
from utils.jsonIO import jsonIO
from utils.construct import construct_logger, construct_handler
from time import sleep
import requests
import logging


# on startup


CONFIG = jsonIO.load("config/config.json")["meta"]

LOGGER = logging.getLogger("locker_base")
LOGGER.setLevel(logging.INFO)

for hdlr in list(LOGGER.handlers):
    print(hdlr)
    LOGGER.removeHandler(hdlr)


LOGGER.addHandler(construct_handler(file_path="logs/info.log"))
LOGGER.addHandler(construct_handler(file_path="logs/error.log", level=logging.ERROR))

LOGGER.info("Starting up...")

# calibrate

LOGGER.info("Initializing height sensor...")
Dimtaker.DISTANCE_FULL = Dimtaker.take_distance(init=True)
LOGGER.info(f"Initializing height sensor done: {Dimtaker.DISTANCE_FULL:.4f}")
starting_url = f"{CONFIG['webserver_address']}/api/locker/{CONFIG['_id']}"
LOGGER.info(f"[Initializing webserver address: {starting_url}")
with requests.get(f"{starting_url}/0/activity/add/1") as page:
    if page.status_code == 200:
        LOGGER.info("Submitted online query.")
    else:
        LOGGER.info(f"Webserver returned {page.status_code}.")


# go into infinite loop trying to detect a height change
# i'll add a user interface if i have time to, use pygame or something idk


while True:
    try:
        distance = Dimtaker.take_distance(init=True)
        if distance <= Dimtaker.DISTANCE_FULL*0.8:
            grace_time = 5
            LOGGER.info(f"Object detected with distance {distance:2f}")

            print(f"[MAIN] Object detected. Giving {grace_time} seconds of grace time.")
            sleep(grace_time)
            print("[MAIN] Taking QR information...")
            img = Imagetaker.take_image(process=True, save=True)
            qr = QRtaker.take_qr(img)
            if qr:
                # TODO: determine if format matches the recipient qr
                if str(qr).startswith("parlock_"):
                    # if yes, make a POST request to the server to get recipient information using collection id and self id.
                    pass
                # then if successfully verified that the recipient does have a parcel that is being deposited in this locker, receive information about which one. unlock said locker.
                # wait for button press and lock.
                # if no, make a POST request to the webserver to get parcel information using tracking number.
                else:
                    print(f"Querying the server for parcel with tracking number {qr}...")
                    page = requests.get(f"{starting_url}/parcel/query", params={"tn": qr})
                    if page.status_code == 200:
                        print(page.json())
                        print(f"[MAIN] Taking object dimensions...")
                        print(Dimtaker.take_dimension_scale(img, full_distance=Dimtaker.DISTANCE_FULL))
                    else:
                        print("Parcel not found!")
                # if verified that this locker is the one that the parcel is supposed to be delivered to, measure dimensions.
                # for available lockers in the list, run through the dimension comparing algorithm.
                # if none of the lockers are suitable, quit.
                # else, send unlock command.
                # wait for button press
                # send lock command.
                # of course, report to the webserver.
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
    except Exception as e:
        LOGGER.error(e)
