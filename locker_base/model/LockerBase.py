from os.path import join
from typing import Iterable
from utils.jsonIO import jsonIO
from utils.construct import construct_path
from inspect import getmembers


class LockerBase:
    """
    One locker has one locker base. (Locker only exists if locker base exists) One locker base can have many locker units.
    Main roles include:
    - Scan parcel QR code
    - Verify parcel identity
    - Scan parcel dimensions
    - Send command for Unit to unlock
    - Send command for Unit to lock
    - Update internal databases
    - Send updated database to server (consider changing to only upload changes)
    - [r] Scan recipient QR code
    - [r] Verify recipient QR code
    - [r] Send command for Unit to unlock
    - [r] Send command for Unit to lock (time-based, consider adding more sensors to know when to lock again)
    """

    CONFIG_FILE_PATH = construct_path("config", "config.json")

    def __init__(self):
        """
        id: id of the locker. should be constant from the birth of the locker. 
        v_code: verification code that is stored from the locker. when establishing first connection from start/restart, id and v_code are sent to the server for identity clarification and online notification. after verifying, the server sends back a new v_code to be recorded and submitted.
        session_id: id of the session. different from locker id and vcode: generated when new connection established, refreshes when next connection established. uses this as a form of referer parameter.
        TODO: consider having a "task backlog" type of thing
        """
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @classmethod
    def load_from_json(cls, config_file_path=None):
        if config_file_path:
            cls.CONFIG_FILE_PATH = config_file_path
        lb_tmp = cls(**jsonIO.load(cls.CONFIG_FILE_PATH)["meta"])
        return

    @staticmethod
    def __verify_identity(_id, v_code):
        # TODO: request for verification from server with these parameters, get new vcode, store in config before next restart
        return True  # returning True for now
