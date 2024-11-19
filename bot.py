import logging
from config import *
from telebot import TeleBot

logging.basicConfig(filename='logs.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    encoding='utf-8')

bot = TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id, f'''
Привет {user_name}, я преобразую твои видео в кружок
Требования к видео(необязательно, но результат будет не самый лучший):
1. Соотношение сторон видео: 1:1
2. Вес видео: 20 мб
3. Ограничение времени видео: 60 секунд''')

if __name__ == "__main__":
    print("Бот запускается...")
    bot.polling()