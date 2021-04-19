import requests
import sys
import os
from PIL import Image

request = 'https://static-maps.yandex.ru/1.x/?ll=132,-26&l=sat&z=4'
response = requests.get(request)
if not response:
    print("Ошибка запроса:", request)
    print("Http статус:", response.status_code, "(", response.reason, ")")
    sys.exit(1)
map_file = "map.png"
with open(map_file, 'wb') as file:
    file.write(response.content)
im = Image.open(map_file)
im.show()
os.remove(map_file)
