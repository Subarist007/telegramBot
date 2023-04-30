import requests
import asyncio

import pprint
from translate import Translator
from environs import Env

from aiogram import Bot, Dispatcher, executor, types

import psycopg2 # Импортируем модуль для работы с DataBase
from config import host, user, password, db_name # Импортируем данные из config


env = Env()
env.read_env()

BOT_TOKEN = env('TOKEN')

#Создаем объекты бота и диспетчера
bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher(bot)

#Словарь соответствия знаков зодиака
sign_zodiac = {'овен': 'aries',
			   'телец': 'taurus',
			   'близнецы': 'gemini',
			   'рак': 'cancer',
			   'лев': 'leo',
			   'дева': 'virgo',
			   'весы': 'libra',
			   'скорпион': 'scorpio',
			   'стрелец': 'sagittarius',
			   'козерог': 'capricorn',
			   'водолей': 'aquarius',
			   'рыбы': 'pisces'
			   }

#Хэндлер обрабатывающий команду "/start"
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
	try:
		# Подключение к базе данных
		connection = psycopg2.connect(
			host=host,
			user=user,
			password=password,
			database=db_name
		)
		connection.autocommit = True

		# Добавление данных о пользователе
		with connection.cursor() as cursor:
			idi = (str(message.from_user['id']),)

			print(idi)
			cursor.execute("""SELECT id_user FROM users WHERE id_user = %s""", (idi))
			data = cursor.fetchone()
			print(data)

			if data is None:
				cursor.execute(
					"""INSERT INTO users (id_user, first_name, last_name) VALUES
					(%s,%s,%s);""", (message.from_user["id"], message.from_user["first_name"], message.from_user["last_name"])
				)
			else:
				print('Такой пользователь уже существует')
			print("[INFO] Data was successfully inserted")
	except Exception as _ex:
		print("[INFO] Error while working with PostgreSQL", _ex)
	finally:
		if connection:
			connection.close()
			print("[INFO] PostgreSQL connection closed")

	await message.answer("Привет!\nЧтобы узнать свой гороскоп на сегодня\nнапиши свой знак зодиака")

#Хэндлер обрабатывающий команду "/help"
@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
	await message.answer("Напишите название своего\nзнака зодиака, чтобы получить\nгороскоп на сегодня")

#Хэндлер обрабатывающий знаки гороскопа
@dp.message_handler()
async def process_horoscope(message: types.Message):
	translator = Translator(to_lang="ru")
	url = "https://sameer-kumar-aztro-v1.p.rapidapi.com/"
	def sign_types(message = message.text.lower()):
		if message in sign_zodiac:
			sign: str = sign_zodiac[message]
		else:
			return False
		return sign

	if sign_types():
		querystring = {"sign": sign_types(), "day": "today"}
		headers = {
			"X-RapidAPI-Key": env('KEY'),
			"X-RapidAPI-Host": env('HOST')
		}
		response = requests.request("POST", url, headers=headers, params=querystring)
		translation = translator.translate(response.json()['description'])

		await message.answer(f'{message.text.upper()}: {translation}')
		print(message.message_id, message.from_user, message.text)
	else:
		await message.answer("Правильно введите название знака зодиака")
		print(message.message_id, message.from_user, message.text)

# pprint.pprint(response.json())

if __name__ == '__main__':
	try:
		# Подключение к базе данных
		connection = psycopg2.connect(
			host=host,
			user=user,
			password=password,
			database=db_name
		)
		connection.autocommit = True

		# Создание новой таблицы
		with connection.cursor() as cursor:
			cursor.execute(
				"""CREATE TABLE IF NOT EXISTS users (
				id serial PRIMARY KEY,
				id_user varchar (50) NOT NULL,
				first_name varchar (50) NOT NULL,
				last_name varchar (50) );"""
			)

			print("[INFO] Table created successfully")
	except Exception as _ex:
		print("[INFO] Error while working with PostgreSQL", _ex)
	finally:
		if connection:
			connection.close()
			print("[INFO] PostgreSQL connection closed")
	executor.start_polling(dp, skip_updates=True)
