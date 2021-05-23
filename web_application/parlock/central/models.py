from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from django.db.models.enums import Choices
import uuid


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

    @property
    def is_staff(self):
        return self.is_admin


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

    name = models.CharField(unique=True, null=False, max_length=8)
    street_address = models.CharField(unique=False, null=False, max_length=128)
    city = models.CharField(unique=False, null=False, max_length=64)
    state = models.CharField(choices=State.choices, null=False, max_length=64)
    zip_code = models.CharField(unique=False, null=False, max_length=5)

    def __str__(self):
        return self.name


class LockerUnit(models.Model):
    """A logical representation of a locker unit. Locker units don't have the ability to talk to the server directly. Is dimension."""
    length = models.DecimalField(max_digits=6, decimal_places=3)
    width = models.DecimalField(max_digits=6, decimal_places=3)
    height = models.DecimalField(max_digits=6, decimal_places=3)


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
    _type = models.PositiveSmallIntegerField(choices=ActivityType.choices, null=False)
    datetime = models.DateTimeField(auto_now_add=True)


class Parcel(models.Model):
    """A parcel item to be registered within the system. Is dimension."""
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    destination_locker = models.ForeignKey(LockerBase, on_delete=models.CASCADE)
    tracking_number = models.CharField(null=False, unique=True, max_length=32)  # value to be verified with qr


class ParcelActivity(models.Model):
    """
    An action log that records the activities of parcels. Should include the following:
        - Registration (adding into the system)
        - verification of parcel (base asks: is the parcel registered in the system?)
        - check in (scan dimension)
        - deposit
        - Withdrawal request (when user requests for qr code for withdrawal)
        - Withdrawal (after confirmation from locker base)

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

    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE)
    _type = models.PositiveSmallIntegerField(choices=ActivityType.choices, null=False)
    datetime = models.DateTimeField(auto_now_add=True)
    # image = models.ImageField() # still hesitating about adding this one, it doesn't actually add real value, just ease of tracing back to troubleshoot. maybe in future versions.
    # is the qr data to verify when user tries to withdraw. should be the hash of the parcel added with the current timestamp. (planned to be implemented like this)
    qr_data = models.IntegerField(null=True, unique=True)

    associated_locker_activity = models.ForeignKey(LockerActivity, null=True, on_delete=models.CASCADE)
