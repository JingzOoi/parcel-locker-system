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

    def __eq__(self, other):
        return self.id == other.id


class LockerBase:

    """
    Logical representation of a locker base. Is initialized once during the execution of this file, data persisting till death.
    """

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

    def contact_webserver(self, *, activity_type: str, **kwargs):
        """Responsible for contacting the webserver. The activity type is based on the inner class ActivityType."""
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
            if msg.topic == LockerBase.UnitCommand.REPLY_REGISTER:
                self.logger.info(f"Attempting to add locker unit with ID {payload['id']} into the range.")
                if locker_unit not in self.locker_units:
                    # TODO: query the webserver for the dimensions of the locker unit. set the dimensions as the attributes of the locker_unit object before adding it into self.locker_units.
                    self.locker_units.append(locker_unit)
                    self.logger.info(f"Added locker unit (ID: {locker_unit.id}) into the range.")

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        self.logger.info("MQTT handler initialization complete.")
        return client


# load config
base = LockerBase(jsonIO.load("config/config.json"))
base.logger.info("Finished reading configuration file.")

# calibrate height sensor and full distance
# base.logger.info("Calibrating height sensor.")
# try:
#     Dimtaker.DISTANCE_FULL = Dimtaker.take_distance()
#     base.logger.info(f"Calibrating height sensor complete. Full height: {Dimtaker.DISTANCE_FULL:.4f}")
# except Exception as e:
#     base.logger.error(e)


# base.contact_webserver(activity_type=LockerBase.ActivityType.ONLINE)
base.send_mqtt_command(command=LockerBase.UnitCommand.QUERY_REGISTER)


while True:

    # measure distance
    # if less than 80% then start process and stuff.

    pass
