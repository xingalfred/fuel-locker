import json

import requests


def cheapestFuelAll() -> dict:
    r = requests.get("https://projectzerothree.info/api.php?format=json")
    response = json.loads(r.text)
    prices = response["regions"][0]["prices"]
    return prices
