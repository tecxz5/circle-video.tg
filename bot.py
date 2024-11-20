import os
from config import *
from telebot import TeleBot
from moviepy.editor import VideoFileClip

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

@bot.message_handler(content_types=['video'])
def process_video(message):
    try:
        notification = bot.reply_to(message, "Видео принято. Обрабатываю...")
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("input_video.mp4", "wb") as video_file:
            video_file.write(downloaded_file)
        input_video = VideoFileClip("input_video.mp4")
        w, h = input_video.size
        circle_size = 360
        aspect_ratio = float(w) / float(h)
        if w > h:
            new_w = int(circle_size * aspect_ratio)
            new_h = circle_size
        else:
            new_w = circle_size
            new_h = int(circle_size / aspect_ratio)
        resized_video = input_video.resize((new_w, new_h))
        output_video = resized_video.crop(x_center=resized_video.w/2, y_center=resized_video.h/2, width=circle_size, height=circle_size)
        output_video.write_videofile("output_video.mp4", codec="libx264", audio_codec="aac", bitrate="5M")
        bot.delete_message(chat_id=message.chat.id, message_id=notification.message_id)
        with open("output_video.mp4", "rb") as video_file:
            bot.send_video_note(
                message.chat.id,
                video_file,
                duration=int(output_video.duration),
                length=circle_size
            )
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")

if __name__ == "__main__":
    print("Бот запускается...")
    bot.polling()