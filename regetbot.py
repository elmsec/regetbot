"""
    Author:     E. Can Elma
    Date:       9 Apr. 2018
    Github:     @canelma
    Twitter:    @_canelma

     A Telegram bot to get recom-,
     mentations for TV shows, aut-
     hors, bands, games, books,
     movies; based on your likes.
"""

import os
import sys
import time
import logging
from tdclass import TasteDive
from secrets import _secret
# from dbhelper import DBHelper
from database import DB, User
from datetime import datetime
from threading import Thread
from functools import wraps
from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    # ReplyKeyboardRemove,
    )
from telegram.ext import (
    Updater,
    Filters,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    # RegexHandler,
    # ConversationHandler
    )
# from telegram.error import (
#     TelegramError, Unauthorized, BadRequest,
#     TimedOut, ChatMigrated, NetworkError
#     )

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

# create logger
logger = logging.getLogger(__name__)

# fh handler
fh = logging.FileHandler('all.log')
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

# list of admins to restrict other users from unauthorized functions
LIST_OF_ADMINS = [_secret['admin_id']]

time_limit = 3600
user_request_limit = 10

help_text = (
    '<b>What are you?</b>\n'
    'I can help you discover new musics, movies, books, authors, games or '
    'TV shows and series. You give me one thing and you can get a lot of '
    'things!\n\n'
    '<b>Make the results efficient</b>\n'
    'If you want to limit the result type to one type of contents, '
    'let\'s say "movies", you can simply do that. Go to /settings, then '
    'touch the "Result Type", choose a type. Or even you can choose the '
    'always ask option to get an option menu when you search for something.'
    '\n\n'
    '<b>That will hurt</b>\n'
    'I\'m not Google. I mean, when you type something wrong, I can\'t '
    'understand what you mean. Uh, that hurts me. 🙈 So, please be careful '
    'about typos.\n\n'
    'Don\'t forget to check /tips!'
)

tips_text = (
    '<b>Useful Hints and Implementations</b>\n'
    'Here are good implementations to get better results. Only for you!\n\n'
    '🔘 <b>Multiple keyword at the same time</b>\n'
    'If you want to search with multiple things, let\'s say "Matrix" and '
    '"Fight Club", to get related things to both of them, you can use '
    'commas to use these inputs together.\n\n'
    '<b>For example:</b> <i>Matrix, Fight Club</i>\n\n'
    '🔘 <b>Specify the type of the thing</b>\n'
    'For example, Fight Club is the name of a book and also of a movie. '
    'But, how do you tell me which one of them fits to your case? You can use '
    '"band:", "movie:", "show:", "book:", "author:" or "game:" operators.\n\n'
    '<b>For example:</b> <i>book:Fight Club, movie:Matrix</i>'
)

# settings text and keyboard to use it many times in related sections
settings_text = (
    'You can manage your settings here. Let me explain what they do.\n\n'
    '<b>Max Results</b>\n'
    'This setting defines the maximum number of recommendations. '
    'You can get n result with this setting.\n\n'
    '<b>Result Type</b>\n'
    'Let\'s say you entered a movie name and there are books, movies and '
    'series related it. I\'ll show you all of them. But you can choice the '
    'result type so I show you only this type of results.\n\n'
    '<b>Remainings</b>\n'
    'This will tell you the remaining request rights of yours.\n\n'
    '<b>Reset All</b>\n'
    'This resets your configuration.'
)
settings_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('Max Results', None, 'set:max_result'),
        InlineKeyboardButton('Result Type', None, 'set:result_type'),
    ],
    [
        InlineKeyboardButton('Remainings', None, 'set:remainings'),
        InlineKeyboardButton('Reset All', None, 'set:reset_all'),
    ]
])


