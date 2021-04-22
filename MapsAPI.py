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
}
geocoder_params = {
    "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
    "format": "json",
    "results": 1
}
places_params = {
    "lang": "ru_RU",
    "apikey": "575a0baa-461e-472c-8be2-bb4234d97a53",
}
format_keys = {"geocode": "geocode", "геокод": "geocode", "l": "l", "layer": "l", "слой": "l", "z": "z", "zoom": "z",
               "масштаб": "z", "scale": "scale", "увеличение": "scale", "pt": "pt", "marker": "pt", "метка": "pt",
               "kind": "kind", "toponym": "kind", "топоним": "kind", "text": "text", "search": "text", "place": "text",
               "поиск": "text", "место": "text", "results": "results", "результаты": "results", "trf": "trf",
               "traffic": "trf", "траффик": "trf"
               }
format_values = {"sat": "sat", "satellite": "sat", "спутник": "sat", "map": "map", "схема": "map", "sat,skl": "sat,skl",
                 "sat,map": "sat,skl", "hybrid": "sat,skl", "гибрид": "sat,skl", "house": "house", "дом": "house",
                 "street": "street", "улица": "street", "metro": "metro", "метро": "metro", "district": "district",
                 "район": "district", "locality": "locality", "пункт": "locality"
                 }

mes = "geocode=Арбат, москва;лишний=параметр;результаты=5;топоним=метро;метка=bl,m".lower().split(';')


def map_api(message):
    message_params = {}
    for param in message:
        if '=' in param:
            param_list = list((map(str.strip, param.split('='))))
            if len(param_list) != 2:
                return "ERROR: ошибка в запрсое"
            key, value = param_list
            if key in format_keys:
                right_key = format_keys[key]
                if right_key in message_params:
                    return "ERROR: такой параметр уже есть"
                message_params[right_key] = value

    if "geocode" not in message_params and "text" not in message_params:
        return "ERROR: отсутствуют обязательные параметры"
    elif "text" in message_params and "geocode" in message_params:
        return "ERROR: несочетаемые параметры"

    for key, value in message_params.items():
        if key in ["geocode", "kind", "results"]:
            if key == "kind":
                if value in format_values:
                    value = format_values[value]
                else:
                    return "ERROR: неверное значение параметра kind"
            geocoder_params[key] = value

    geocode_response = requests.get(geocode_api_server, params=geocoder_params)
    if not geocode_response:
        return f"""Ошибка запроса: {geocode_api_server}
Http статус: {geocode_response.status_code} ({geocode_response.reason})"""

    json_geocode_response = geocode_response.json()
    try:
        envelope = \
            json_geocode_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["boundedBy"][
                "Envelope"]
        lower_lon, lower_lat = map(float, envelope["lowerCorner"].split())
        upper_lon, upper_lat = map(float, envelope["upperCorner"].split())
        spn = f"{upper_lon - lower_lon},{upper_lat - lower_lat}"
        pos = json_geocode_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
        pos = ",".join(pos.split())
    except Exception:
        return "ERROR: не удалось получить значения ответа на запрос"

    toponym_names, toponym_poses = [], []
    geocoder_params["geocode"] = pos
    if "kind" in geocoder_params:
        toponym_geocode_response = requests.get(geocode_api_server, params=geocoder_params)
        json_toponym_geocode_response = toponym_geocode_response.json()
        for member in json_toponym_geocode_response["response"]["GeoObjectCollection"]["featureMember"]:
            toponym_names.append(member["GeoObject"]["name"])
            toponym_poses.append(member["GeoObject"]["Point"]["pos"])
        if not toponym_names:
            return "Не удалось найти ближайшие топонимы"

    for key, value in message_params.items():
        if key in ["l", "z", "scale", "pt", "trf"]:
            if key == "l":
                if value in format_values:
                    value = format_values[value]
                else:
                    return "ERROR: неверное значение параметра l"
            elif key == "pt":
                pass
            elif key == "z" and not (value.isdigit() and 0 <= int(value) <= 17):
                return "ERROR: неверное значение параметра z"
            elif key == "scale" and not (value.isdigit() and 1 <= float(value) <= 4):
                return "ERROR: неверное значение параметра scale"
            static_params[key] = value
    if "z" not in static_params:
        static_params["spn"] = spn
    if "pt" in message_params:
        marker_definition = message_params.get("pt").split(',')
        if len(marker_definition) != 2:
            return "ERROR: неправильное количество аргументов в параметре метки"
        marker_color, marker_size = marker_definition
        if not (marker_color in ["wt", "do", "db", "bl", "gn", "dg", "gr", "lb", "nt", "or", "pn", "rd", "vv", "yw",
                                 "org", "dir", "bylw"] and marker_size in ["m", "l"]):
            return "ERROR: неправильное значение аргументов в параметре метки"
    else:
        marker_color, marker_size = "dir", "m"
    if toponym_poses:
        static_params["pt"] = '~'.join(
            [",".join(toponym_pos.split()) + f",pm2{marker_color}{marker_size}" for toponym_pos in toponym_poses])
    else:
        static_params["ll"] = pos
        if "pt" in message_params:
            static_params["pt"] = f"{pos},pm2{marker_color}{marker_size}"
    static_response = requests.get(static_api_server, params=static_params)
    if not static_response:
        return f"""Ошибка запроса: {static_api_server}
Http статус: {static_response.status_code}, ({static_response.reason})"""

    map_file = "map.png"
    with open(map_file, 'wb') as file:
        file.write(static_response.content)
    im = Image.open(map_file)
    im.show()
    os.remove(map_file)


if __name__ == '__main__':
    result = map_api(mes)
    if result is not None:
        print(result)
