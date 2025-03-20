import telebot
import os
import json
from datetime import datetime
from session import SessionManager,start_session
from cards import setup as setup_cards

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
token = config['token']
dev_ids = config['dev_id']

bot = telebot.TeleBot(token)
session_manager = SessionManager(bot)
setup_cards(bot)
start_time = None

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, f"Привет, {message.from_user.first_name}! Я готов к работе.")

@bot.message_handler(commands=['roll'])
def roll_command(message):
    import random
    random_number = random.randint(1, 100)
    bot.reply_to(message, f"🎲 Выпало число: {random_number}")

@bot.message_handler(commands=['start_session'])
def start_session_handler(message):
    start_session(bot, message)

@bot.message_handler(commands=['close_session'])
def close_session_handler(message):    
    if session_manager.delete_session():
        bot.reply_to(message, "Сессия успешно завершена!")
    else:
        bot.reply_to(message, "Нет активной сессии для завершения.")

@bot.message_handler(commands=['vote'])
def vote_command(message):
    session_manager = SessionManager(bot)
    session_manager.start_voting(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
def handle_vote(call):
    session_manager.handle_vote(call)

@bot.callback_query_handler(func=lambda call: call.data in ["participate", "withdraw", "list"])
def handle_session_buttons(call):
    session_manager.handle_session_buttons(call)

# Форматирование времени работы
def format_uptime(uptime):
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"📅 Дней: {days}")
    if hours > 0:
        parts.append(f"⏰ Часов: {hours}")
    if minutes > 0:
        parts.append(f"🕑 Минут: {minutes}")
    if seconds > 0 or not parts:
        parts.append(f"⏲️ Секунд: {seconds}")

    return "\n".join(parts)

# Обработчик команды /worktime
@bot.message_handler(commands=['worktime'])
def worktime_command(message):
    if start_time is None:
        bot.reply_to(message, "Бот только что запущен, время работы ещё не зафиксировано.")
    else:
        uptime = datetime.now() - start_time
        formatted_uptime = format_uptime(uptime)
        bot.reply_to(message, f"Бот работает уже:\n{formatted_uptime}")

# Обработчик команды /reload
@bot.message_handler(commands=['reload'])
def reload_command(message):
    if message.from_user.id not in dev_ids:
        bot.reply_to(message, "У вас нет прав для использования этой команды.")
        return
    
    bot.reply_to(message, "Перезагрузка пока недоступна для Telegram-бота. Поддержка когов отсутствует в telebot.")

# Обработчик команды /ping
@bot.message_handler(commands=['ping'])
def ping_command(message):
    bot.reply_to(message, "Понг! Бот работает.")

# Обработчик команды /cls
@bot.message_handler(commands=['cls'])
def cls_command(message):
    if message.from_user.id not in dev_ids:
        bot.reply_to(message, "У вас нет прав для использования этой команды.")
        return

    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        bot.reply_to(message, "Консоль была очищена.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка при очистке консоли: {str(e)}")

# Обработчик входящих сообщений
@bot.message_handler(func=lambda m: True)
def log_message(message):
    chat_name = message.chat.title if message.chat.type != "private" else "Личные сообщения"
    print(f"[{chat_name}] {message.from_user.first_name}: {message.text}")

# Запуск бота
if __name__ == "__main__":
    start_time = datetime.now()
    print(f"Бот запущен в {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    bot.infinity_polling()