def restricted(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            logger.critical(
                "Unauthorized access denied for {}.".format(user_id))
            return
        return func(bot, update, *args, **kwargs)
    return wrapped


def start(bot, update, args):
    try:
        user = update.effective_user
        new_user = User(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        new_user.save()
    except Exception as e:
        logger.error(e)
    finally:
        message = (
            '👋 Hi, <b>{}</b>!\n\n'
            'I can suggest good things according to your favorite '
            'musics/bands, movies, TV shows/series, books, authors and games.'
            '\n\n'
            '<b>Do you need help?</b>\n'
            'If you want to know how to get recommendations, type /help.\n\n'
            '<b>Do you need extra tips?</b>\n'
            'Here is /tips for you.'
        )
        update.message.reply_html(message.format(user.first_name))


def help_me(bot, update):
    update.message.reply_html(help_text)


def tips(bot, update):
    update.message.reply_html(tips_text)


def auto_fill_up(bot, job):
    user_data = job.context['user_data']
    user_id = job.context['user_id']

    try:
        user = User.get(telegram_id=user_id)

        user.total_request = 0
        user.timestamp = datetime.now()
        user.save()
    except Exception as e:
        logger.error(e)

    if user_data['fill_up_notify'] is True:
        user_data['fill_up_notify'] = False
        message = (
            '✅ The time has come!\n'
            'Your credits has been filled up for 10 new requests.'
            )
        bot.send_message(chat_id=user_id, text=message)


def answer_user(bot, update, job_queue, user_data=None, result_type=None):
    user_id = update.effective_user.id
    user = User.get_or_none(telegram_id=user_id)

    if not user:
        logger.warning('User not found.')
        return

    user_total_requests = user.total_request + 1  # +1 for this request
    query = user_data['query']
    update_message = update.message or update.callback_query.message

    # get result type from database
    user_result_type = result_type or user.result_type

    # request limit control
    time_now = datetime.now()
    user_past_time = int((time_now - user.timestamp).total_seconds())

    if user_total_requests >= user_request_limit:
        remaining_time = (time_limit - user_past_time)

        if not job_queue.get_jobs_by_name(
                '{}_auto_fill_up'.format(str(user_id))):
            user.timestamp = time_now
            user.save()
            remaining_time = time_limit
            job_queue.run_once(
                auto_fill_up,
                remaining_time,
                context={'user_id': user_id, 'user_data': user_data},
                name='{}_auto_fill_up'.format(str(user_id)))
            user_data['fill_up_notify'] = False

        mins, secs = divmod(int(remaining_time), 60)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                'Yes, notify me! 😎', callback_data='notify')],
            [InlineKeyboardButton(
                'No, thanks. 🙄', callback_data='cancel')],
        ])

        message = (
            '🥀 <b>Sorry. </b> You can do only 10 requests per hour.\n\n'
            '⏱ Come back {}min {}sec later. '
            'Or if you want, I\'ll call you when the time has come.'
        ).format(mins, secs)

        if user_total_requests > user_request_limit:
            if update.message is None:
                return bot.edit_message_text(
                    text=message,
                    chat_id=update_message.chat_id,
                    message_id=user_data['message_id'],
                    parse_mode='HTML',
                    reply_markup=keyboard)
            else:
                return update_message.reply_text(
                    message, reply_markup=keyboard,
                    parse_mode='HTML'
                    )
    elif user_total_requests < user_request_limit and \
            user_past_time >= time_limit:
        user_total_requests = 1  # there is already a line to use this variable
        user.timestamp = time_now
        user.save()

    if update.callback_query:
        sent_message = bot.edit_message_text(
            text='⌛️ Loading..',
            chat_id=update_message.chat_id,
            message_id=update_message.message_id
        )
    else:
        sent_message = update_message.reply_text(
            '⌛️ Loading..'
        )

    tastedive = TasteDive(_secret['tastedive_key'])
    user.total_request = user_total_requests
    user.save()

    no_error = False
    try:
        result = tastedive.get_similar(
            query=query,
            info=user.show_info,
            verbose=user.show_info,
            limit=user.max_result,
            q_type=user_result_type or '',
        )

        result = tastedive.prettify(*result)
        message = '👌🏻 Successful.'
        no_error = True
    except ValueError as e:
        message = e.__str__()
    except KeyError as e:
        logger.error(e)
        message = 'Something bad happened. Try again later.'
    finally:
        bot.edit_message_text(
            text=message,
            chat_id=update_message.chat_id,
            message_id=sent_message.message_id
        )

    if 'result' not in locals():
        return

    keyboard = [
        [
            InlineKeyboardButton('💾 Save', callback_data='save_that'),
            InlineKeyboardButton(
                '⭐️⭐️⭐️⭐️⭐️', url='https://t.me/tlgrmcbot?start=regetbot-bot')
        ]
    ]

    if no_error:
        update_message.reply_text(
            result,
            parse_mode='HTML',
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


def text_messages(bot, update, job_queue, user_data):
    query = update.message.text
    user_id = update.effective_user.id
    user = User.get_or_none(telegram_id=user_id)
    ask_or_not = user.result_type == 'always_ask' or None

    if not user:
        logger.warning('User not found.')
        return

    user_data['query'] = query

    if ask_or_not is None:
        return answer_user(
            bot, update, job_queue=job_queue, user_data=user_data)

    types = [
        'all', 'music', 'movies', 'shows', 'books', 'authors', 'games']
    buttons = [
        InlineKeyboardButton(
            types[i].capitalize(),
            callback_data='search:' + types[i],
        ) for i in range(len(types))
    ]
    keyboard = [
        buttons[:1],
        buttons[1:3],
        buttons[3:5],
        buttons[5:],
    ]

    edit_text = 'What kind of recommendations do you want to get?'
    sent_message = update.message.reply_text(
        edit_text, reply_markup=InlineKeyboardMarkup(keyboard))

    if user_data.get('message_id'):
        try:
            bot.edit_message_text(
                text='Old request.',
                chat_id=update.message.chat_id,
                message_id=user_data['message_id']
            )
        except Exception:
            logger.warning('Old message could not be edited.')

    user_data['message_id'] = sent_message.message_id


def get_settings(bot, update, user_data):
    global settings_keyboard
    message = settings_text

    # sent settings message
    sent_message = update.message.reply_html(
        message,
        reply_markup=settings_keyboard
    )

    # if there is already a keyboard contains settings buttons
    if user_data.get('settings_msg'):
        message_id = user_data.pop('settings_msg')
        # remove old settings keyboard
        try:
            bot.edit_message_text(
                text=settings_text,
                chat_id=update.message.chat_id,
                message_id=message_id,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.info(e)

    # save the message id of the settings message to the user_data
    user_data['settings_msg'] = sent_message.message_id


def search_callback(bot, update, job_queue, user_data):
    query = update.callback_query
    result_type = query.data.split(':')[1]

    return answer_user(
        bot, update, job_queue=job_queue,
        user_data=user_data, result_type=result_type)


def callbacks(bot, update, user_data, job_queue):
    query = update.callback_query
    markup = None
    msg_text = query.message.text

    if query.data == 'settings':
        query.answer('')
        edit_text = settings_text
        markup = settings_keyboard
    elif query.data == 'notify':
        query.answer('✅ Reminder has set.')
        edit_text = msg_text.find('Or if you want')
        edit_text = msg_text[:edit_text] + (
            "<b>I'll call you when the time has come.</b>"
        )
        user_data['fill_up_notify'] = True
    elif query.data == 'cancel':
        edit_text = msg_text
    elif query.data == 'save_that':
        query.answer('✅ Successfully saved.')
        edit_text = query.message.text_html_urled
        edit_text += '\n\n────────\n\n✅ <b>Saved List:</b> #save_for_later\n\n'
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton('✅ Saved', callback_data='saved_that'),
                InlineKeyboardButton(
                    '⭐️⭐️⭐️⭐️⭐️', url='https://t.me/storebot?start=regetbot')
            ]
        ])
    elif query.data == 'saved_that':
        query.answer('❌ Successfully removed.')
        edit_text = query.message.text_html_urled
        find_to_replace = edit_text.find('────────', -300)
        edit_text = edit_text[:find_to_replace]
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton('💾 Save', callback_data='save_that'),
                InlineKeyboardButton(
                    '⭐️⭐️⭐️⭐️⭐️', url='https://t.me/storebot?start=regetbot')
            ]
        ])

    bot.edit_message_text(
        text=edit_text,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=markup or None,
        parse_mode='HTML',
        disable_web_page_preview=True
    )


