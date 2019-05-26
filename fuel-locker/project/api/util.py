import enum
import random

types = {}
types["U91"] = 52
types["Diesel"] = 53
types["LPG"] = 54
types["U95"] = 55
types["U98"] = 56
types["E10"] = 57


class FuelLockStatus(enum.Enum):
    ACTIVE = 0
    EXPIRED = 1
    REDEEMED = 2


def generateDeviceId() -> str:
    return "".join(random.choice("0123456789abcdef") for i in range(15))


def fuelTypeToEan(fuelType: str) -> int:
    if fuelType in types.keys():
        return types[fuelType]
    else:
        raise Exception("Locked in an invalid fuel type {}".format(fuelType))
