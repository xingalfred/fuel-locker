import json
import math
from datetime import datetime

import requests
from flask import Blueprint, redirect, render_template, request, session, url_for

from . import elevenseven, seveneleven, util

fuelLockerBlueprint = Blueprint("fuelLocker", __name__, template_folder="./templates")


@fuelLockerBlueprint.route("/")
def index():
    session["prices"] = elevenseven.cheapestFuelAll()

    if "accessToken" in session.keys():
        (url, _, headers) = seveneleven.listLockIns(
            session["accessToken"], session["deviceSecret"], session["deviceId"]
        )

        r = requests.get(url, headers=headers)
        response = json.loads(r.text)

        if response:
            session.pop("current", None)
            session.pop("history", None)
            for lock in reversed(response):
                status = int(lock["Status"])
                if status == util.FuelLockStatus.ACTIVE.value:
                    key = "active"
                elif (
                    status == util.FuelLockStatus.EXPIRED.value
                    or status == util.FuelLockStatus.REDEEMED.value
                ):
                    key = "history"
                session[key] = lock
                session[key]["Status"] = util.FuelLockStatus(status).name

                for timestamp in ["RedeemedAt", "ExpiresAt", "CreatedAt"]:
                    if timestamp in lock.keys():
                        session[key][timestamp] = datetime.fromtimestamp(
                            lock[timestamp]
                        ).strftime("%y-%m-%d %H:%M:%S")

    return render_template("index.html")


@fuelLockerBlueprint.route("/login", methods=["POST"])
def login():
    session.pop("ErrorMessage", None)
    session.pop("SuccessMessage", None)

    session["deviceId"] = util.generateDeviceId()

    email = request.form["email"]
    password = request.form["password"]

    (url, payload, headers) = seveneleven.login(session["deviceId"], email, password)

    r = requests.post(url, data=payload, headers=headers)
    response = json.loads(r.text)

    if "Message" in response.keys():
        session["ErrorMessage"] = response["Message"]

    else:
        accessToken = r.headers["X-AccessToken"]

        deviceSecret = response["DeviceSecretToken"]
        accountId = response["AccountId"]
        firstName = response["FirstName"]
        cardBalance = str(response["DigitalCard"]["Balance"])

        session["accessToken"] = accessToken
        session["deviceSecret"] = deviceSecret
        session["accountId"] = accountId
        session["firstName"] = firstName
        session["cardBalance"] = cardBalance

    return redirect(url_for("fuelLocker.index"))


@fuelLockerBlueprint.route("/logout")
def logout():
    (url, data, headers) = seveneleven.logout(
        session["accessToken"], session["deviceSecret"]
    )
    requests.post(url, data=data, headers=headers)
    session.clear()
    return redirect(url_for("fuelLocker.index"))


@fuelLockerBlueprint.route("/lock", methods=["POST"])
def lock():
    fuelType = request.form["fuelType"]
    i = list(filter(lambda x: session["prices"][x]["type"] == fuelType, range(6)))[0]

    (url, payload, headers) = seveneleven.startSession(
        session["accessToken"],
        session["deviceSecret"],
        session["deviceId"],
        session["prices"][i]["lat"],
        session["prices"][i]["lng"],
    )

    r = requests.post(url, data=payload, headers=headers)

    response = json.loads(r.content)

    if "ErrorType" in response.keys():
        session[
            "ErrorMessage"
        ] = "An error has occured. This is most likely due to a fuel lock already being in place."
        return redirect(url_for("fuelLocker.index"))

    ean = util.fuelTypeToEan(fuelType)

    price = 0
    for store in response["CheapestFuelTypeStores"]:
        for fuelPrice in store["FuelPrices"]:
            if fuelPrice["Ean"] == ean:
                price = float(fuelPrice["Price"])
                break
        if price != 0:
            break

    if price == 0:
        raise Exception(
            "Could not find fuel price for selected fuel type {}".format(fuelType)
        )
    elif price > session["prices"][i]["price"]:
        raise Exception(
            "The fuel price is too high compared to the cheapest available."
        )

    balance = float(response["Balance"] * 100)
    numberOfLitres = math.floor(balance / price)

    (url, payload, headers) = seveneleven.confirm(
        session["accessToken"],
        session["deviceSecret"],
        session["deviceId"],
        session["accountId"],
        ean,
        numberOfLitres,
    )

    r = requests.post(url, data=payload, headers=headers)

    response = json.loads(r.content)

    if "Message" in response.keys():
        session["ErrorMessage"] = response["Message"]
    else:
        session[
            "SuccessMessage"
        ] = "Successfully locked {} at {} cents per litre".format(fuelType, price)

    return redirect(url_for("fuelLocker.index"))
