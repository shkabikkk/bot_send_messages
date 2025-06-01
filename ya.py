from telethon.sync import TelegramClient
from telethon.tl.functions.messages import SendMediaRequest
from telethon.tl.types import InputMediaUploadedPhoto, InputMediaUploadedDocument
from telethon.errors import PersistentTimestampOutdatedError, FloodWaitError, RPCError
import asyncio
import time
import os
import sys
import random
import threading
import telebot
from telebot import types
import logging
from io import StringIO

# Настройки
api_id = 26940168
api_hash = '215022f99105f13b0e091b010463fef3'
phone = '+14407393438'
bot_token = '7652897749:AAGxhDJWdVQZKJSZ9z4WdIxEiEgPdZBnGcA'

# Глобальные переменные
script_running = False
current_script_thread = None
stop_event = threading.Event()
log_subscribers = set()
log_stream = StringIO()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(log_stream)
    ]
)
logger = logging.getLogger(__name__)

# Список групп для рассылки
group_usernames = ['wbery_vip2', 'wberysl', 
                  'chatik_piarvz777', 'STANDOFF_2n', 'standoff_chatk', 'Nowasti_ot_Mr_Roblox'
                  , 'models_chat_traun_poezda12', 'brawl_stars_chat02', 'fin_crypto_chat', 'brawlstarschatik_24'
                  , 'ufarabota_chat']

message_text = '''
🔥Твой личный рай уже здесь🔥
Топовый контент популярных блогерш и моделей уже ждет тебя в нашем телеграмм канале 🔞МОДЕЛИ 18+🔞 (https://t.me/models18_plus)
✅ Эксклюзивный контент
✅ Активность
✅ Самые лучшие модели

👉 Жми сюда (https://t.me/models18_plus)
'''
image_path = None
delay_seconds = 60

# Инициализация бота
bot = telebot.TeleBot(bot_token)

