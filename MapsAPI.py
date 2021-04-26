import os
import requests
from PIL import Image
from serversAndParams import static_api_server, geocode_api_server, places_api_server
from serversAndParams import static_params, geocoder_params, places_params, format_keys, format_values

mes = "geocode=Москва;лишний=параметр;l=map;kind=locality;results=2".lower().split(';')


class MapAPI:
    def __init__(self, message):
        self.message = message
        self.message_params = {}
        self.static_params = static_params
        self.geocoder_params = geocoder_params
        self.places_params = places_params
        self.kind_param = None
        output = self.main()
        if output is not None:
            print(output)

    def main(self):
        self.message_params = {}
        for param in self.message:
            if '=' in param:
                param_list = list((map(str.strip, param.split('='))))
                if len(param_list) != 2:
                    return "Ошибка в инициализации параметра"
                key, value = param_list
                if key in format_keys:
                    right_key = format_keys[key]
                    if right_key in self.message_params:
                        return "Одинаковые параметры в запросе"
                    self.message_params[right_key] = value

        geocode_param = "geocode" in self.message_params
        text_param = "text" in self.message_params
        self.kind_param = "kind" in self.message_params
        if not geocode_param and not text_param:
            return "ERROR: отсутствует обязательный параметр"
        elif geocode_param and text_param:
            return "ERROR: параметры text и geocode в запросе"
        elif text_param and self.kind_param:
            return "ERROR: параметры text и kind в запросе"

        for key, value in self.message_params.items():
            if key in ["l", "z", "scale", "pt", "trf"]:
                if key == "l":
                    if value in format_values:
                        value = format_values[value]
                    else:
                        return "Неверное значение параметра l"
                elif key == "z" and not (value.isdigit() and 0 <= int(value) <= 17):
                    return "Неверное значение параметра z"
                elif key == "scale" and not (value.isdigit() and 1 <= float(value) <= 4):
                    return "Неверное значение параметра scale"
                self.static_params[key] = value

        if geocode_param:
            output = self.geocode_request()
        else:
            output = self.text_request()
        if output is not None:
            return output
        static_response = requests.get(static_api_server, params=self.static_params)
        if not static_response:
            return f"""Ошибка в запросе: {static_api_server}
Http статус: {static_response.status_code} ({static_response.reason})"""

        self.show_image(static_response.content)

    def geocode_request(self):
        for key, value in self.message_params.items():
            if key in ["geocode", "kind", "results"]:
                if key == "kind":
                    if value in format_values:
                        value = format_values[value]
                    else:
                        return "ERROR: недопустимое значение параметра kind"
                self.geocoder_params[key] = value

        geocode_response = requests.get(geocode_api_server, params=self.geocoder_params)
        if not geocode_response:
            return f"""Ошибка запроса: {geocode_api_server}
        Http статус: {geocode_response.status_code} ({geocode_response.reason})"""
        json_geocode_response = geocode_response.json()
        pos = None
        try:
            objects = []
            members = json_geocode_response["response"]["GeoObjectCollection"]["featureMember"]
            if self.kind_param:
                members = [members[0]]
            for member in members:
                envelope = member["GeoObject"]["boundedBy"]["Envelope"]
                lower_lon, lower_lat = map(float, envelope["lowerCorner"].split())
                upper_lon, upper_lat = map(float, envelope["upperCorner"].split())
                spn = f"{upper_lon - lower_lon},{upper_lat - lower_lat}"
                pos = ",".join(member["GeoObject"]["Point"]["pos"].split())
                address = member["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["text"]
                if not self.kind_param:
                    info = {"spn": spn, "pos": pos, "address": address}
                    objects.append(info)
        except Exception:
            return "Произошла ошибка во время обработки запроса"
        if not objects and not self.kind_param:
            return "Не удалось найти объекты"
        init_marker_params_output = self.init_marker_params()
        if len(init_marker_params_output) == 1:
            return init_marker_params_output
        marker_color, marker_size = init_marker_params_output
        if self.kind_param:
            find_toponyms_output = self.find_toponyms(pos)
            if isinstance(find_toponyms_output, str):
                return find_toponyms_output
            toponyms = find_toponyms_output
            self.static_params["pt"] = '~'.join(
                [f"{','.join(toponym['pos'].split())},pm2{marker_color}{marker_size}" for toponym in toponyms])
            if "z" not in static_params:
                static_params["spn"] = max(toponym["spn"] for toponym in toponyms)
        else:
            self.static_params["pt"] = '~'.join(
                [f"{geo_object['pos']},pm2{marker_color}{marker_size}" for geo_object in objects])
            if "z" not in self.static_params:
                self.static_params["spn"] = max(geo_object["spn"] for geo_object in objects)

    def text_request(self):
        for key, value in self.message_params.items():
            if key in ["text", "results"]:
                self.places_params[key] = value
        places_response = requests.get(places_api_server, params=self.places_params)
        if not places_response:
            return f"""Ошибка в запросе: {places_api_server}
Http статус: {places_response.status_code} ({places_response.reason})"""

        json_places_response = places_response.json()
        features = []
        for feature in json_places_response["features"]:
            info = {"name": feature.get("properties", {"name": "Не найдено"}).get("name", "Не найдено"),
                    "coordinates": feature.get("geometry", {"coordinates": "Не найден"}).get("coordinates",
                                                                                             "Не найдено"),
                    "address": feature.get("properties", {"description": "Не найдено"}).get("description",
                                                                                            "Не найдено")}
            spn = feature.get("properties", {"boundedBy": None}).get("boundedBy", None)
            if spn is not None:
                lower, upper = spn
                spn = f"{upper[0] - lower[0]},{upper[1] - lower[1]}"
            info["spn"] = spn
            if "CompanyMetaData" in feature["properties"]:
                meta_data = feature.get("properties", {"CompanyMetaData": "Не найдено"}).get("CompanyMetaData",
                                                                                             "Не найдено")
                if meta_data == "Не найдено":
                    info["category"] = info["hours"] = info["url"] = info["phones"] = "Не найден"
                    features.append(info)
                    continue
                info["category"] = " / ".join(
                    [category["name"] for category in meta_data.get("Categories", [{"name": "Не найдено"}])])
                info["hours"] = meta_data.get("Hours", {'text': "Не найдено"}).get("text", "Не найдено")
                info["url"] = meta_data.get("url", "Не найдено")
                if "Phones" in meta_data:
                    info["phones"] = " / ".join(
                        [phone["formatted"] for phone in meta_data.get("Phones", ["Не найдено"])])
            else:
                info["address"] = feature.get("properties", {"description": "Не найдено"}).get("description",
                                                                                               "Не найден")
            features.append(info)
        if not features:
            return "Не удалось получить описание организаций"
        init_marker_params_output = self.init_marker_params()
        if isinstance(init_marker_params_output, str):
            return init_marker_params_output
        marker_color, marker_size = init_marker_params_output
        self.static_params["pt"] = "~".join(
            f"{','.join(map(str, feature['coordinates']))},pm2{marker_color}{marker_size}" for feature in features)
        if "z" not in self.static_params:
            static_params["spn"] = max(info["spn"] for info in features)

    def find_toponyms(self, pos):
        self.geocoder_params["geocode"] = pos
        toponym_geocode_response = requests.get(geocode_api_server, params=self.geocoder_params)
        json_toponym_geocode_response = toponym_geocode_response.json()
        try:
            toponyms = []
            for member in json_toponym_geocode_response["response"]["GeoObjectCollection"]["featureMember"]:
                envelope = member["GeoObject"]["boundedBy"]["Envelope"]
                l1, l2 = map(float, envelope["lowerCorner"].split())
                u1, u2 = map(float, envelope["upperCorner"].split())
                spn = f"{u1 - l1},{u2 - l2}"
                info = {"name": member["GeoObject"]["name"], "pos": member["GeoObject"]["Point"]["pos"],
                        "address": member["GeoObject"]["description"], "spn": spn}
                toponyms.append(info)
        except Exception:
            return "Произошла ошибка во время обработки топонимов"
        if not toponyms:
            return "Не удалось получить описание топонимов"
        return toponyms

    def init_marker_params(self):
        marker_definition = self.message_params.get("pt", "nt,m").split(',')
        if len(marker_definition) != 2:
            return "Неверное количество параметров в описании метки"
        marker_color, marker_size = marker_definition
        if marker_color not in ["wt", "do", "db", "bl", "gn", "dg", "gr", "lb", "nt", "or", "pn", "rd", "vv", "yw",
                                "org", "dir", "bylw"] or marker_size not in ["m", "l"]:
            return "Неправильное значение аргументов в параметре метки"
        return marker_color, marker_size

    def show_image(self, content):
        map_file = "map.png"
        with open(map_file, 'wb') as file:
            file.write(content)
        im = Image.open(map_file)
        im.show()
        os.remove(map_file)


if __name__ == '__main__':
    map_api = MapAPI(mes)
