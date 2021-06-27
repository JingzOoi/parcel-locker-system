from utils.dimtaker import Dimtaker
from utils.qrtaker import QRtaker
from utils.imagetaker import Imagetaker
from utils.jsonIO import jsonIO
from utils.construct import construct_logger, construct_handler
from time import sleep
import requests
import logging
import json
import paho.mqtt.client as mqtt


class LockerBase:

    class ActivityType:
        # follows the webserver configuration.
        ONLINE = "online"
        OFFLINE = "offline"
        REGISTER = "register"
        SCANQRRECIPIENT = "withdraw-qr"
        SCANQRPARCEL = "parcel"
        SCANDIM = "scandim"
        UNLOCK = "unlock"
        LOCK = "lock"
        CHANGE_V_CODE = "change"

    class UnitCommand:
        BASE = "locker_unit/query"
        REGISTER = f"{BASE}/register"

    def __init__(self, conf: dict):
        self.CONFIG = conf
        self.id = self.CONFIG["id"]
        self.verification_code = self.CONFIG["verification_code"]
        self.webserver_address = self.CONFIG["webserver_address"]
        self.logger = logging.getLogger("locker_base")
        for hdlr in list(self.logger.handlers):
            print(hdlr)
            self.logger.removeHandler(hdlr)
        self.logger.addHandler(construct_handler(file_path="logs/info.log", level=logging.INFO))
        self.logger.addHandler(construct_handler(file_path="logs/error.log", level=logging.ERROR))
        self.session = requests.Session()
        self.mqtt_client = self.init_mqtt()
        self.mqtt_client.connect(self.CONFIG["mqtt"]["host"])
        self.mqtt_client.loop_start()

    def export_config(self):
        return {
            "id": self.id,
            "verification_code": self.verification_code,
            "webserver_address": self.webserver_address
        }

    def save_config(self):
        self.logger.info("Writing current config to config/config.json.")
        if jsonIO.save("config/config.json", self.export_config()):
            self.logger.info("Exporting config successful.")
        else:
            self.logger.error("An error has occured while exporting config.")

    def send_mqtt_command(self, *, unit_id: int = None, command: str):
        self.logger.info(f"Sending command {command} to locker unit {unit_id}.")
        self.mqtt_client.publish(topic=command, payload=None, qos=0)

    def contact_webserver(self, *, activity_type: str, **kwargs):
        url = f"{self.webserver_address}/api/locker/{self.id}/{activity_type}/"
        params = {"verification_code": self.verification_code, **kwargs}
        self.logger.info(f"Contacting webserver at endpoint /{activity_type}. Data: {json.dumps(params)}")
        with self.session.post(url, data=params) as page:
            if page.status_code == 200:
                self.logger.info(f"Webserver returned status code {page.status_code}.")
                return page.json()
            else:
                self.logger.error(f"Webserver returned status code {page.status_code}.")
                return None

    def init_mqtt(self):
        self.logger.info("Initializing MQTT handler.")

        def on_connect(client, userdata, flags, rc):
            client.subscribe(self.CONFIG["mqtt"]["root_topic"])

        def on_message(client, userdata, msg):
            self.logger.info(f"Received MQTT message: {msg.payload} from topic {msg.topic}")
            print(f"Received MQTT message: {msg.payload} from topic {msg.topic}")

        c = mqtt.Client()
        c.on_connect = on_connect
        c.on_message = on_message
        self.logger.info("MQTT handler initialization complete.")
        return c


# load config
base = LockerBase(jsonIO.load("config/config.json"))
base.logger.info("Finished reading configuration file.")

# calibrate height sensor and full distance
base.logger.info("Calibrating height sensor.")
try:
    Dimtaker.DISTANCE_FULL = Dimtaker.take_distance()
    base.logger.info(f"Calibrating height sensor complete. Full height: {Dimtaker.DISTANCE_FULL:.4f}")
except Exception as e:
    base.logger.error(e)


# base.contact_webserver(activity_type=LockerBase.ActivityType.ONLINE)
base.send_mqtt_command(command=LockerBase.UnitCommand.REGISTER)

for i in range(10):
    sleep(1)


# CONFIG = jsonIO.load("config/config.json")["LockerBase"]


# LOGGER.info("Starting up...")

# # calibrate

# LOGGER.info("Initializing height sensor...")
# Dimtaker.DISTANCE_FULL = Dimtaker.take_distance(init=True)
# LOGGER.info(f"Initializing height sensor done: {Dimtaker.DISTANCE_FULL:.4f}")

# # initialize and inform webserver that the device is online

# # read from config
# starting_url = f"{CONFIG['webserver_address']}/api/locker/{CONFIG['_id']}"
# LOGGER.info(f"[Initializing webserver address: {starting_url}")
# with requests.get(f"{starting_url}/0/activity/add/1") as page:
#     if page.status_code == 200:
#         LOGGER.info("Submitted online query.")
#     else:
#         LOGGER.info(f"Webserver returned {page.status_code}.")


# # go into infinite loop trying to detect a height change
# # i'll add a user interface if i have time to, use pygame or something idk


# while True:
#     try:
#         distance = Dimtaker.take_distance(init=True)
#         if distance <= Dimtaker.DISTANCE_FULL*0.8:
#             grace_time = 5
#             LOGGER.info(f"Object detected with distance {distance:2f}")

#             print(f"[MAIN] Object detected. Giving {grace_time} seconds of grace time.")
#             sleep(grace_time)
#             print("[MAIN] Taking QR information...")
#             img = Imagetaker.take_image(process=True, save=True)
#             qr = QRtaker.take_qr(img)
#             if qr:
#                 # TODO: determine if format matches the recipient qr
#                 if str(qr).startswith("parlock_"):
#                     # if yes, make a POST request to the server to get recipient information using collection id and self id.
#                     pass
#                 # then if successfully verified that the recipient does have a parcel that is being deposited in this locker, receive information about which one. unlock said locker.
#                 # wait for button press and lock.
#                 # if no, make a POST request to the webserver to get parcel information using tracking number.
#                 else:
#                     print(f"Querying the server for parcel with tracking number {qr}...")
#                     page = requests.get(f"{starting_url}/parcel/query", params={"tn": qr})
#                     if page.status_code == 200:
#                         print(page.json())
#                         print(f"[MAIN] Taking object dimensions...")
#                         print(Dimtaker.take_dimension_scale(img, full_distance=Dimtaker.DISTANCE_FULL))
#                     else:
#                         print("Parcel not found!")
#                 # if verified that this locker is the one that the parcel is supposed to be delivered to, measure dimensions.
#                 # for available lockers in the list, run through the dimension comparing algorithm.
#                 # if none of the lockers are suitable, quit.
#                 # else, send unlock command.
#                 # wait for button press
#                 # send lock command.
#                 # of course, report to the webserver.
#             else:
#                 print(f"[MAIN] QR information not found!")
#             print("[MAIN] Operation complete. Resetting...")
#             sleep(10)
#             print("[MAIN] Waiting for next object...")
#         sleep(2)
#     except KeyboardInterrupt:
#         print(f"[EXIT] Shutting down.")
#         # TODO: save config if applicable
#         exit(0)
#     except Exception as e:
#         LOGGER.error(e)
