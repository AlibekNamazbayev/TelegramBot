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

class User:
    def __init__(self, city):
        self.city = city
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

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    conn = CXOracle('hr', 'hr')
    res = conn.select_cities()
    cities = []
    for i in range(len(res)):
        cities.append(res[i][1])
    callbacks = []
    for i in range(len(res)):
        callbacks.append('c'+str(res[i][0]))
    msg = bot.send_message(message.chat.id, """\
        Hi there, I am Example bot.
        What's your city?
        """, reply_markup=create_inline_keyboard(cities, callbacks))

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    chat_id = call.message.chat.id
    if call.data[0] == 'c':
        city_id = int(call.data[1])
        user = User(city_id)
        user_dict[chat_id] = user
        msg= bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
            text="When is your birthday? Write in format: 31/12/2019")
        bot.register_next_step_handler(msg, process_birthdate_step)
    elif call.data[0] == 's':
        subject_id = int(call.data[1])
        user = user_dict[chat_id]
        user.subject= subject_id
        msg= bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
            text="How many tenge you can pay per year?")
        bot.register_next_step_handler(msg, process_fininfo_step)

def process_birthdate_step(message):
    try:
        chat_id = message.chat.id
        birthdate = message.text
        try:
            birthdate = datetime.strptime(birthdate, '%d/%m/%Y')
        except Exception as e:
            msg = bot.reply_to(message, 'Please write according to format. When is your birthday?')
            bot.register_next_step_handler(msg, process_birthdate_step)
            return
        user = user_dict[chat_id]
        user.birthdate = birthdate
        msg = bot.reply_to(message, 'What is your band score in UNT?')
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
            subjects.append(str(res[i][3]))
        callbacks = []
        for i in range(len(res)):
            callbacks.append('s'+str(res[i][0]))

        bot.send_message(chat_id, "Subject ", reply_markup=create_inline_keyboard(subjects, callbacks))


def process_fininfo_step(message):
    # try:
        chat_id = message.chat.id
        fininfo = message.text
        user = user_dict[chat_id]
        user.fininfo = fininfo
        conn = CXOracle('hr', 'hr')
        bot.send_message(chat_id, 'City: ' + str(user.city) + '\n'
                                  'Birthdate: ' + str(user.birthdate) + '\n'
                                  'Score: ' + user.score + '\n'
                                  'Subject: ' + str(user.subject) + '\n'
                                  'Financial info: ' + user.fininfo)


        cursor = conn.select_university_specialty(user.city, user.score,
            user.subject, user.fininfo)
   
        count = len(cursor)
        a = '{0} places found:\n\n'.format(count)
        b = 1
        for i in cursor:
            a += '{0}. University: {1}\n'.format(b, i[0])
            a += 'Specialty: {}\n\n'.format(i[1])
            b += 1
        bot.send_message(chat_id, a)
    # except Exception as e:
         # bot.reply_to(message, 'oooops')

# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
bot.enable_save_next_step_handlers(delay=2)

# Load next_step_handlers from save file (default "./.handlers-saves/step.save")
# WARNING It will work only if enable_save_next_step_handlers was called!
bot.load_next_step_handlers()

bot.polling()


import cx_Oracle 


class CXOracle:

    def __init__(self, username, password):

        self.connection = cx_Oracle.connect('{}/{}@localhost'.format(username, password))
        self.cursor = self.connection.cursor()


    def select_cities(self):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM cities').fetchall()

    def select_city(self, city):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM cities WHERE ID = ? ', (city,)).fetchall()[0]

    def select_subject(self, subject):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM subjects WHERE ID = ? ', (subject,)).fetchall()[0]

    def select_subjects(self):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM subjects').fetchall()

    def select_university_specialty(self, city, score, subject, fininfo):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            st = '''SELECT univercity.uni_eng, specialties.name_eng,
                specialties.sub_id, univercity.city_id FROM uni_spe 
                INNER JOIN univercity ON uni_spe.uni_id=univercity.id 
                INNER JOIN specialties ON uni_spe.spe_id=specialties.code
                WHERE sub_id={} and city_id={}'''.format(str(subject), str(city))
            return self.cursor.execute(st).fetchall()

    def select_single_specialty(self, rownum):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('SELECT * FROM specialties WHERE id = ?', (rownum,)).fetchall()[0]

    def count_universities(self):
        """ Считаем количество строк """
        with self.connection:
            result = self.cursor.execute('SELECT * FROM universities').fetchall()
            return len(result)

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()
