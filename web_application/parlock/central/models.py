from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email or not username:
            return "Required fields are missing."

        user = self.model(
            username=username,
            email=email,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """A custom made user class to be used within Django's internal system. Is kind of dimension."""
    username = models.CharField(unique=True, max_length=32)
    email = models.EmailField(unique=True, max_length=255)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, email={self.email})"

    @property
    def is_staff(self):
        return self.is_admin

    def parcels(self):
        self.parcel_set
        p_list = [parcel for parcel in Parcel.objects.filter(recipient=self)]
        p_list.sort(key=lambda p: p.last_seen_activity().datetime, reverse=True)
        return p_list


class LockerUnit(models.Model):
    """A logical representation of a locker unit. Locker units don't have the ability to talk to the server directly. Is dimension."""
    length = models.DecimalField(max_digits=6, decimal_places=3)
    width = models.DecimalField(max_digits=6, decimal_places=3)
    height = models.DecimalField(max_digits=6, decimal_places=3)

    def __repr__(self):
        return f"LockerUnit(id={self.id}, length={self.length}, width={self.width}, height={self.height})"


class LockerBase(models.Model):
    """A logical representation of a locker base inside the system. A locker base can have many locker units. Is dimension."""

    class State(models.TextChoices):
        JHR = "JHR", "Johor"
        KDH = "KDH", "Kedah"
        KTN = "KTN", "Kelantan"
        MLK = "MLK", "Malacca"
        NSN = "NSN", "Negeri Sembilan"
        PHG = "PHG", "Pahang"
        PNG = "PNG", "Penang"
        PRK = "PRK", "Perak"
        PLS = "PLS", "Perlis"
        SGR = "SGR", "Selangor"
        TRG = "TRG", "Terengganu"
        SBH = "SBH", "Sabah"
        SWK = "SWK", "Sarawak"
        KUL = "KUL", "Federal Territory of Kuala Lumpur"

    name = models.CharField(unique=True, null=False, max_length=64)  # should be something like "Parlock @ South City Plaza"
    street_address = models.CharField(unique=False, null=False, max_length=128)
    city = models.CharField(unique=False, null=False, max_length=64)
    state = models.CharField(choices=State.choices, null=False, max_length=64)
    zip_code = models.CharField(unique=False, null=False, max_length=5)
    verification_code = models.CharField(unique=True, null=False, max_length=12)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"LockerBase(id={self.id}, name={self.name}, address={self.address[:20]}, verification_code={self.verification_code})"

    @property
    def address(self):
        return f"{self.street_address}, {self.zip_code} {self.city}, {self.State(self.state).label}"

    def nearby(self):
        return [lb for lb in LockerBase.objects.filter(zip_code=self.zip_code)[:3]]

    @staticmethod
    def verify(v_code: str):
        return LockerBase.objects.get(verification_code=v_code)

    def add_activity(self, *, activity_type: int, locker_unit: LockerUnit = None):
        la = LockerActivity(locker_base=self, locker_unit=locker_unit, type=activity_type)
        la.save()
        return la


class LockerActivity(models.Model):
    """
    An action log that records the activities of locker bases and units. Should include the following:
        - Going online (base and unit)
        - Scanning (submit query of parcel qr code/recipient qr code to webserver)
        - Scanning dimensions
        - Locker unit lock/unlock

    """
    class ActivityType(models.IntegerChoices):
        ONLINE = 1, "ONLINE"  # when the base initializes and connects to the webserver
        OFFLINE = 2, "OFFLINE"  # will before death
        REGISTER = 3, "REGISTER"  # [UNIT] after base initialization, base queries units, informs webserver about available units
        SCANQRRECIPIENT = 4, "SCANQRRECIPIENT"  # the process of determining if a QR code is a parcel or recipient identification is done on the locker base.
        SCANQRPARCEL = 5, "SCANQRPARCEL"
        SCANDIM = 6, "SCANDIM"  # reporting the parcel dimensions (or don't)
        UNLOCK = 7, "UNLOCK"  # [UNIT] unit unlock
        LOCK = 8, "LOCK"  # [UNIT] unit lock

    locker_base = models.ForeignKey(LockerBase, null=False, on_delete=models.CASCADE)
    locker_unit = models.ForeignKey(LockerUnit, null=True, on_delete=models.CASCADE)  # important! not every activity has to involve a locker unit!
    type = models.PositiveSmallIntegerField(choices=ActivityType.choices, null=False)
    datetime = models.DateTimeField(auto_now_add=True)

    def __repr__(self) -> str:
        return f"LockerActivity(id={self.id}, locker_base={self.locker_base.name}, locker_unit={self.locker_unit}, type={LockerActivity.ActivityType(self.type).label})"


