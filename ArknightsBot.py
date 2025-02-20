from ast import Pass
from zoneinfo import ZoneInfo
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from vk_api import VkUpload
import calendar
import datetime
import time
from pybooru import Danbooru
import requests
import vk_api
import threading
import sqlite3

vk_session = vk_api.VkApi(token="vk1.a.EL3L1hE2V-rHHnQX1lXYsa1yjLgV08OuyAwnybzkw4yqg53LAvB8DkFAYpHNz_LMtKMrx2YRi_neoxI8YxkMea6FHZFQYrJf3nMAlehUBE9px0HdkI3g9OwVGdmDDlBIEHVyS3_HgbXw9XRvZaywEanzBeZwLDGyFELSWwhHlqF9kzuzdmvx36uotnl-pF-HqsyNy8OYdwIbL4JVT8VFHw")
danbooruClient = Danbooru("danbooru", username="NVKalashnikov", api_key="1nafoWw9jkWrJrNZpF6F1v2B")
session = requests.Session()
upload = VkUpload(vk_session)
vk = vk_session.get_api()

def init_db():
    with sqlite3.connect('images.db') as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                DanbooruID INTEGER,
                post_text TEXT,
                file_url TEXT,
                source_url TEXT
            )
        """)

init_db()


teleClient = telebot.TeleBot('7702289828:AAFby7_1ogSZPW6zPeG5lpmf0PVbY00_Hv8')
chat_id = -1002488737729

onProcessing = 0


class teleBot:
    def __init__(self, teleClient, danbooruClient, session, vk, upload, chat_id):
        self.danbooru = danbooruClient
        self.teleBot = teleClient
        self.vk = vk
        self.session = session
        self.upload = upload
        self.lastid = 0
        self.animage_id = 0
        self.chat = chat_id


    def gen_markup(self, danbooruID):
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(InlineKeyboardButton("На публикацию", callback_data=f"publicate_{danbooruID}"),
                   InlineKeyboardButton("Удалить", callback_data=f"delete_{danbooruID}"))
        return markup


    def regularPars(self):
        while True:
            time.sleep(10)
            self.danbooruPars()


    def danbooruPars(self):
        try:
            print("Parsing")
            post = self.danbooru.post_list(limit=1, page=1, tags="arknights")
            for _id in post:
                if _id['id'] == self.lastid:
                    print("Oldpost return")
                    return
                else:
                    self.lastid = _id['id']
                    print(self.lastid)
            print("Getting a post")
            self.danbooruGrab(post)
        except Exception as e:
            print(e)


    def danbooruGrab(self, post):
        for _img in post:
            tags = _img['tag_string'].split()
            for check in tags:
                if check == "sex" or check == "nude" or check == "nipples" or check == "penis" or check == "pussy" or check == "futanari" or check == "cum": #если в тегах найденного арта есть хотя-бы один из тегов в этой проверке, то ищется новый арт (некий блеклист тегов)
                    print("BlackList return")
                    return
            print("tags check pass")
            try:
                file_url = _img['file_url']
            except KeyError:
                print("KeyError return")
                return
            source_url, danbooruID, artist = _img['source'], _img['id'], _img['tag_string_artist']
            characters = self.format_characters(_img['tag_string_character'])
            print("tag konstrukt pass")
            message = characters + "\n" + "#Arknights" + "\n\n" + f"by {artist}"
            file_ext = _img['file_ext']
            print(file_url)
            file_size = _img['file_size'] / 1000 / 1024
            print(_img)
            if _img['file_size'] > 5000000:
                print("Это очень большое изображение.")
                try:
                    self.teleBot.send_photo(self.chat, _img['large_file_url'], caption = message + "\n\n" + source_url + "\n\n" + file_ext + f" {file_size} Mb", reply_markup=self.gen_markup(danbooruID))
                    self.save_image_data(danbooruID, message, file_url, source_url)
                except Exception as e:
                    print(f"{e}")
            else:
                try:
                    self.teleBot.send_photo(self.chat, file_url, caption = message + "\n\n" + source_url + "\n\n" + file_ext + f" {file_size} Mb", reply_markup=self.gen_markup(danbooruID))
                    self.save_image_data(danbooruID, message, file_url, source_url)
                except Exception as e:
                    print(f"{e}")
            return


    def format_characters(self, tag_string):
        return "\n".join(f"#{tag.replace('_(arknights)', '')}@arknightsmg " for tag in tag_string.split())


    def save_image_data(self, danbooruID, post_text, file_url, source_url):
        with sqlite3.connect('images.db') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Images (DanbooruID, post_text, file_url, source_url)
                VALUES (?, ?, ?, ?)
            """, (danbooruID, post_text, file_url, source_url))


    def start(self):
        timer_thread = threading.Thread(target=self.regularPars)
        timer_thread.daemon = True
        timer_thread.start()
        dateTime_thread = threading.Thread(target=self.calendar)
        dateTime_thread.daemon = True
        dateTime_thread.start()


    def calendar(self):
        now = datetime.datetime.now()
        year = now.year
        for month in range(1, 13):
            print(month)
            cond = sqlite3.connect('images.db')
            cursord = cond.cursor()
            cursord.execute(f"""CREATE TABLE IF NOT EXISTS year{year}_month{month}(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            day INTEGER,
                            unixDay INTEGER)""")
            cursord.execute(f'SELECT day FROM year{year}_month{month} WHERE day=?', (10,))
            ali = cursord.fetchall()
            cond.close()
            if not ali:
                my_calendar = calendar.monthcalendar(year, month)
                dates = []
                for i in my_calendar:
                    for q in i:
                        if q != 0:
                            if len(str(q)) == 1:
                                q = str(f"0{q}")
                                dates.append(q)
                            else:
                                dates.append(str(q))
                cond = sqlite3.connect('images.db')
                cursord = cond.cursor()

                for z in dates:
                    dtz = datetime.datetime.fromisoformat(f"{year}-{f'0{month}' if len(str(month)) == 1 else month}-{z} 00:00:00")
                    print(dtz)
                    dt = dtz.replace(tzinfo=ZoneInfo("Europe/Moscow"))
                    d = dt.timestamp()
                    cursord.execute(f"INSERT INTO year{year}_month{month} (day, unixDay) VALUES (?, ?)", (z, d))
                    cursord.execute(f"""CREATE TABLE IF NOT EXISTS  year{year}_month{month}_day{z} (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                hour INTEGER,
                                unixHour INTEGER,
                                danbooruID INTEGER)""")
                    for b in range(0, 24):
                        cond.execute(f"INSERT INTO year{year}_month{month}_day{z} (hour, unixHour) VALUES (?, ?)", (b, d))
                        d += 3600
                cond.commit()  
                cond.close()


    def gen_markup_edit(self, danbooruID):
        self.dbID = danbooruID
        markup = InlineKeyboardMarkup()
        markup.row_width = 4
        markup.add(InlineKeyboardButton("Январь", callback_data=f"month_1"),
                   InlineKeyboardButton("Февраль", callback_data=f"month_2"),
                   InlineKeyboardButton("Март", callback_data=f"month_3"),
                   InlineKeyboardButton("Апрель", callback_data=f"month_4"),
                   InlineKeyboardButton("Май", callback_data=f"month_5"),
                   InlineKeyboardButton("Июнь", callback_data=f"month_6"),
                   InlineKeyboardButton("Июль", callback_data=f"month_7"),
                   InlineKeyboardButton("Август", callback_data=f"month_8"),
                   InlineKeyboardButton("Сентябрь", callback_data=f"month_9"),
                   InlineKeyboardButton("Октябрь", callback_data=f"month_10"),
                   InlineKeyboardButton("Ноябрь", callback_data=f"month_11"),
                   InlineKeyboardButton("Декабрь", callback_data=f"month_12"))
        return markup


    def calendar_execute_month(self, month):
        self.monthly = month
        now = datetime.datetime.now()
        year = now.year
        cord = sqlite3.connect('images.db')
        cursorr = cord.cursor()
        cursorr.execute(f"SELECT day FROM year{year}_month{month}")
        x = cursorr.fetchall()
        cord.close()
        markup = InlineKeyboardMarkup()
        markup.row_width = 7
        buttons = []
        for z in x:
            buttons.append(InlineKeyboardButton(f"{z[0]}", callback_data=f"day_{z[0]}"))
        markup.add(*buttons)
        return markup
    
    def calendar_execute_day(self, day):
        self.day = day
        now = datetime.datetime.now()
        year = now.year
        cord = sqlite3.connect('images.db')
        cursorr = cord.cursor()
        cursorr.execute(f"SELECT hour, danbooruID FROM year{year}_month{self.monthly}_day{day}")
        buttons = []
        q = cursorr.fetchall()
        cord.close()
        markup = InlineKeyboardMarkup()
        markup.row_width = 4
        for z in q:
            if z[1] == None:
                buttons.append(InlineKeyboardButton(f"{z[0]}", callback_data=f"hour_{z[0]}"))
            else:
                buttons.append(InlineKeyboardButton(f"X", callback_data=f"close"))
        markup.add(*buttons)
        return markup


    def vk_posting(self, hour, call_id, chat_id, msg_id):
        cord = sqlite3.connect('images.db')
        cursorr = cord.cursor()
        cursorr.execute(f"SELECT unixHour FROM year{datetime.datetime.now().year}_month{self.monthly}_day{self.day} WHERE hour = ?", (hour,))
        unix = cursorr.fetchone()[0]
        cursorr.execute(f"SELECT post_text, file_url, source_url FROM Images WHERE DanbooruID = ?", (self.dbID,))
        image = cursorr.fetchall()
        message = image[0][0]
        print(message)
        try:
            print("Аттачу")
            attachments = []
            image = self.session.get(image[0][1], stream=True)
            photo = self.upload.photo_wall(photos=image.raw)[0]
            attachments.append(f"photo{photo['owner_id']}_{photo['id']}")
            print("Зааттачил")
            self.vk.wall.post(owner_id=-195726793, from_group=1, attachment=','.join(attachments), publish_date=unix + 70, message=message)
            cursorr.execute(f"UPDATE year{datetime.datetime.now().year}_month{self.monthly}_day{self.day} SET danbooruID = ? WHERE hour = ?", (self.dbID, hour))
            self.teleBot.answer_callback_query(call_id, "Пост успешно отложен.")
            teleClient.edit_message_reply_markup(chat_id, msg_id, reply_markup=bot.final(hour))
            print(image)
        except Exception as e:
            self.teleBot.answer_callback_query(call_id, f"Не удалось отложить пост: {e}")
            print(e)
        cord.commit()
        cord.close()

    def final(self, hour):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(f"Пост отложен на {self.day}.{self.monthly}.{datetime.datetime.now().year} на {hour} часов.", callback_data = "nonData"))
        return markup

bot = teleBot(teleClient, danbooruClient, session, vk, upload, chat_id)
bot.start()

@teleClient.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print(call.message.chat.id)
    print(call.message.id)
    if "publicate" in call.data:
        danbooruID = call.data.replace("publicate_", "")
        teleClient.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=bot.gen_markup_edit(danbooruID))
    elif "delete" in call.data:
        try:
            teleClient.delete_message(call.message.chat.id, call.message.id)
            teleClient.answer_callback_query(call.id, "Сообщение удалено.")
        except:
            teleClient.answer_callback_query(call.id, "Не удалось удалить сообщение.")
    elif "month" in call.data:
        month = call.data.replace("month_", "")
        teleClient.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=bot.calendar_execute_month(month))
    elif "day" in call.data:
        day = call.data.replace("day_", "")
        teleClient.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=bot.calendar_execute_day(day))
    elif "hour" in call.data:
        hour = call.data.replace("hour_", "")
        bot.vk_posting(hour, call.id, call.message.chat.id, call.message.id)
    elif "close" in call.data:
        teleClient.answer_callback_query(call.id, "На эту дату уже запланирован пост.")

teleClient.infinity_polling()
