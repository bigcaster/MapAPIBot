import telebot
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from pycbrf import ExchangeRates

url = 'http://api.openweathermap.org/data/2.5/weather'
api_weather = 'e4a3da131fe7dd1aa4d06d1ded5c6963'
api_telegram = '1719349692:AAHNGDF0WeCkGXy3Ef8uWuYXtWmzQF4VypE'

bot = telebot.TeleBot(api_telegram)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 'Добро пожаловать, ' + str(message.from_user.first_name) + '!' + '\n' +
                     'Чем вам помочь?')


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id,
                     '/start запуск бота\n/help команды бота\n/weather узнать погоду' + '\n' +
                     '/news узнать сегодняшние новости' + '\n' + '/currency курс валют' + '\n' +
                     '/map карты')


@bot.message_handler(commands=['news'])
def news(message):
    URL = 'https://ria.ru/world/'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36'
    }

    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    texts = soup.findAll('a', 'list-item__title')

    for i in range(len(texts[:-16]), -1, -1):
        txt = str(i + 1) + ') ' + texts[i].text
        bot.send_message(message.chat.id, '<a href="{}">{}</a>'.format(texts[i]['href'], txt), parse_mode='html')


@bot.message_handler(commands=['map'])
def map(message):
    bot.send_message(message.chat.id, 'Что вас интересует?')
    bot.register_next_step_handler(message)
    map_file = "map.png"
    with open(map_file, 'wb') as file:
        file.write(content)

    if not geocode_response:
        return f"Ошибка запроса: {geocode_api_server}"
    else:
        return geocode_request


@bot.message_handler(commands=['currency'])
def currency(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton('GBP')
    item2 = telebot.types.KeyboardButton('EUR')
    item3 = telebot.types.KeyboardButton('CNY')
    item4 = telebot.types.KeyboardButton('USD')
    markup.add(item1, item2, item3, item4)
    bot.send_message(chat_id=message.chat.id, text="<b>Какой курс валюты вас интересует?</b>", reply_markup=markup,
                     parse_mode="html")
    bot.register_next_step_handler(message, exchange_rate)


@bot.message_handler(content_types=['USD', 'EUR', 'CNY', 'GBP'])
def exchange_rate(message):
    message_norm = message.text.strip().lower()
    if message_norm in ['usd', 'eur', 'cny', 'gbp']:
        rates = ExchangeRates(datetime.now())
        bot.send_message(chat_id=message.chat.id,
                         text=f"<b>Сейчас курс: {message_norm.upper()} = {float(rates[message_norm.upper()].rate)}</b>",
                         parse_mode="html")
    else:
        bot.send_message(message.chat.id, f'Такой курс валюты: {message_norm.upper()} не найден')
    bot.register_next_step_handler(message)


@bot.message_handler(commands=['weather'])
def weather(message):
    bot.send_message(message.chat.id, 'Чтобы узнать погоду напишите в чат название города')
    bot.register_next_step_handler(message, test)


@bot.message_handler(content_types=['text'])
def test(message):
    city_name = message.text

    try:
        params = {'APPID': api_weather, 'q': city_name, 'units': 'metric', 'lang': 'ru'}
        result = requests.get(url, params=params)
        weather = result.json()

        bot.send_message(message.chat.id, "В городе " + str(weather["name"]) + " температура: " + str(
            int(weather["main"]['temp'])) + "\n" +
                         "Минимальная температура: " + str(float(weather['main']['temp_min'])) + "\n" +
                         "Скорость ветра: " + str(float(weather['wind']['speed'])) + "\n" +
                         "Давление: " + str(float(weather['main']['pressure'])) + "\n" +
                         "Влажность: " + str(int(weather['main']['humidity'])) + "%" + "\n" +
                         "Видимость: " + str(weather['visibility']) + "\n" +
                         "Описание: " + str(weather['weather'][0]["description"]) + "\n")

    except:
        bot.send_message(message.chat.id, "Город " + city_name + " не найден")


if __name__ == '__main__':
    bot.polling(none_stop=True)
