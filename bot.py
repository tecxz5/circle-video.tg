import os
import time
from config import *
from telebot import TeleBot
from moviepy.editor import VideoFileClip
import threading

bot = TeleBot(TOKEN)

# Словарь для хранения информации об обработке видео для каждого пользователя
processing_status = {}  # {user_id: True/False} - True если есть задача в обработке
video_queue = {}  # {user_id: [(message, notification_id), ...]}
queue_lock = threading.Lock()

@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id, f'''
Привет {user_name}, я преобразую твои видео в кружок
Требования к видео(необязательно, но результат будет не самый лучший):
1. Соотношение сторон видео: 1:1
2. Вес видео: 20 мб
3. Ограничение времени видео: 60 секунд''')

def process_video_task(message, notification_id):
    """Функция для обработки видео в отдельном потоке."""
    user_id = message.from_user.id
    try:
        # notification = bot.reply_to(message, "Видео принято. Обрабатываю...")
        start_time = time.time()

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

        # Разделяем видео на части
        total_duration = output_video.duration
        num_chunks = 10  # Количество частей, на которые разбиваем видео
        chunk_duration = total_duration / num_chunks

        for i in range(num_chunks):
            # Вычисляем время начала и конца для текущей части
            start_time_chunk = i * chunk_duration
            end_time_chunk = (i + 1) * chunk_duration
            chunk = output_video.subclip(start_time_chunk, end_time_chunk)
            # Формируем имя файла для текущей части
            output_file_chunk = f"output_video_part_{i}.mp4"
            # Записываем текущую часть видео
            chunk.write_videofile(
                output_file_chunk,
                codec="libx264",
                audio_codec="aac",
                bitrate="2M"
            )
            # Вычисляем прогресс и отправляем сообщение
            progress = (i + 1) / num_chunks
            elapsed_time = time.time() - start_time
            remaining_time = elapsed_time / progress * (1 - progress)
            
            bot.edit_message_text(
                f"Видео принято. Обрабатываю...\nОсталось: {remaining_time:.1f} сек",
                chat_id=message.chat.id,
                message_id=notification_id #Используем notification_id
            )

            # Удаляем временный файл
            os.remove(output_file_chunk)

        # Собираем все части в один файл
        # (Этот шаг можно оптимизировать, записывая сразу в нужный файл)
        output_video.write_videofile(
            "output_video.mp4",
            codec="libx264",
            audio_codec="aac",
            bitrate="1M"
        )

        bot.delete_message(chat_id=message.chat.id, message_id=notification_id) #Используем notification_id
        with open("output_video.mp4", "rb") as video_file:
            bot.send_video_note(
                message.chat.id,
                video_file,
                duration=int(output_video.duration),
                length=circle_size
            )
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")
    finally:
        with queue_lock:
            try:
                if user_id in video_queue and video_queue[user_id]:
                    video_queue[user_id].pop(0)  # Удаляем обработанное видео из очереди
                    if video_queue[user_id]:
                        process_next_video(user_id)
                    else:
                        del video_queue[user_id]
                        processing_status.pop(user_id, None) #Удаляем если очередь пуста
                else:
                    processing_status.pop(user_id, None) #Удаляем если не в очереди
            except Exception as e:
                print(f"Ошибка в finally: {e}")
        print(f"Видео для пользователя {user_id} обработано. Запускаем следующее из очереди, если есть.")

def process_next_video(user_id):
    """Обрабатывает следующее видео из очереди для данного пользователя."""
    with queue_lock:
        if user_id in video_queue and video_queue[user_id]:
            next_message, notification_id = video_queue[user_id][0] #Получаем message и notification_id
            threading.Thread(target=process_video_task, args=(next_message, notification_id)).start() #Передаем notification_id

@bot.message_handler(content_types=['video'])
def process_video(message):
    user_id = message.from_user.id
    with queue_lock:
        if user_id in processing_status: #Если есть в processing_status - значит обрабатывается
            # Пользователь уже в очереди, добавляем в очередь
            notification = bot.reply_to(message, "Ваше видео добавлено в очередь.") #Отвечаем сразу
            if user_id not in video_queue:
                video_queue[user_id] = [(message, notification.message_id)] #Сохраняем message и notification_id
            else:
                video_queue[user_id].append((message, notification.message_id)) #Сохраняем message и notification_id
            bot.reply_to(message, f"Всего в очереди: {len(video_queue[user_id])}. Дождитесь окончания обработки предыдущих видео.")
            return

        # Если пользователь не в очереди, начинаем обработку
        processing_status[user_id] = True #Добавляем в processing_status
        notification = bot.reply_to(message, "Видео принято. Обрабатываю...") #Отвечаем
        threading.Thread(target=process_video_task, args=(message, notification.message_id)).start() #Передаем notification_id

if __name__ == "__main__":
    print("Бот запускается...")
    bot.infinity_polling()