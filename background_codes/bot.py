# -*- coding: utf-8 -*-

import logging
import telebot
from telebot import types
from datetime import datetime
from dateutil import parser
import config
from db import CXOracle
import pdb

bot = telebot.TeleBot(config.token)
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.
user_dict = {}

languages = config.languages
db_localization = config.db_localization

languages_short = ['en', 'ru', 'kz']
db_languages = {
    'en' : [ 'uni_eng', 'name_eng' ], 
    'ru' : [ 'uni_ru', 'name_rus' ] ,
    'kz' : [ 'uni_kz', 'name_kz' ]
    }

class User:
    def __init__(self):
        self.city = None
        self.birthdate = None
        self.score = None
        self.subject = None
        self.fininfo = None
        self.lang = None


def create_inline_keyboard(words, callback_datas):
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    patients = dict(zip(callback_datas,words))
    kb = types.InlineKeyboardMarkup()
    for key in patients:
        kb.add(types.InlineKeyboardButton(text=patients[key], callback_data=key))

    return kb


def send_welcome(message):
    conn = CXOracle('hr', 'hr')
    res = conn.select_cities()
    cities = []
    chat_id = message.chat.id
    for i in range(len(res)):
        cities.append(res[i][languages[user_dict[message.chat.id].lang]])
    callbacks = []
    for i in range(len(res)):
        callbacks.append('c'+str(res[i][0]))
    msg = bot.send_message(message.chat.id, db_localization[ user_dict[chat_id].lang ][0], reply_markup=create_inline_keyboard(cities, callbacks))

@bot.message_handler(commands=['help', 'start'])
def bot_start(message):
    kb = create_inline_keyboard( ['English', 'Russian', 'Kazakh'], languages_short )

    bot.send_message( message.chat.id, 'Smart Graduate', reply_markup = kb )

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    if call.data[0] == 'c':
        city_id = int(call.data[1])
        user = user_dict[chat_id]
        user.city = city_id
        user_dict[chat_id] = user
        msg= bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
            text=db_localization[ user_dict[chat_id].lang ][1])
        bot.register_next_step_handler(msg, process_birthdate_step)
    elif call.data[0] == 's':
        subject_id = int(call.data[1])
        user = user_dict[chat_id]
        user.subject= subject_id
        msg= bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
            text=db_localization[ user_dict[chat_id].lang ][2])
        bot.register_next_step_handler(msg, process_fininfo_step)
    elif call.data in languages_short:
        if chat_id not in user_dict:
            user = User()
            user.lang = call.data
            user_dict[chat_id] = user
        else:
            user_dict[chat_id].lang = call.data
        send_welcome(call.message)

def process_birthdate_step(message):
    try:
        chat_id = message.chat.id
        birthdate = message.text
        try:
            birthdate = datetime.strptime(birthdate, '%d/%m/%Y')
        except Exception as e:
            msg = bot.reply_to(message, db_localization[ user_dict[chat_id].lang ][3])
            bot.register_next_step_handler(msg, process_birthdate_step)
            return
        user = user_dict[chat_id]
        user.birthdate = birthdate
        msg = bot.reply_to(message, db_localization[ user_dict[chat_id].lang ][4])
        bot.register_next_step_handler(msg, process_score_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_score_step(message):
        chat_id = message.chat.id
        score = message.text
        user = user_dict[chat_id]
        user.score = score
        conn = CXOracle('hr', 'hr')
        res = conn.select_subjects()
        subjects = []
        for i in range(len(res)):
            subjects.append(str(res[i][languages[user_dict[message.chat.id].lang]]))
        callbacks = []
        for i in range(len(res)):
            callbacks.append('s'+str(res[i][0]))

        bot.send_message(chat_id, db_localization[ user_dict[chat_id].lang ][5], reply_markup=create_inline_keyboard(subjects, callbacks))


def process_fininfo_step(message):
    # try:
        chat_id = message.chat.id
        fininfo = message.text
        user = user_dict[chat_id]
        user.fininfo = fininfo
        conn = CXOracle('hr', 'hr')
        data_to_send = db_languages[ user_dict[chat_id].lang ]
        bot.send_message(chat_id, db_localization[ user_dict[chat_id].lang ][6] + str(user.city) + '\n' +
                                  db_localization[ user_dict[chat_id].lang ][7] + str(user.birthdate) + '\n' + 
                                  db_localization[ user_dict[chat_id].lang ][8] + user.score + '\n' + 
                                  db_localization[ user_dict[chat_id].lang ][9] + str(user.subject) + '\n' + 
                                  db_localization[ user_dict[chat_id].lang ][10] + user.fininfo)


        cursor = conn.select_university_specialty(data_to_send[0], data_to_send[1], user.city, user.score,
            user.subject, user.fininfo)
   
        count = len(cursor)
        a = '{0} {1}\n'.format(count, db_localization[ user_dict[chat_id].lang ][11])
        b = 1
        for i in cursor:
            a += '{0}. {1} {2}\n'.format(b,db_localization[ user_dict[chat_id].lang ][12], i[0])
            a += '{} {}\n\n'.format(db_localization[ user_dict[chat_id].lang ][13], i[1])
            b += 1
        bot.send_message(chat_id, a)

bot.enable_save_next_step_handlers(delay=2)

bot.load_next_step_handlers()

bot.polling()