def show_main_menu(chat_id, message_text="Выберите действие:"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('📋 Список чатов')
    btn2 = types.KeyboardButton('✉️ Просмотреть сообщение')
    btn3 = types.KeyboardButton('🔄 Изменить сообщение')
    btn4 = types.KeyboardButton('➕ Добавить чат')
    btn5 = types.KeyboardButton('➖ Удалить чат')
    btn6 = types.KeyboardButton('▶️ Запустить рассылку')
    btn7 = types.KeyboardButton('⏹ Остановить рассылку')
    btn8 = types.KeyboardButton('📜 Показать логи')
    btn9 = types.KeyboardButton('🚫 Остановить логи')
    markup.row(btn1, btn2, btn3)
    markup.row(btn4, btn5)
    markup.row(btn6, btn7)
    markup.row(btn8, btn9)
    
    bot.send_message(chat_id, message_text, reply_markup=markup)

class LogSender:
    def __init__(self):
        self.active = False
        self.last_sent_position = 0
    
    def start_sending_logs(self, chat_id):
        if chat_id not in log_subscribers:
            log_subscribers.add(chat_id)
            self.active = True
            logger.info(f"Пользователь {chat_id} подписался на логи")
    
    def stop_sending_logs(self, chat_id):
        if chat_id in log_subscribers:
            log_subscribers.remove(chat_id)
            logger.info(f"Пользователь {chat_id} отписался от логов")
    
    def send_new_logs(self):
        if not log_subscribers:
            return
        
        log_content = log_stream.getvalue()
        new_content = log_content[self.last_sent_position:]
        
        if new_content:
            for chat_id in list(log_subscribers):
                try:
                    if len(new_content) > 4000:
                        parts = [new_content[i:i+4000] for i in range(0, len(new_content), 4000)]
                        for part in parts:
                            bot.send_message(chat_id, f"<pre>{part}</pre>", parse_mode='HTML')
                    else:
                        bot.send_message(chat_id, f"<pre>{new_content}</pre>", parse_mode='HTML')
                except Exception as e:
                    logger.error(f"Ошибка отправки логов пользователю {chat_id}: {e}")
                    log_subscribers.remove(chat_id)
            
            self.last_sent_position = len(log_content)

log_sender = LogSender()

async def create_client():
    client = TelegramClient('user_session', api_id, api_hash)
    await client.connect()
    
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        await client.sign_in(phone, input('Введите код из Telegram: '))
    
    return client

async def send_to_group(client, group, media=None, max_retries=3):
    for attempt in range(max_retries):
        if stop_event.is_set():
            return False
            
        try:
            entity = await client.get_entity(group)
            
            if media:
                await client(SendMediaRequest(
                    peer=entity,
                    media=media,
                    message=message_text
                ))
            else:
                await client.send_message(entity, message_text)
                
            logger.info(f"✅Сообщение в {group} отправлено")
            return True
            
        except Exception as e:
            if stop_event.is_set():
                return False
                
            logger.error(f"❌Ошибка при отправке в {group}: {str(e)}")
            await asyncio.sleep(random.randint(5, 15))
    
    return False

async def main_async():
    global script_running
    
    media = None
    if image_path and os.path.exists(image_path):
        try:
            client = await create_client()
            file = await client.upload_file(image_path)
            media = InputMediaUploadedPhoto(file) if image_path.lower().endswith(('.png', '.jpg', '.jpeg')) else InputMediaUploadedDocument(file)
            await client.disconnect()
        except Exception as upload_error:
            logger.error(f"Не удалось загрузить изображение: {upload_error}")

    while not stop_event.is_set():
        start_time = time.time()
        logger.info("Начало нового цикла рассылки")
        
        try:
            client = await create_client()
            random.shuffle(group_usernames)
            
            for group in group_usernames:
                if stop_event.is_set():
                    break
                    
                success = await send_to_group(client, group, media)
                
                if stop_event.is_set():
                    break
                    
                delay = random.uniform(3, 10) if success else random.uniform(10, 30)
                logger.info(f"Ожидание {delay:.1f} сек перед следующим сообщением")
                
                start_delay = time.time()
                while (time.time() - start_delay) < delay and not stop_event.is_set():
                    await asyncio.sleep(0.5)
                    log_sender.send_new_logs()
                
                if stop_event.is_set():
                    break
            
            if stop_event.is_set():
                break
                
            elapsed = time.time() - start_time
            logger.info(f"Цикл рассылки завершен за {elapsed:.2f} сек")
            
            if delay_seconds > elapsed:
                remaining = delay_seconds - elapsed
                logger.info(f"Ожидание {remaining:.2f} сек до следующего цикла")
                
                start_delay = time.time()
                while (time.time() - start_delay) < remaining and not stop_event.is_set():
                    await asyncio.sleep(0.5)
                    log_sender.send_new_logs()
                    
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            await asyncio.sleep(10)
        finally:
            if 'client' in locals():
                await client.disconnect()
    
    script_running = False
    logger.info("Рассылка полностью остановлена")

def main():
    asyncio.run(main_async())

def start_script():
    global script_running, current_script_thread, stop_event
    
    if script_running:
        return "Скрипт уже работает!"
    
    stop_event.clear()
    script_running = True
    current_script_thread = threading.Thread(target=main)
    current_script_thread.start()
    return "Скрипт запущен!"

def stop_script():
    global script_running, stop_event
    
    if not script_running:
        return "Скрипт не был запущен!"
    
    stop_event.set()
    script_running = False
    return "Скрипт останавливается... Ожидайте завершения текущих отправок."

# Обработчики команд бота
@bot.message_handler(commands=['start'])
def send_welcome(message):
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '📋 Список чатов')
def show_chats(message):
    chats_list = "\n".join([f"{i+1}. {chat}" for i, chat in enumerate(group_usernames)])
    bot.send_message(message.chat.id, f"📋 Список чатов ({len(group_usernames)}):\n\n{chats_list}")
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '✉️ Просмотреть сообщение')
def show_message(message):
    bot.send_message(message.chat.id, f"Текущее сообщение:\n\n{message_text}")
    show_main_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '🔄 Изменить сообщение')
