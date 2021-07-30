from datetime import datetime
from os import waitpid
from typing import Text
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext, storage
from aiogram.types import reply_keyboard
from aiogram.types import message
from aiogram.types.inline_keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types.message import ParseMode
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging, json

# from attr import field
from config import TOKEN

import keyboards as kb
from work_db import Baza

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)
baza = Baza('db/charhadb.db')
chat = 'https://t.me/CharhaChat'

@dp.message_handler(commands=['start'])
# вывод меню по команде 'start'
async def start_command(message: types.Message):
    if baza.check_user(int(message.from_user.id)):
        cu, cs = baza.get_count_user_shops()
        greeting_message = '\nВ Боте зарегистрировано <B>' + str(cu) + '</B> 👨‍🚀 пользователей\n'
        greeting_message = greeting_message + 'Есть информация по <B>'+ str(cs) + '</B> 🏬 магазинам' 
        greeting_message = greeting_message + '\nОбсуждение :' + chat
    else:
        greeting_message = "\nВы впервые у нас. Бот находится в стадии тестирования. Все вопросы и замечания можно обсудить в " + chat
        greeting_message = greeting_message + 'Бот предоставлет информацию об очередях в торговых объектах г.Минска, а также готов принять Вашу информацию. \nСделайте выбор...👇'
        baza.add_user(int(message.from_user.id), message.from_user.username)
    await bot.send_message(message.from_user.id, 'Привет,' + str(message.from_user.username) + greeting_message, reply_markup=kb.kb1)


@dp.message_handler(lambda message: message.text == 'Информация ℹ')
# обработчик нажатия кнопки 'информация' и инлайн клава запроса региона
async def info_shops(message: types.Message):
    await bot.send_message(message.from_user.id, '🗺 Регион', reply_markup=kb.ikb3)


@dp.message_handler(content_types=['location'])
# обработчик нажатия 'location'
async def get_location(message: types.Message, state: FSMContext):
    #global g_shop_id # будем использовать глобальную переменную для передачи из второго меню id магазина
    await bot.delete_message(message.chat.id, message.message_id) # удаляем сообщение с локацией
    ikb = InlineKeyboardMarkup()
    data_shop = baza.search_shops(message.location['latitude'], message.location['longitude'])
    # TO DO много магазинов
    # print (data_shop)
    if data_shop != []:
        #TODO магазинов может быть много
        shop_button_ikb = InlineKeyboardButton('📌 ' + data_shop[0][2] + ' ' + data_shop[0][1], callback_data=data_shop[0][0])
        # название магазина и адрес лепим на кнопку
        ikb.add(shop_button_ikb)
        async with state.proxy() as td:
            td['shop_id'] = data_shop[0][0]
        await bot.send_message(message.from_user.id, 'По данным геолокации рядом с Вами', reply_markup=ikb)
        
    else:
        await bot.send_message(message.from_user.id, 'К сожалению 😡, в базе нет рядом магазинов, нажмите "Информация"', reply_markup=kb.kb1) 

@dp.callback_query_handler(lambda region: region.data.startswith('reg'))
# обрабатываем ввод региона и делаем инлайн клаву по сетям
async def save_reg_ikb3(callback_region: types.CallbackQuery, state:FSMContext):
    region_ok = int(callback_region.data[-1])
    async with state.proxy() as td:
        td['region'] = region_ok
    ikb4 = InlineKeyboardMarkup(resize_keyboard=True)
    list_net = baza.get_name_net(region_ok)
    check = 0
    net_but = []
    for i in list_net:
        check = check + 1
        cbd = 'net' + i[0]
        net_but.append(InlineKeyboardButton(i[0], callback_data=cbd)) # необходимо вывести в два столбика
        if check == 2:
            ikb4.add(net_but[0], net_but[1])
            net_but = []
            check = 0
    if net_but != []:
        ikb4.add(net_but[0])
    await bot.send_message(callback_region.from_user.id, 'Выбираем сеть', reply_markup=ikb4)

