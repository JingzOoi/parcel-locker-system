from inspect import getmembers


class LockerUnit:

    """
    Is a space to put parcels in to and take parcels out from.
    Attributes:
    - id
    - name
    - size (a tuple with 3 dimensions)
    Main roles:
    - Connect to Base
    - Wait for command from Base
    - Unlock (consider adding origin/referer kwargs as verification)
    - Lock
    """

    def __init__(self, _id, name, size):
        self.id = _id
        self.name = name
        self.size = size

    def __repr__(self):
        return f"LockerUnit(id={self.id}, name={self.name}, size={self.size})"

    def __eq__(self, other_locker_unit):
        return True if isinstance(other_locker_unit) == LockerUnit and other_locker_unit.id == self.id else False

    def connect(self):
        pass

    def unlock(self):
        pass

    def lock(self):
        pass


if __name__ == "__main__":
    arguments = {
        "_id": "LU00001",
        "name": "LU00001",
        "size": (30, 30, 30)
    }
    lu = LockerUnit(**arguments)
    print(repr(lu))
