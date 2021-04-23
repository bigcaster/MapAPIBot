import telebot
from bs4 import BeautifulSoup
import requests

url = 'http://api.openweathermap.org/data/2.5/weather'
api_weather = 'e4a3da131fe7dd1aa4d06d1ded5c6963'
api_telegram = '1719349692:AAHNGDF0WeCkGXy3Ef8uWuYXtWmzQF4VypE'

bot = telebot.TeleBot(api_telegram)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Добро пожаловать, ' + str(message.from_user.first_name) + '!' + '\n' +
                     'Чем вам помочь?')
    bot.register_next_step_handler(message)


@bot.message_handler(commands=['news'])
def news(message):
    URL = 'https://ria.ru/world/'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36'
    }

    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    texts = soup.findAll('a', 'list-item__title')

    for i in range(len(texts[:-14]), -1, -1):
        txt = str(i + 1) + ') ' + texts[i].text
        bot.send_message(message.chat.id, '<a href="{}">{}</a>'.format(texts[i]['href'], txt), parse_mode='html')


@bot.message_handler(commands=['weather'])
def weather(message):
    bot.send_message(message.chat.id, 'чтоб узнать погоду напишите в чат название города')
    bot.register_next_step_handler(message, test)


@bot.message_handler(content_types=['text'])
def test(message):
    city_name = message.text

    try:
        params = {'APPID': api_weather, 'q': city_name, 'units': 'metric', 'lang': 'ru'}
        result = requests.get(url, params=params)
        weather = result.json()

        bot.send_message(message.chat.id, "В городе " + str(weather["name"]) + " температура " + str(
            float(weather["main"]['temp'])) + "\n" +
                         "Скорость ветра " + str(float(weather['wind']['speed'])) + "\n" +
                         "Влажность " + str(int(weather['main']['humidity'])) + "%" + "\n" +
                         "Описание " + str(weather['weather'][0]["description"]) + "\n\n")

    except:
        bot.send_message(message.chat.id, "Город " + city_name + " не найден")


if __name__ == '__main__':
    bot.polling(none_stop=True)