def setting_callbacks(bot, update, job_queue):
    query = update.callback_query
    setting = query.data.split(':')[1]
    user_id = update.effective_user.id
    user = User.get_or_none(telegram_id=user_id)
    keyboard = list()

    if not user:
        logger.warning('User not found.')
        return

    if setting == 'max_result':
        max_result = user.max_result
        buttons = [
            InlineKeyboardButton(
                '{}'.format(i+1),
                callback_data='_set:max_result:{}'.format(i+1))
            for i in range(15)]
        keyboard = [
            buttons[:5],
            buttons[5:10],
            buttons[10:15],
            buttons[15:],
        ]
        edit_text = (
            '<b>MAXIMUM RESULTS</b>\n'
            'This setting defines the maximum number of recommendations.\n\n'
            'Your current max result value is <b>{}</b>.'
        ).format(max_result)
    elif setting == 'result_type':
        type_emoji = {
            'music': '🎤', 'movies': '🎬', 'shows': '📺',
            'books': '📖', 'authors': '👤', 'games': '🕹',
            'all': '📦'
        }
        types = [
            'all', 'music', 'movies', 'shows', 'books', 'authors', 'games']
        buttons = [
            InlineKeyboardButton(
                '❔ Always Ask', callback_data='_set:result_type:always_ask')
        ]
        buttons += [
            InlineKeyboardButton(
                type_emoji[types[i]] + ' ' + types[i].capitalize(),
                callback_data='_set:result_type:' + types[i],
            ) for i in range(len(types))
        ]
        keyboard = [
            buttons[:2],
            buttons[2:4],
            buttons[4:6],
            buttons[6:],
        ]
        result_type = user.result_type.replace('_', ' ')
        edit_text = (
            '<b>RESULT TYPE</b>\n'
            'This setting affects the results.\n'
            'You can define the type of your results here.\n\n'
            'Your current result type is <b>{}</b>.'
            ).format(result_type)
    elif setting == 'remainings':
        time_now = datetime.now()
        user_time = user.timestamp
        remaining_requests = 10-user.total_request
        remain = time_limit - (time_now-user_time).total_seconds()

        mins, secs = divmod(int(remain), 60)
        if remain < 0 and remaining_requests > 0:
            mins, secs = 0, 0

        edit_text = (
            '<b>DETAILS:</b>\n'
            'You may check your request limit here. Every user has 10 '
            'request right per hour to perform new query. \n\n'
            '💎 <b>Request credits:</b> {}\n'
            '⏱ <b>Time to fill up:</b> {}min {}sec'
            ).format(remaining_requests, mins, secs)
    elif setting == 'reset_all':
        keyboard = [
            [
                InlineKeyboardButton(
                    '😌 Yes, sure.', callback_data='_set:reset_all:sure'),
            ]
        ]
        edit_text = (
            '<b>RESET ALL SETTINGS</b>\n'
            'It will reset your maximum result and result type settings.\n\n'
            'Are you sure?'
            )

    keyboard += [[
        InlineKeyboardButton('🔙 Back', callback_data='settings')
    ]]

    query.answer('')
    bot.edit_message_text(
        text=edit_text,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


def change_settings(bot, update):
    global settings_keyboard
    query = update.callback_query
    setting = query.data.split(':')[1]
    value = query.data.split(':')[2]
    user_id = update.effective_user.id
    user = User.get_or_none(telegram_id=user_id)

    if not user:
        logger.warning('User not found.')
        return

    if setting == 'max_result':
        user.max_result = value
        edit_text = '✅ The max result has limited to {}.'.format(value)
    elif setting == 'result_type':
        user.result_type = value
        value = value.replace('_', ' ')
        edit_text = '✅ The result type has defined as {}.'.format(value)
    elif setting == 'reset_all':
        user.max_result = 5
        user.result_type = 'all'
        edit_text = '✅ Your settings have been reset.'
    user.save()

    keyboard = settings_keyboard

    query.answer(edit_text)
    bot.edit_message_text(
        text=settings_text,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    query.answer(edit_text)


@restricted
def manage_jobs(bot, update, job_queue, args):
    jobs = job_queue.jobs()

    message = 'No such an argument.'
    # want to run all waiting jobs to dont lose them?
    if args and args[0] == 'run_jobs' and len(jobs) > 0:
        for num, job in enumerate(jobs, 1):
            auto_fill_up(bot, job)
            time.sleep(1)
            total = num

        message = (
            '{}/{} jobs executed.\nYou can stop the script, users '
            'won\'t lose their queued jobs.'.format(len(jobs), total)
        )

    else:
        # or just wanna see how many jobs there?
        if len(jobs) > 0:
            # there are some jobs
            message = (
                'There are some jobs.\n'
                'To run them, write /admin_case run_jobs.'
            )
        else:
            message = (
                'There are no queued jobs.\n'
            )

    return update.message.reply_text(message)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    # Create the database and its necessary tables at startup
    DB.connect()
    DB.create_tables([User])

    # Create the Updater and pass it your bot's token.
    updater = Updater(_secret['bot_key'])

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    def stop_and_restart():
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    @restricted
    def restart(bot, update):
        update.message.reply_text('Bot is restarting...')
        Thread(target=stop_and_restart).start()

    dp.add_handler(CommandHandler('start', start, pass_args=True))
    dp.add_handler(CommandHandler('help', help_me))
    dp.add_handler(CommandHandler('tips', tips))

    dp.add_handler(CommandHandler(
        'settings', get_settings, pass_user_data=True))

    dp.add_handler(MessageHandler(
        Filters.text, text_messages, pass_job_queue=True, pass_user_data=True))

    dp.add_handler(CallbackQueryHandler(
        search_callback, pattern='^search:',
        pass_user_data=True, pass_job_queue=True))

    dp.add_handler(CallbackQueryHandler(
        setting_callbacks, pattern='^set:', pass_job_queue=True))

    dp.add_handler(CallbackQueryHandler(
        change_settings, pattern='^_set:'))

    dp.add_handler(CallbackQueryHandler(
        callbacks, pass_job_queue=True, pass_user_data=True))

    dp.add_handler(CommandHandler(
        'jobs', manage_jobs, pass_job_queue=True, pass_args=True))

    dp.add_handler(CommandHandler('r', restart))

    # log all errors
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