@dp.callback_query_handler(lambda net: net.data.startswith('net'))
# обрабатываем выбор сети и делаем инлайн клаву с адресами
async def save_net_ikb4(callback_net: types.CallbackQuery, state:FSMContext):
    net_ok = callback_net.data[3:]
    async with state.proxy() as td:
        region = td['region']
    ikb5 = InlineKeyboardMarkup(resizekeyboard=True)
    list_address = baza.get_address_shop(region, net_ok)
    for i in list_address:
        print (i)
        cbd = 'addr' + str(i[0])
        addr_but = InlineKeyboardButton(i[1], callback_data=cbd)
        ikb5.add(addr_but)
    await bot.send_message(callback_net.from_user.id, 'Выбираем адрес', reply_markup=ikb5)

@dp.callback_query_handler(lambda addr: addr.data.startswith('addr'))
# Обрабатываем адрес и выводим информацию
async def info_about_shop(callback_addr: types.CallbackQuery, state:FSMContext):
    id_shop = int(callback_addr.data[4:])
    baza.add_events(callback_addr.from_user.id, id_shop, 0, False)
    statistic = baza.get_statistic_shop(id_shop)
    print (statistic)
    info = baza.get_info_shop(id_shop)
    await bot.send_photo(callback_addr.from_user.id, str(info[5]), str(info[1]))
    answer_to_user = "📭 Адрес :" + str(info[0]) 
    time_to = "\n🕑 Время работы: <B>" + str(info[2]) + ".00 -" + str(info[3]) + ".00</B>"
    # time_to = time_to + "\n👩🏻‍🦳 Приемка: нет данных" пока убираем
    time_to = time_to + "\n🛌 Ночная приемка : "
    if info[4]:
        time_to = time_to + '✅'
    else:
        time_to = time_to + '🚫'
    time_to = time_to + "\n📋 График приемки : "
    if info[6]:
        time_to = time_to + '✅'
    else:
        time_to = time_to + '🚫'
    stroka = '\n🚚 <U>Прогноз по времени:</U>\n'
    if statistic != None:
        fine_hours = json.loads(statistic[0])
        for i in range(0,23):
            if str(i) in fine_hours.keys():
                stroka = stroka + str(i) + ':00- ' + str(i+1) + ':00 : <B>' + str(fine_hours[str(i)]) + '</B>\n'
    else:
        stroka = stroka + 'Нет информации\n'
    request_user = baza.get_request_count(id_shop)
    if request_user > 1:
        req = "\n❓ Запросов по магазину :" + str(request_user-1)
    else:
        req = "\n❓ За последние 2 часа запросов не было"
    charha = baza.get_info_charha(id_shop)
    if charha != None:
        ch = "\nℹ Информация за последний час - " + str(charha[0]) + " 🚛"
    else:
        ch = "\nℹ Онлайн информации нет 🏳"
    answer = answer_to_user + time_to + stroka + req + ch
    await bot.send_message(callback_addr.from_user.id, answer, reply_markup=kb.kb1)

@dp.callback_query_handler(lambda car: car.data.startswith('car'))
async def save_car_ikb2(callback_car: types.CallbackQuery, state: FSMContext):
    #global g_shop_id
    car_ok = int(callback_car.data[-1])
    if car_ok > 1:
        car_ok = car_ok * 2 # пока что просто умножаем на 2, далее продумать алгоритм
    #TODO добавить алгоритм учета правильного выставления машинок по количетсву
    async with state.proxy() as td:
        id_shop = td['shop_id']
    baza.add_events(callback_car.from_user.id, id_shop, car_ok, True)
    period = datetime.now().hour
    baza.create_finehours_shop(id_shop, period, car_ok)
    await bot.send_message(callback_car.from_user.id, 'Благодарим за информацию!', reply_markup=kb.kb1) 


@dp.callback_query_handler()
# обработчик инлайн клавы с количетсвом машинок
async def enter_cars(message: types.Message):
    await bot.send_message(message.from_user.id,'Ну как?', reply_markup=kb.ikb2)

if __name__ == '__main__':
    executor.start_polling(dp)