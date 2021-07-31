import sqlite3
import json

from datetime import datetime, timedelta

delta_request = 2
delta_info = 1

class Baza:

    def __init__(self, db_file):
        # инициализация соединения
        self.connection = sqlite3.connect(database=db_file)
        self.cursor = self.connection.cursor()

    def close(self):
        self.connection.close()
    
    def check_user(self, user_id):
        # проверка наличия юзера
        with self.connection:
            temp = self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id, )).fetchone()
        if temp:
            return True
        else: 
            return False
    
    def add_user(self, user_id, name):
        # добавляем юзера
        with self.connection:
            return self.cursor.execute("INSERT INTO users (id, name, count_info, last) VALUES (?, ?, ?, ?)", 
            (user_id, name, 1, datetime.now()))

    def change_statistic(self, user, info):
        # меняем статистику юзера если он выдает инфу + время последнего посещения
        with self.connection:
            count = self.cursor.execute("SELECT count_info FROM users WHERE id = ?", (user,)).fetchone()
            count = int(count[0])
            if info:
                count = count + 1
            return self.cursor.execute("UPDATE users SET count_info=?, last=? WHERE id=?", (count, datetime.now(), user))
            
    def get_count_user_shops (self):
        # выдаем счетчик пользователей и количетсво магазинов в базе
        with self.connection:
            count_users = self.cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            count_shops = self.cursor.execute("SELECT COUNT(*) FROM shops").fetchone()[0]
        return count_users, count_shops
            

    def search_shops(self, lat_, long_):
        # поиск магазина по координатоам
        with self.connection:
            lat_down = round(lat_ - 0.003, 3)
            lat_up = round(lat_ + 0.003, 3)
            long_down = round(long_ - 0.003, 3)
            long_up = round(long_ + 0.003, 3)
            # 0,003 оптимальная цифра в радиусе 200м
            return self.cursor.execute("SELECT id, address, short FROM shops WHERE (latitude BETWEEN ? AND ?) AND (longitude BETWEEN ? AND ? )", 
            (lat_down, lat_up, long_down, long_up)).fetchall()

            
    def add_events(self, user, shop, cars, info):
        with self.connection:
            # добавляем любое событие запрос инфы info = False, подача info = True
            self.change_statistic(user, info)
            return self.cursor.execute("INSERT INTO events (id_user, id_shop, cars, date, info) VALUES (?, ?, ?, ?, ?)",
            (user, shop, cars, datetime.now(), info))
    
    def create_finehours_shop(self, shop, period, cars):
        # меняем статистику магазина если введена информация
        with self.connection:
            # проверим, если инфо по магазину
            info_shop = self.cursor.execute("SELECT hours FROM fine_hours WHERE id_shop = ?", (shop,)).fetchone()
            
            fine_hours_tuple = {period: cars}
            if info_shop == None:
                return self.cursor.execute("INSERT INTO fine_hours (id_shop, hours) VALUES (?, ?)",
                (shop, json.dumps(fine_hours_tuple)))
            else:
                decode = json.loads(info_shop[0])
                if str(period) in decode:
                    # если есть уже статистика за этот период
                    decode[str(period)] = int((cars + decode[str(period)])/2)
                else:
                    decode[str(period)] = cars
                return self.cursor.execute("UPDATE fine_hours SET hours = ? WHERE id_shop = ?", (json.dumps(decode), shop))

    def get_name_net(self, region):
        # выдаем название всех сетей в регионе
        with self.connection:
            return self.cursor.execute("SELECT DISTINCT short FROM shops WHERE region=? AND net=True", (region,)).fetchall()
    
    def get_address_shop(self, region, net, flag):
        # ищем адреса магазинов, если введен регион и название сети
        #TODO потом нужно исправить short на название сети в БД
        with self.connection:
            if flag:
                return self.cursor.execute("SELECT id, address, short FROM shops WHERE (region = ? AND short = ? AND net = ?)", (int(region), net, flag)).fetchall()
            else:
                return self.cursor.execute("SELECT id, address, short FROM shops WHERE (region = ? AND net = ?)", (int(region), flag)).fetchall()


    def get_statistic_shop(self, id):
        # получаем статистику по ID магазина
        with self.connection:
            return self.cursor.execute("SELECT hours FROM fine_hours WHERE id_shop=?", (id,)).fetchone()

    def get_info_shop(self, id):
        # выдаем информацию по магизу из shops
        with self.connection:
            return self.cursor.execute("SELECT address, name, time_begin, time_end, night, foto, schedule FROM shops WHERE id=?",(id,)).fetchone()

    def get_request_count(self, id_shop):
        # выдаем количетсво запросов по магазину за период
        with self.connection:
            time_period = datetime.now() - timedelta(hours=delta_request) # delta_request пока равно 2 часам
            return self.cursor.execute("SELECT COUNT(*) FROM events WHERE (id_shop=? AND date>? AND info=False)", (id_shop, time_period)).fetchone()[0]
    
    def get_info_charha(self, id_shop):
        # выдаем информацию если сейчас есть онлайн
        with self.connection:
            time_period = datetime.now() - timedelta(hours=delta_info) # delta_info пока равно 1 часу
            return self.connection.execute("SELECT cars FROM events WHERE (id_shop=? AND info=True AND date>?) ORDER BY date DESC", (id_shop, time_period)).fetchone()

    
    def delete_events(self):
        with self.connection:
            time_period = datetime.now() - timedelta(days=1) # будем чистить сообщения старше 3 часов
            return self.connection.execute("DELETE FROM events WHERE date<?", (time_period,))