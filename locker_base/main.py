from time import sleep
from utils.qrtaker import QRtaker
from utils.imagetaker import Imagetaker
from utils.dimtaker import Dimtaker
from utils.jsonIO import jsonIO
from utils.construct import construct_handler
import requests
import logging
import json
import paho.mqtt.client as mqtt


class LockerUnit:

    """Logical representation of a locker unit."""

    def __init__(self, _id):
        self.id = _id
        self.is_available = True
        self.length = None
        self.width = None
        self.height = None

    def __eq__(self, other):
        return self.id == other.id

    def dimensions(self) -> dict:
        return {
            "length": self.length,
            "width": self.width,
            "height": self.height
        }

    def __repr__(self) -> str:
        return f"LockerUnit(id={self.id}, is_available={self.is_available}, length={self.length}, width={self.width}, height={self.height})"


class LockerBase:

    """
    Logical representation of a locker base. 
    Is initialized once during the execution of this file, data persisting till death.
    """

    class ActivityType:
        # follows the webserver configuration.
        ONLINE = "online"
        OFFLINE = "offline"
        REGISTER = "register"
        SCANQRRECIPIENT = "withdraw-qr"
        SCANQRPARCEL = "parcel"
        SCANDIM = "scandim"
        DEPOSIT = "deposit"  # note: these needs complete param
        WITHDRAW = "withdraw"  # note: these needs complete param
        CHANGE_V_CODE = "change"

    class UnitCommand:
        QUERY_BASE = "locker_unit/query"
        REPLY_BASE = "locker_unit/reply"
        QUERY_REGISTER = f"{QUERY_BASE}/register"
        REPLY_REGISTER = f"{REPLY_BASE}/register"
        QUERY_LOCK = f"{QUERY_BASE}/lock"
        REPLY_LOCK = f"{REPLY_BASE}/lock"
        QUERY_UNLOCK = f"{QUERY_BASE}/unlock"
        REPLY_UNLOCK = f"{REPLY_BASE}/unlock"

    def __init__(self, conf: dict):
        self.CONFIG = conf
        self.id = self.CONFIG["id"]
        self.verification_code = self.CONFIG["verification_code"]
        self.webserver_address = self.CONFIG["webserver_address"]

        self.locker_units = []

        self.logger = logging.getLogger("locker_base")
        self.logger.setLevel(logging.INFO)
        for hdlr in list(self.logger.handlers):
            print(hdlr)
            self.logger.removeHandler(hdlr)
        self.logger.addHandler(construct_handler(file_path="logs/info.log", level=logging.INFO))
        self.logger.addHandler(construct_handler(file_path="logs/error.log", level=logging.ERROR))

        console_log_handler = logging.StreamHandler()
        console_log_handler.setLevel(logging.INFO)
        console_log_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(console_log_handler)

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
        """Overwrite config file with current config. Usually done after verification code has been changed."""
        self.logger.info("Writing current config to config/config.json.")
        if jsonIO.save("config/config.json", self.export_config()):
            self.logger.info("Exporting config successful.")
        else:
            self.logger.error("An error has occured while exporting config.")

    def send_mqtt_command(self, *, locker_unit: LockerUnit = None, command: str):
        """Publishes MQTT commands. If a locker unit is provided, then the command is sent while specifying a locker unit."""
        if locker_unit and locker_unit in self.locker_units and command.startswith(LockerBase.UnitCommand.QUERY_BASE):
            self.logger.info(f"Sending command {command} to locker unit with id {locker_unit.id}.")
            self.mqtt_client.publish(topic=f"{command}/{locker_unit.id}", payload=None, qos=0)
        elif not locker_unit and command.startswith(LockerBase.UnitCommand.QUERY_BASE):
            self.logger.info(f"Broadcasting command {command} to all locker units in the vicinity.")
            self.mqtt_client.publish(topic=f"{command}", payload=None, qos=0)

    def contact_webserver(self, *, activity_type: str, params: dict = {}):
        """Responsible for contacting the webserver. The activity type is based on the inner class ActivityType."""
        url = f"{self.webserver_address}/api/locker/{self.id}/{activity_type}/"
        params = {"verification_code": self.verification_code, **params}  # v code is needed for every request sent to the webserver.
        self.logger.info(f"Contacting webserver at endpoint /{activity_type}. Data: {json.dumps(params)}")
        with self.session.post(url, data=params) as page:
            if page.status_code == 200:
                self.logger.info(f"Webserver returned status code {page.status_code}.")
                return page.json()
            else:
                self.logger.error(f"Webserver returned status code {page.status_code}.")
                return None

    def init_mqtt(self):
        """This function is called during the initialization of the LockerBase object to set up the MQTT listener."""

        self.logger.info("Initializing MQTT handler.")

        def on_connect(client, userdata, flags, rc):
            # this is a function to be assigned to mqtt.client, replacing the original function.
            # sets the conditions to connect to the mqtt broker.
            client.subscribe(f"{LockerBase.UnitCommand.REPLY_BASE}/#")
            self.logger.info(f"Subscribed to topic {LockerBase.UnitCommand.REPLY_BASE}/#.")

        def on_message(client, userdata, msg):
            # this is a function to be assigned to mqtt.client, replacing the original function.
            # parsing of the MQTT messages happen here.
            payload = json.loads(msg.payload)
            self.logger.info(f"Received MQTT message: {payload} from topic {msg.topic}.")
            locker_unit = LockerUnit(payload["id"])
            if msg.topic.startswith(LockerBase.UnitCommand.REPLY_REGISTER):
                self.logger.info(f"Attempting to add locker unit with ID {payload['id']} into the range.")
                if locker_unit not in self.locker_units:
                    resp = self.contact_webserver(activity_type=LockerBase.ActivityType.REGISTER, params={"unit_id": locker_unit.id})
                    if resp and resp["success"]:
                        locker_unit.length = float(resp["length"])
                        locker_unit.width = float(resp["width"])
                        locker_unit.height = float(resp["height"])
                        locker_unit.is_available = resp["is_available"]
                        self.locker_units.append(locker_unit)
                        self.logger.info(f"Added {repr(locker_unit)} into the range.")

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        self.logger.info("MQTT handler initialization complete.")
        return client


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