class Parcel(models.Model):
    """A parcel item to be registered within the system. Is dimension."""
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    destination_locker = models.ForeignKey(LockerBase, on_delete=models.CASCADE)
    tracking_number = models.CharField(null=False, unique=True, max_length=32)  # value to be verified with qr

    def __repr__(self) -> str:
        return f"Parcel(recipient={self.recipient.username}, destination_locker={self.destination_locker.name}, tracking_number={self.tracking_number})"

    def last_seen_activity(self):
        return ParcelActivity.objects.filter(parcel=self).latest("datetime")

    def activities(self):
        return [pa for pa in ParcelActivity.objects.filter(parcel=self).order_by("-datetime")]

    def can_be_withdrawn(self) -> bool:
        return 4 <= self.last_seen_activity().type < 7

    def add_activity(self, locker_base: LockerBase, activity_type: int):
        if locker_base == self.destination_locker:
            try:
                if activity_type == ParcelActivity.ActivityType.QUERY:
                    # query is associated with scanqrparcel
                    la = locker_base.add_activity(activity_type=LockerActivity.ActivityType.ONLINE, locker_unit=None)
                if la:
                    pa = ParcelActivity(parcel=self, type=activity_type, associated_locker_activity=la)
                    pa.save()
                    return True
                else:
                    pa = ParcelActivity(parcel=self, type=activity_type, associated_locker_activity=None)
                    pa.save()
                    return True
            except:
                return False
        else:
            return False


class ParcelActivity(models.Model):
    """
    An action log that records the activities of parcels. Should include the following:
        - Registration (adding into the system)
        - verification of parcel (base asks: is the parcel registered in the system?)
        - check in (scan dimension)
        - deposit
        - Withdrawal request (when user requests for qr code for withdrawal)
        - Withdrawal (after confirmation from locker base)
        - Cancellation (soft delete)

    associated_locker_activity: some parcel activities can be mapped to be related with certain locker activities, that's how the system knows which locker is associated with each parcel. 
        - when the parcel qr code is scanned, an entry is created in LockerActivity to scan. the same code is queried from Parcel.tracking_number to see if it is a valid parcel. if yes, then a ParcelActivity entry is added with type Arrival, with the LockerActivity entry linked in the associated_locker_activity field
        - when the parcel dimension is scanned, an entry is created in LockerActivity as well. This action is associated with 'checking in' in this table.
        - the base is planned to send entries to lock and unlock as two separate entries. deposit and withdrawal should be associated with 2 locker activities each...?
        - when the user qr code is scanned, locker activity is created, then associating parcel activity with type withdraw request is noted down.

    the use of associated locker activity allows the system to refer to past activity while not touching the dimension tables themselves.

    """

    class ActivityType(models.IntegerChoices):

        REGISTER = 1, "REGISTER"  # when the parcel is registered into the system
        QUERY = 2, "QUERY"  # associated with SCANQRPARCEL
        CHECKIN = 3, "CHECKIN"  # associated with SCANDIM
        DEPOSIT = 4, "DEPOSIT"  # associated with LOCK and UNLOCK
        WITHDRAWAPP = 5, "WITHDRAWAPP"  # added when user clicks on the option to generate qr code, only type that uses qr_data
        WITHDRAWREQ = 6, "WITHDRAWREQ"  # associated with SCANQRRECIPIENT
        WITHDRAW = 7, "WITHDRAW"  # associated with LOCK and UNLOCK
        CANCEL = 8, "CANCEL"  # a label that shows the parcel as not being able to arrive, tracking number is *not* released

    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE)
    type = models.PositiveSmallIntegerField(choices=ActivityType.choices, null=False)
    datetime = models.DateTimeField(auto_now_add=True)
    # image = models.ImageField() # still hesitating about adding this one, it doesn't actually add real value, just ease of tracing back to troubleshoot. maybe in future versions.
    # is the qr data to verify when user tries to withdraw. should be the hash of the parcel added with the current timestamp. (planned to be implemented like this)
    # qr_data = models.IntegerField(null=True, unique=True)

    associated_locker_activity = models.ForeignKey(LockerActivity, null=True, on_delete=models.CASCADE)

    def get_type_str(self):
        return self.ActivityType(self.type).label
