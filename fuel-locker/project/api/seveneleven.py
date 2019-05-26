import base64
import hashlib
import hmac
import time
import typing
import uuid

from . import constants

Request = typing.Tuple[str, str, dict]


def getKey(encryptedKey: typing.List[int]) -> str:
    # get the hex from the encrypted secret key and then split every 2nd character into an array row
    hex_string = hashlib.sha1("om.sevenel".encode("utf-8")).hexdigest()
    hex_array = [hex_string[i : i + 2] for i in range(0, len(hex_string), 2)]

    # Key is the returned key
    key = ""
    i = 0

    # Get the unobfuscated key
    while i < len(encryptedKey):
        length = i % (len(hex_array))
        key += chr(int(hex_array[length], 16) ^ int(encryptedKey[i]))

        i = i + 1
    return key


key = getKey(constants.OBFUSCATED_APP_ID)
key2 = base64.b64decode(getKey(constants.OBFUSCATED_API_ID))


def login(accessToken: str, email: str, password: str) -> typing.Tuple[str, str, dict]:
    payload = (
        '{"Email":"%s","Password":"%s","DeviceName":"HTC6525LVW","DeviceOsNameVersion":"Android 8.1.0"}'
        % (email, password)
    )

    url = getUrl("/account/login")
    timestamp = str(int(time.time()))
    uuidVar = str(uuid.uuid4())
    tssa = getTssa(url, timestamp, uuidVar, "POST", payload, None)
    headers = getHeaders(tssa, accessToken, None)

    return (url, payload, headers)


def logout(accessToken: str, deviceSecret: str) -> typing.Tuple[str, str, dict]:
    payload = '""'

    url = getUrl("/account/logout")

    timestamp = str(int(time.time()))
    uuidVar = str(uuid.uuid4())

    tssa = getTssa(url, timestamp, uuidVar, "POST", payload, accessToken)
    headers = getHeaders(tssa, deviceSecret, None)

    return (url, payload, headers)


def startSession(
    accessToken: str, deviceSecret: str, deviceId: str, lat: str, lng: str
) -> typing.Tuple[str, str, dict]:
    timestamp = str(int(time.time()))

    payload = '{"LastStoreUpdateTimestamp":%s,"Latitude":"%s","Longitude":"%s"}' % (
        timestamp,
        lat,
        lng,
    )

    url = getUrl("/FuelLock/StartSession")
    uuidVar = str(uuid.uuid4())

    tssa = getTssa(url, timestamp, uuidVar, "POST", payload, accessToken)
    headers = getHeaders(tssa, deviceId, deviceSecret)

    return (url, payload, headers)


def confirm(
    accessToken: str,
    deviceSecret: str,
    deviceId: str,
    accountId: str,
    fuelType: str,
    numberOfLitres: int,
) -> typing.Tuple[str, str, dict]:
    numberOfLitres = 5
    payload = '{"AccountId":"%s","FuelType":"%s","NumberOfLitres":"%s"}' % (
        accountId,
        fuelType,
        str(numberOfLitres),
    )

    url = getUrl("/FuelLock/Confirm")
    timestamp = str(int(time.time()))
    uuidVar = str(uuid.uuid4())
    tssa = getTssa(url, timestamp, uuidVar, "POST", payload, accessToken)
    headers = getHeaders(tssa, deviceId, deviceSecret)

    return (url, payload, headers)


def listLockIns(
    accessToken: str, deviceSecret: str, deviceId: str
) -> typing.Tuple[str, str, dict]:
    url = getUrl("/FuelLock/List")
    timestamp = str(int(time.time()))
    uuidVar = str(uuid.uuid4())

    tssa = getTssa(url, timestamp, uuidVar, "GET", None, accessToken)
    headers = getHeaders(tssa, deviceId, deviceSecret)
    return (url, "", headers)


def getUrl(path: str) -> str:
    return "%s%s%s" % (constants.API_BASE_URL, constants.LATEST_API_VERSION, path)


def getTssa(
    url: str,
    timestamp: str,
    uuidVar: str,
    method: str,
    payload: typing.Optional[str],
    accessToken: typing.Optional[str],
) -> str:
    replace = url.replace("https", "http").lower()

    str3 = key + method + replace + timestamp + uuidVar

    if payload is not None:
        data = base64.b64encode(hashlib.md5(payload.encode("utf-8")).digest()).decode(
            "utf-8"
        )
        str3 += data

    signature = base64.b64encode(
        hmac.new(key2, str3.encode("utf-8"), digestmod=hashlib.sha256).digest()
    )

    tssa = "tssa 4d53bce03ec34c0a911182d4c228ee6c:%s:%s:%s" % (
        signature.decode("utf-8"),
        uuidVar,
        timestamp,
    )

    if accessToken is not None:
        tssa += ":%s" % accessToken

    return tssa


def getHeaders(tssa: str, deviceId: str, deviceSecret: typing.Optional[str]) -> dict:
    headers = {}
    headers["Content-Type"] = "application/json; charset=utf-8"
    headers["User-Agent"] = "Apache-HttpClient/UNAVAILABLE (java 1.4)"
    headers["X-DeviceID"] = deviceId
    headers["X-OsName"] = "Android"
    headers["X-OsVersion"] = "Android 8.1.0"
    headers["X-AppVersion"] = "1.7.0.2009"
    headers["Authorization"] = tssa
    if deviceSecret is not None:
        headers["X-DeviceSecret"] = deviceSecret
    return headers
