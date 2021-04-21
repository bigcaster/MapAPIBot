import os
import sys
import requests
import json
from PIL import Image

static_api_server = "https://static-maps.yandex.ru/1.x/"
geocode_api_server = "https://geocode-maps.yandex.ru/1.x/"
places_api_server = "https://search-maps.yandex.ru/v1/"
static_params = {
    "l": "map",
    "ll": None,
}
geocoder_params = {
    "geocode": None,
    "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
    "format": "json",
    "results": 1
}
places_params = {
    "text": None,
    "lang": "ru_RU",
    "apikey": "575a0baa-461e-472c-8be2-bb4234d97a53",
    "format": "json"
}
format_keys = {"location": "geocode", "локация": "geocode", "geocode": "geocode", "геокод": "geocode", "l": "l",
               "layer": "l", "слой": "l", "spn": "spn", "area": "spn", "область": "spn", "z": "z", "zoom": "z",
               "масштаб": "z", "scale": "scale", "увеличение": "scale", "size": "size", "размер": "size", "pt": "pt",
               "mark": "pt", "метка": "pt", "kind": "kind", "toponym": "kind", "топоним": "kind", "text": "text",
               "search": "text", "place": "text", "поиск": "text", "место": "text", "results": "results",
               "результат": "results", "trf": "trf", "traffic": "trf", "траффик": "trf"}

format_values = {"sat": "sat", "satellite": "sat", "спутник": "sat", "map": "map", "схема": "map", "sat,skl": "sat,skl",
                 "hybrid": "sat,skl", "гибрид": "sat,skl", "metro": "metro", "метро": "metro"}

mes = "geocode=Москва, Ленина 50б; слой=спутник;топоним=метро;лишний=параметр".lower().split(';')


def check_error(all_params, message_params):
    if len(all_params) != len(set(all_params)):
        print("ERROR! - одинаковые параметры - SYS.EXIT")
        sys.exit(1)
    if not ("geocode" in message_params or "text" in message_params):
        print("ERROR! - отсутствуют обязательные параметры - SYS.EXIT")
        sys.exit(1)
    if "text" in message_params and "geocode" in message_params:
        print("ERROR! - несочетаемые параметры - SYS.EXIT")
        sys.exit(1)
    if "spn" in message_params and "z" in message_params:
        print("ERROR! - несочетаемые параметры - SYS.EXIT")
        sys.exit(1)


def map_api(message):
    unprocessed_message_params = {}
    for param in message:
        if '=' in param:
            key, value = map(str.strip, param.split('='))
            unprocessed_message_params[key] = value

    all_params = []
    for key in unprocessed_message_params.keys():
        if key in format_keys:
            all_params.append(format_keys[key])

    message_params = {}
    for key, value in unprocessed_message_params.items():
        if key in format_keys:
            message_params[format_keys[key]] = unprocessed_message_params[key]

    check_error(all_params, message_params)

    for key, value in message_params.items():
        if key in ["geocode", "kind", "results"]:
            if key == "kind":
                value = format_values[value]
            geocoder_params[key] = value

    geocode_response = requests.get(geocode_api_server, params=geocoder_params)
    if not geocode_response:
        print(f"""Ошибка запроса: {geocode_api_server}
Http статус: {geocode_response.status_code} ({geocode_response.reason})""")
        sys.exit(1)
    json_geocode_response = geocode_response.json()
    pos = json_geocode_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
    lon, lat = pos.split()
    envelope = json_geocode_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["boundedBy"][
        "Envelope"]
    lower, upper = envelope["lowerCorner"], envelope["upperCorner"]
    lower_lon, lower_lat = map(float, lower.split())
    upper_lon, upper_lat = map(float, upper.split())
    spn = upper_lon - lower_lon, upper_lat - lower_lat


map_api(mes)