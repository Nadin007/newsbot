import logging
import os
import time

from html_parser import parse

import httpx
from dotenv import load_dotenv
from telegram import Bot, Poll, ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, PollAnswerHandler, PollHandler,
                          filters)

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = os.getenv('URL_CAT')
URL_WEATHER = os.getenv('WEATHER_URL')
URL_YAHOO = os.getenv('YAHOO_URL')
bot = Bot(token=TELEGRAM_TOKEN)


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


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
    """Inform user about what this bot can do"""
    await update.message.reply_text(
        text=(
            'Hi, I am a news Bot! I am ready to feet you with the hottest news if you choose the command /news. '
            'Also you can select /poll to get a Poll, /quiz to get a Quiz or /preview'
            ' to generate a preview for your poll, '
            '/weater to get today\'s weather, /cute to see something cute'))


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
            ['BBS', 'Yahoo!', 'Back']
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
            ['/weater', '/poll'],
            ['/news', '/cute']
        ])
    await context.bot.send_message(
        chat_id=chat.id,
        text='Thank you for turning me on {}'.format(name),
        reply_markup=buttons)


async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a predefined poll"""
    questions = "What is the best day of the week?"
    answers = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    message = await context.bot.send_poll(
        update.effective_chat.id,
        questions,
        answers,
        is_anonymous=False,
        allows_multiple_answers=True,
    )
    # Save some info about the poll the bot_data for later use in receive_poll_answer
    payload = {
        message.poll.id: {
            "questions": questions,
            "message_id": message.message_id,
            "chat_id": update.effective_chat.id,
            "answers": answers,
        }
    }
    context.bot_data.update(payload)


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a predefined poll"""
    questions = "What is the capital of UK?"
    options = ["Bradford", "Cambridge", "London", "Bristol"]
    message = await update.effective_message.reply_poll(
        questions, options, type=Poll.QUIZ, correct_option_id=2
    )
    # Save some info about the poll the bot_data for later use in receive_quiz_answer
    payload = {
        message.poll.id: {"chat_id": update.effective_chat.id, "message_id": message.message_id}
    }
    context.bot_data.update(payload)


async def receive_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Close quiz after three participants took it"""
    # the bot can receive closed poll updates we don't care about
    if update.poll.is_closed:
        return
    if update.poll.total_voter_count == 3:
        try:
            quiz_data = context.bot_data[update.poll.id]
        # this means this poll answer update is from an old poll, we can't stop it then
        except KeyError:
            return
        await context.bot.stop_poll(quiz_data["chat_id"], quiz_data["message_id"])


async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize a users poll vote"""
    answer = update.poll_answer
    answered_poll = context.bot_data[answer.poll_id]
    try:
        questions = answered_poll["questions"]
    # this means this poll answer update is from an old poll, we can't do our answering then
    except KeyError:
        return
    selected_options = answer.option_ids
    answer_string = ""
    for question_id in selected_options:
        if question_id != selected_options[-1]:
            answer_string += questions[question_id] + " and "
        else:
            answer_string += questions[question_id]
    await context.bot.send_message(
        answered_poll["chat_id"],
        f"{update.effective_user.mention_html()} feels {answer_string}!",
        parse_mode=ParseMode.HTML,
    )
    answered_poll["answers"] += 1
    # Close poll after three participants voted
    if answered_poll["answers"] == 3:
        await context.bot.stop_poll(answered_poll["chat_id"], answered_poll["message_id"])


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    # chat_id = CHAT_ID
    var = ['Yahoo!']
    application.add_handler(CommandHandler('start', wake_up))
    application.add_handler(CommandHandler('cute', get_cat))
    application.add_handler(CommandHandler('weater', get_forecast))
    application.add_handler(CommandHandler('news', news))
    application.add_handler(CommandHandler("poll", poll))
    application.add_handler(CommandHandler("quiz", quiz))
    application.add_handler(PollAnswerHandler(receive_poll_answer))
    application.add_handler(PollHandler(receive_quiz_answer))
    application.add_handler(MessageHandler(filters.Text(var), yahoo_news))
    application.add_handler(MessageHandler(filters.Text(), handler_message))

    '''The bot will work until you press Ctrl-C'''
    application.run_polling(poll_interval=5.0)


if __name__ == '__main__':
    main()