# reports to webserver about online status
base.contact_webserver(activity_type=LockerBase.ActivityType.ONLINE)
# queries for available locker units
base.send_mqtt_command(command=LockerBase.UnitCommand.QUERY_REGISTER)


while True:

    base.logger.info("Starting new scanning process.")
    dist = Dimtaker.take_distance()
    base.logger.info(f"Got distance: {dist:.4f}.")
    # process starts when closest object is 85% of the full distance
    if dist < Dimtaker.DISTANCE_FULL*0.85:
        base.logger.info("Approved, starting image taking process.")
        img = Imagetaker.take_image(process=True, save=True)
        base.logger.info("Taken and processed, taking QR info.")
        data = QRtaker.take_qr(img)
        if data:
            base.logger.info(f"Got QR info of {data}, contacting webserver for info.")
            if data.startswith("withdraw_"):
                # if starts with "withdraw_" = is a generated withdraw qr code
                resp = base.contact_webserver(activity_type=LockerBase.ActivityType.SCANQRRECIPIENT, params={"qr_data": data})
                if resp:
                    unit_id = resp["unit_id"]
                    # find matching units connected to base
                    match_units = list(filter(lambda unit: unit.id == unit_id, base.locker_units))
                    if match_units:
                        match_unit = match_units[0]
                        base.logger.info(f"Found matching locker unit {repr(match_unit)}.")
                        base.send_mqtt_command(locker_unit=match_unit, command=LockerBase.UnitCommand.QUERY_UNLOCK)
                        base.contact_webserver(
                            activity_type=LockerBase.ActivityType.WITHDRAW,
                            params={
                                "qr_data": data,
                                "unit_id": match_unit.id,
                                "complete": False
                            }
                        )
                        # ideally, listen for command from button. listener requires a separate thread (probably) and can't be fit on this main process at the moment. future improvements.
                        sleep(10)
                        base.send_mqtt_command(locker_unit=match_unit, command=LockerBase.UnitCommand.QUERY_LOCK)
                        base.contact_webserver(
                            activity_type=LockerBase.ActivityType.WITHDRAW,
                            params={
                                "qr_data": data,
                                "unit_id": match_unit.id,
                                "complete": True
                            }
                        )
                        match_unit.is_available = True
                        base.logger.info("Withdraw complete.")
                    else:
                        base.logger.error("No matching locker units found!")

            else:
                # if not start with "withdraw_" = probably a parcel qr
                resp = base.contact_webserver(activity_type=LockerBase.ActivityType.SCANQRPARCEL, params={"tracking_number": data})
                if resp:
                    # measure dimension
                    dims = Dimtaker.take_dimension_scale(img, full_distance=Dimtaker.DISTANCE_FULL)
                    base.logger.info(f"Obtained dimensions of parcel: {json.dumps(dims)}")
                    # report to webserver
                    base.contact_webserver(activity_type=LockerBase.ActivityType.SCANDIM, params={"tracking_number": data})
                    # find an empty unit
                    available_lockers = [locker_unit for locker_unit in base.locker_units if locker_unit.is_available]
                    base.logger.info(f"Found {len(available_lockers)} available locker units.")
                    for locker_unit in available_lockers:
                        # do a test fit to see if parcel fits into the unit
                        base.logger.info(f"Testing locker unit {locker_unit.id}.")
                        if Dimtaker.test_fit(dims, locker_unit.dimensions()) is True:
                            # approve on the first successful attempt
                            approved_unit = locker_unit
                            base.logger.info(f"Found suitable locker unit {approved_unit.id}.")
                            break
                    if approved_unit:
                        base.send_mqtt_command(locker_unit=approved_unit, command=LockerBase.UnitCommand.QUERY_UNLOCK)
                        base.contact_webserver(
                            activity_type=LockerBase.ActivityType.DEPOSIT,
                            params={
                                "tracking_number": data,
                                "unit_id": approved_unit.id,
                                "complete": False
                            }
                        )
                        # ideally, listen for command from button. listener requires a separate thread (probably) and can't be fit on this main process at the moment. future improvements.
                        sleep(10)
                        base.send_mqtt_command(locker_unit=approved_unit, command=LockerBase.UnitCommand.QUERY_LOCK)
                        base.contact_webserver(
                            activity_type=LockerBase.ActivityType.DEPOSIT,
                            params={
                                "tracking_number": data,
                                "unit_id": approved_unit.id,
                                "complete": True
                            }
                        )
                        base.logger.info("Deposit complete.")
                    else:
                        base.logger.error("No available locker units found!")

    base.logger.info("Process complete, resetting.")
    sleep(2)
