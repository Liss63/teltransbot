#!/usr/bin/env python3.8
from transmission_rpc import Client, torrent as ti
import telebot
from telebot.types import BotCommand
import io
import pathlib


def torrent_fields(self):
    return self._fields


bot = telebot.TeleBot('token')
bot.set_my_commands([BotCommand('list', 'список торрентов'), BotCommand('add', 'Добавить торрент')])
c = Client(host='host', port=9091, username='user', password='password')
userTorrent = {}
hideBoard = telebot.types.ReplyKeyboardRemove()
setattr(ti.Torrent, "fields", property(torrent_fields))


def get_user_torrent(uid):
    if uid in userTorrent:
        return userTorrent[uid]
    else:
        userTorrent[uid] = 0
        return 0


def convert_bytes(num):
    step_unit = 1000.0
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < step_unit:
            return "%3.1f %s" % (num, x)
        num /= step_unit


@bot.message_handler(commands=['list'])
def get_torrents_list(message):
    torrents_list = c.get_torrents()
    keyboard = telebot.types.InlineKeyboardMarkup()
    for t in torrents_list:
        keyboard.add(telebot.types.InlineKeyboardButton(text=t.name, callback_data=t.id))
    bot.send_message(message.from_user.id, text="Список торрентов", reply_markup=keyboard)


@bot.message_handler(func=lambda message: (message.content_type == 'text') &
                                          (get_user_torrent(message.chat.id) != 0) &
                                          (message.text == 'info'))
def info_button_handler(message):
    torrent_id = userTorrent[message.chat.id]
    torrent = c.get_torrent(torrent_id)
    bot.send_message(message.chat.id, torrent.name)
    bot.send_message(message.chat.id,
                     "Progress %d%s of %s. Status: %s" % (torrent.progress,
                                                          '%',
                                                          convert_bytes(torrent.fields["sizeWhenDone"].value),
                                                          torrent.status))
    bot.send_message(message.chat.id, "Path: %s" % torrent.fields['downloadDir'].value)


@bot.message_handler(func=lambda message: (message.content_type == 'text') &
                                          (get_user_torrent(message.chat.id) != 0) &
                                          (message.text == 'to films'))
def to_films_button_handler(message):
    torrent_id = userTorrent[message.chat.id]
    torrent = c.get_torrent(torrent_id)
    path = torrent.fields['downloadDir'].value
    p = pathlib.Path(path).parent.joinpath('films')
    c.move_torrent_data(torrent_id, p)
    bot.send_message(message.chat.id, "moved to %s" % p)


@bot.message_handler(func=lambda message: (message.content_type == 'text') &
                                          (get_user_torrent(message.chat.id) != 0) &
                                          (message.text == 'to serials'))
def to_serials_button_handler(message):
    torrent_id = userTorrent[message.chat.id]
    torrent = c.get_torrent(torrent_id)
    path = torrent.fields['downloadDir'].value
    p = pathlib.Path(path).parent.joinpath('serials')
    c.move_torrent_data(torrent_id, p)
    bot.send_message(message.chat.id, "moved to %s" % p)


@bot.message_handler(func=lambda message: (message.content_type == 'text') &
                                          (get_user_torrent(message.chat.id) != 0) &
                                          (message.text == 'delete'))
def delete_button_handler(message):
    torrent_id = userTorrent[message.chat.id]
    c.remove_torrent(torrent_id)
    bot.send_message(message.chat.id, "deleted")


@bot.message_handler(func=lambda message: (message.content_type == 'text') &
                                          (get_user_torrent(message.chat.id) != 0) &
                                          (message.text == 'stop'))
def stop_button_handler(message):
    torrent_id = userTorrent[message.chat.id]
    c.stop_torrent(torrent_id)
    bot.send_message(message.chat.id, "stopped")


@bot.message_handler(func=lambda message: (message.content_type == 'text') &
                                          (get_user_torrent(message.chat.id) != 0) &
                                          (message.text == 'start'))
def start_button_handler(message):
    torrent_id = userTorrent[message.chat.id]
    c.start_torrent(torrent_id)
    bot.send_message(message.chat.id, "started")


@bot.message_handler(func=lambda message: (message.content_type == 'text') &
                                          (get_user_torrent(message.chat.id) != 0) &
                                          (message.text == 'exit'))
def exit_button_handler(message):
    userTorrent[message.chat.id] = 0

    bot.send_message(message.chat.id, 'Выберите торрент', reply_markup=hideBoard)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    bot.send_message(message.from_user.id, text=message.text)
    bot.send_message(message.from_user.id, text=str(userTorrent))


@bot.message_handler(content_types=['document'])
def get_text_messages(message):
    file_info = bot.get_file(message.document.file_id)
    data = bot.download_file(file_info.file_path)
    c.add_torrent(io.BytesIO(data))
    bot.send_message(message.from_user.id, text='Торрент добавлен')


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    torrent_id = int(call.data)
    userTorrent[call.message.chat.id] = torrent_id
    torrent = c.get_torrent(torrent_id)
    bot.answer_callback_query(call.id, call.data, show_alert=False)
    markup = telebot.types.ReplyKeyboardMarkup()
    markup.add('info', 'to films', 'to serials', 'delete', 'start', 'stop', 'exit')
    bot.send_message(call.message.chat.id, text=torrent.name, reply_markup=markup)


bot.polling(none_stop=True, interval=0)
