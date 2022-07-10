import os
from telegram import Bot, ReplyKeyboardMarkup, Update
from telegram.ext import Application, filters, MessageHandler, CommandHandler, ContextTypes
from dotenv import load_dotenv
import httpx
import time
from html_parser import parse


load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = os.getenv('URL_CAT')
URL_WEATHER = os.getenv('WEATHER_URL')
URL_YAHOO = os.getenv('YAHOO_URL')
bot = Bot(token=TELEGRAM_TOKEN)


async def weather_forecast():
    querystring = {"aggregateHours":"24","location":"Toronto,ca","contentType":"json","unitGroup":"us","shortColumnNames":"0"}
    headers = {
        "X-RapidAPI-Key": "61009a916bmsh83fbaf5cb967a55p1e2a76jsnd88782f867f3",
        "X-RapidAPI-Host": "visual-crossing-weather.p.rapidapi.com"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request("GET", URL_WEATHER, headers=headers, params=querystring)
        print(response.json()['locations']['Toronto,ca']['currentConditions'])
    except Exception as error:
        print(error)
        new_url = URL_WEATHER
        async with httpx.AsyncClient() as client:
            response = await client.request("GET", new_url, headers=headers, params=querystring)
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


async def get_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await context.bot.send_message(
        chat.id, await weather_forecast()
    )


async def new_img():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(URL)
    except Exception as error:
        print(error)
        new_url = 'https://api.thedogapi.com/v1/images/search'
        async with httpx.AsyncClient() as client:
            response = client.get(new_url)
    response_json = response.json()
    random_cat_url = response_json[0].get('url')
    return random_cat_url


async def get_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await context.bot.send_photo(
        chat.id, await new_img()
    )


async def handler_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get info from chat and save it in new variable.
    chat = update.effective_chat
    await context.bot.send_message(
        chat_id=chat.id,
        text='Hi, I am a news Bot! I am ready to feet you with the hottest news.')


async def yahoo_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    try:
        async with httpx.AsyncClient() as client:
            html_text = (await client.get(URL_YAHOO)).text
        soup = parse(html_text)
    except Exception as error:
        raise Exception(f'You have a problem here - {error}!')
    for el in soup:
        await context.bot.send_message(chat_id=chat.id, text=el)


async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await context.bot.send_message(
        chat_id=chat.id,
        text='{}, please choose the sourse you want to see news from'.format(name),
        reply_markup=buttons)


async def wake_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # In response to the /start command
    #  will send the message 'Thank you for turning me on'
    chat = update.effective_chat
    name = update.message.chat.first_name
    buttons = ReplyKeyboardMarkup(
        [
            ['/weater', 'order a pancake'],
            ['/news', '/want_smth_cute']
        ])
    await context.bot.send_message(
        chat_id=chat.id,
        text='Thank you for turning me on {}'.format(name),
        reply_markup=buttons)


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    # chat_id = CHAT_ID
    var = ['Yahoo!']
    application.add_handler(CommandHandler('start', wake_up))
    application.add_handler(CommandHandler('want_smth_cute', get_cat))
    application.add_handler(CommandHandler('weater', get_forecast))
    application.add_handler(CommandHandler('news', news))
    application.add_handler(MessageHandler(filters.Text(var), yahoo_news))
    application.add_handler(MessageHandler(filters.Text(), handler_message))

    '''The bot will work until you press Ctrl-C'''
    application.run_polling(poll_interval=5.0)


if __name__ == '__main__':
    main()
