from email.mime import image
import os
from telegram import Bot, ReplyKeyboardMarkup
from telegram.ext import Updater, Filters, MessageHandler, CommandHandler
from dotenv import load_dotenv
import requests
import time
import asyncio
from html_parser import parse


load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = os.getenv('URL_CAT')
URL_WEATHER = os.getenv('WEATHER_URL')
URL_YAHOO = os.getenv('YAHOO_URL')
bot = Bot(token=TELEGRAM_TOKEN)


def weather_forecast():
    querystring = {"aggregateHours":"24","location":"Toronto,ca","contentType":"json","unitGroup":"us","shortColumnNames":"0"}
    headers = {
        "X-RapidAPI-Key": "61009a916bmsh83fbaf5cb967a55p1e2a76jsnd88782f867f3",
        "X-RapidAPI-Host": "visual-crossing-weather.p.rapidapi.com"
    }
    try:
        response = requests.request("GET", URL_WEATHER, headers=headers, params=querystring)
        print(response.json()['locations']['Toronto,ca']['currentConditions'])
    except Exception as error:
        print(error)
        new_url = URL_WEATHER
        response = requests.request("GET", new_url, headers=headers, params=querystring)
    response = response.json()['locations']['Toronto,ca']['currentConditions']
    temperature = round((float(response['temp']) - 32) * (5 / 9), 0)
    visibility = response['visibility']
    sunrise = time.strptime(response['sunrise'].rsplit('-', 1)[0], '%Y-%m-%dT%H:%M:%S')
    t_sunrise = time.strftime('%b %d %Y %H:%M:%S', sunrise)
    sunset = time.strptime(response['sunset'].rsplit('-', 1)[0], '%Y-%m-%dT%H:%M:%S')
    t_sunset = time.strftime('%b %d %Y %H:%M:%S', sunset)
    icon = response['icon']
    weather_response = (
        f'The temperature today - {temperature}°C, {icon}\n'
        f'The expected visibility - {visibility}\n'
        f'The sunrise {t_sunrise}\n'
        f'The sunset {t_sunset}\n')
    return weather_response


def get_forecast(update, context):
    chat = update.effective_chat
    context.bot.send_message(
        chat.id, weather_forecast()
    )


def new_img():
    try:
        response_1 = requests.get(URL)
    except Exception as error:
        print(error)
        new_url = 'https://api.thedogapi.com/v1/images/search'
        response_1 = requests.get(new_url)
    response_1 = response_1.json()
    random_cat_url = response_1[0].get('url')
    return random_cat_url


def get_cat(update, context):
    chat = update.effective_chat
    context.bot.send_photo(
        chat.id, new_img()
    )


def handler_message(update, context):
    # Get info from chat and save it in new variable.
    chat = update.effective_chat
    context.bot.send_message(chat_id=chat.id,
                             text='Hi, I am a news Bot! I am ready to feet you with the hottest news.')


def yahoo_news(update, context):
    chat = update.effective_chat
    try:
        soup = parse(URL_YAHOO)
        print(soup)
    except Exception as error:
        raise Exception(f'You have a problem here - {error}!')
    context.bot.send_message(chat_id=chat.id, text=[el for el in soup])


def news(update, context):
    # In response to the /news command
    #  will appear another buttons with sites you want
    # see news
    chat = update.effective_chat
    name = update.message.chat.first_name
    buttons = ReplyKeyboardMarkup(
        [
            ['Dailymail', 'CNN'],
            ['BBS', 'Yahoo!']
        ])
    context.bot.send_message(chat_id=chat.id,
                             text='{}, please choose the sourse you want to see news from'.format(name),
                             reply_markup=buttons)


def wake_up(update, context):
    # In response to the /start command
    #  will send the message 'Thank you for turning me on'
    chat = update.effective_chat
    name = update.message.chat.first_name
    buttons = ReplyKeyboardMarkup(
        [
            ['/weater', 'order a pancake'],
            ['/news', '/want_smth_cute']
        ])
    context.bot.send_message(chat_id=chat.id,
                             text='Thank you for turning me on {}'.format(name),
                             reply_markup=buttons)


def main():
    updater = Updater(token=TELEGRAM_TOKEN)
    # chat_id = CHAT_ID
    var = ['Yahoo!']
    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(CommandHandler('want_smth_cute', get_cat))
    updater.dispatcher.add_handler(CommandHandler('weater', get_forecast))
    updater.dispatcher.add_handler(CommandHandler('news', news))
    updater.dispatcher.add_handler(MessageHandler(Filters.text(var), yahoo_news))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handler_message))

    updater.start_polling(poll_interval=5.0)
    '''The bot will work until you press Ctrl-C'''
    updater.idle()


if __name__ == '__main__':
    main()