def change_message(message):
    msg = bot.send_message(message.chat.id, "Введите новое сообщение:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_message_change)

def process_message_change(message):
    global message_text
    message_text = message.text
    show_main_menu(message.chat.id, "✅ Сообщение обновлено!")

@bot.message_handler(func=lambda message: message.text == '➕ Добавить чат')
def add_chat(message):
    msg = bot.send_message(message.chat.id, "Введите username чата (без @):", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_chat_add)

def process_chat_add(message):
    chat = message.text.strip().replace('@', '')
    if chat not in group_usernames:
        group_usernames.append(chat)
        show_main_menu(message.chat.id, f"✅ Чат @{chat} добавлен!")
    else:
        show_main_menu(message.chat.id, f"⚠️ Чат @{chat} уже есть в списке!")

@bot.message_handler(func=lambda message: message.text == '➖ Удалить чат')
def remove_chat(message):
    markup = types.InlineKeyboardMarkup()
    for chat in group_usernames:
        markup.add(types.InlineKeyboardButton(chat, callback_data=f"remove_{chat}"))
    bot.send_message(message.chat.id, "Выберите чат для удаления:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('remove_'))
def process_chat_remove(call):
    chat = call.data[7:]
    if chat in group_usernames:
        group_usernames.remove(chat)
        bot.edit_message_text(f"✅ Чат @{chat} удален!", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "Чат не найден!")
    show_main_menu(call.message.chat.id)

@bot.message_handler(func=lambda message: message.text == '▶️ Запустить рассылку')
def start_distribution(message):
    if script_running:
        show_main_menu(message.chat.id, "⚠️ Рассылка уже запущена!")
        return
        
    msg = bot.send_message(message.chat.id, "Введите интервал между циклами (в секундах):", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_start_distribution)

def process_start_distribution(message):
    global delay_seconds
    try:
        delay_seconds = int(message.text)
        result = start_script()
        show_main_menu(message.chat.id, result)
    except ValueError:
        show_main_menu(message.chat.id, "❌ Ошибка! Введите число.")

@bot.message_handler(func=lambda message: message.text == '⏹ Остановить рассылку')
def stop_distribution(message):
    result = stop_script()
    show_main_menu(message.chat.id, result)

@bot.message_handler(func=lambda message: message.text == '📜 Показать логи')
def show_logs(message):
    log_sender.start_sending_logs(message.chat.id)
    show_main_menu(message.chat.id, "✅ Вы подписались на получение логов. Новые логи будут приходить автоматически.")
    
    log_content = log_stream.getvalue()
    last_lines = "\n".join(log_content.splitlines()[-10:])
    if last_lines:
        bot.send_message(message.chat.id, f"<pre>Последние логи:\n{last_lines}</pre>", parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == '🚫 Остановить логи')
def stop_logs(message):
    log_sender.stop_sending_logs(message.chat.id)
    show_main_menu(message.chat.id, "Вы больше не будете получать логи.")

def log_sender_loop():
    while True:
        try:
            log_sender.send_new_logs()
            time.sleep(5)
        except Exception as e:
            logger.error(f"Ошибка в log_sender_loop: {e}")
            time.sleep(10)

if __name__ == '__main__':
    logger.info("Бот запускается...")
    
    log_thread = threading.Thread(target=log_sender_loop, daemon=True)
    log_thread.start()
    
    bot_thread = threading.Thread(target=bot.polling, kwargs={'none_stop': True})
    bot_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Получен сигнал KeyboardInterrupt, останавливаем бота...")
        stop_event.set()
        bot.stop_polling()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        stop_event.set()
        bot.stop_polling()
    finally:
        logger.info("Бот завершил работу")