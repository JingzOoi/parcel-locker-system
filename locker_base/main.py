from model.LockerBase import LockerBase
from model.LockerUnit import LockerUnit
from utils.construct import construct_path


lb = LockerBase.load_from_json()

print(lb.id)
