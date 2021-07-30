from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, location
from aiohttp.client import request

#some code

# основное меню
kb1 = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
geo_but_kb1 = KeyboardButton('Я на месте 🗺', request_location=True)
info_but_kb1 = KeyboardButton('Информация ℹ')
kb1.add(geo_but_kb1, info_but_kb1)


ikb2 = InlineKeyboardMarkup(resize_keyboard=True)
car0_but_ikb2 = InlineKeyboardButton('Никого', callback_data='car0')
car1_but_ikb2 = InlineKeyboardButton('1-2 машины', callback_data='car1')
car2_but_ikb2 = InlineKeyboardButton('Подожду...', callback_data='car2')
car3_but_ikb2 = InlineKeyboardButton('Час точно', callback_data='car3')
car4_but_ikb2 = InlineKeyboardButton('Жопа!', callback_data='car4')
car5_but_ikb2 = InlineKeyboardButton('Жесть!!!', callback_data='car5')
ikb2.add(car0_but_ikb2, car1_but_ikb2, car2_but_ikb2, car3_but_ikb2, car4_but_ikb2, car5_but_ikb2)

# инлайн выбора региона
# пока что 7 и 5
ikb3 = InlineKeyboardMarkup(resize_keyboard=True)
reg7_but_ikb3 = InlineKeyboardButton('7️⃣ Минск', callback_data='reg7')
reg5_but_ikb3 = InlineKeyboardButton('5️⃣ Минская область', callback_data='reg5')
ikb3.add(reg5_but_ikb3, reg7_but_ikb3)


