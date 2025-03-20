import os
import json
import time
from telebot import types

# Путь к файлу для хранения данных
SESSION_FILE = "sessions.json"
VOTING_TIME = 180  # Время голосования в секундах (3 минуты)
VOTING_INTERVAL = 20  # Интервал обновления времени (каждые 20 секунд)

# Функция для инициализации JSON
def init_session_storage():
    if not os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

# Функция для загрузки данных
def load_sessions():
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Функция для сохранения данных
def save_sessions(sessions):
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=4, ensure_ascii=False)

# Класс для управления сессиями
class SessionManager:
    def __init__(self, bot):
        self.bot = bot
        init_session_storage()

    def create_session(self, chat_id):
        """Создает новую игровую сессию с указанием chat_id."""
        sessions = load_sessions()
        if "participants" in sessions:
            return False  # Сессия уже существует
        sessions["participants"] = []
        sessions["chat_id"] = chat_id  # Сохраняем chat_id
        save_sessions(sessions)
        return True

    def add_participant(self, user_id):
        """Добавляет участника в сессию."""
        sessions = load_sessions()
        participants = sessions.get("participants", [])
        if int(user_id) in participants:
            return False  # Участник уже добавлен
        participants.append(int(user_id))
        sessions["participants"] = participants
        save_sessions(sessions)
        return True

    def remove_participant(self, user_id):
        """Удаляет участника из сессии."""
        sessions = load_sessions()
        participants = sessions.get("participants", [])
        if str(user_id) not in participants:
            return False  # Участника нет в сессии
        participants.remove(str(user_id))
        sessions["participants"] = participants
        save_sessions(sessions)
        return True

    def list_participants(self):
        """Возвращает список участников."""
        sessions = load_sessions()
        return sessions.get("participants", [])

    def delete_session(self):
        """Удаляет сессию."""
        sessions = load_sessions()
        if "participants" in sessions:
            del sessions["participants"]
            save_sessions(sessions)
            return True
        return False

    def handle_session_buttons(self, call):
        """Обрабатывает нажатия кнопок в Telegram."""
        user_id = call.from_user.id

        if call.data == "participate":
            if self.add_participant(user_id):
                self.bot.answer_callback_query(call.id, "Вы успешно добавлены в сессию!")
            else:
                self.bot.answer_callback_query(call.id, "Вы уже участвуете!")
        elif call.data == "withdraw":
            if self.remove_participant(user_id):
                self.bot.answer_callback_query(call.id, "Вы успешно удалены из сессии!")
            else:
                self.bot.answer_callback_query(call.id, "Вы не участвуете в этой сессии!")
        elif call.data == "list":
            participants = self.list_participants()
            if not participants:
                self.bot.send_message(call.message.chat.id, "Список участников пуст.")
            else:
                participant_list = []
                for index, user_id in enumerate(participants, start=1):
                    try:
                        user_info = self.bot.get_chat(user_id)  # Получаем данные о пользователе
                        username = f"@{user_info.username}" if user_info.username else f"ID: {user_id}"
                        participant_list.append(f"#{index} | {username}")
                    except Exception as e:
                        participant_list.append(f"#{index} | Неизвестный пользователь (ID: {user_id})")
                        print(f"Ошибка получения данных для пользователя {user_id}: {e}")

                participant_list_text = "\n".join(participant_list)
                self.bot.send_message(call.message.chat.id, f"Участники сессии:\n{participant_list_text}")

    def start_voting(self, message):
        """Запускает голосование для участников."""
        sessions = load_sessions()
        participants = sessions.get("participants", [])
        
        if len(participants) <= 1:
            self.bot.send_message(message.chat.id, "Недостаточно участников для голосования.")
            return

        # Инициализация голосов, если их нет
        if "votes" not in sessions:
            sessions["votes"] = {str(user_id): {"count": 0, "voters": []} for user_id in participants}
            save_sessions(sessions)

        votes = sessions["votes"]
        end_time = time.time() + VOTING_TIME

        # Генерация кнопок
        markup = types.InlineKeyboardMarkup()
        for user_id in participants:
            try:
                user_info = self.bot.get_chat(user_id)
                username = user_info.username if user_info.username else f"ID: {user_id}"
            except Exception as e:
                username = f"ID: {user_id}"
                print(f"Ошибка получения данных для пользователя {user_id}: {e}")
            markup.add(types.InlineKeyboardButton(username, callback_data=f"vote_{user_id}"))

        # Сохраняем чат для итогов
        voting_chat_id = message.chat.id
        sessions["voting_chat_id"] = voting_chat_id
        save_sessions(sessions)

        # Отправка кнопок всем участникам
        for user_id in participants:
            self.bot.send_message(user_id, "Проголосуйте за участника:", reply_markup=markup)

        # Отслеживание голосования
        last_reported_time = None  # Для отправки оставшегося времени
        while time.time() < end_time:
            sessions = load_sessions()
            all_voters = set(v for user_data in votes.values() for v in user_data["voters"])
            if len(all_voters) == len(participants):  # Если все участники проголосовали
                self.end_voting(votes)
                return  # Завершаем голосование сразу, когда все проголосовали

            remaining_time = int(end_time - time.time())
            if remaining_time % VOTING_INTERVAL == 0 and remaining_time != last_reported_time:
                # Сообщаем оставшееся время
                last_reported_time = remaining_time
                for user_id in participants:
                    self.bot.send_message(user_id, f"Оставшееся время голосования: {remaining_time} секунд.")

            time.sleep(1)

        # Если время истекло, завершаем голосование
        self.end_voting(votes)

    def handle_vote(self, call):
        """Обрабатывает голос за участника."""
        print(f"Получен callback: {call.data}")  # Отладочная информация
        voter_id = str(call.from_user.id)
        voted_id = call.data.split("_")[1]  # Получаем ID игрока, за которого голосуют
        print(f"Голос от {voter_id} за участника {voted_id}")  # Отладочная информация

        sessions = load_sessions()
        participants = sessions.get("participants", [])
        
        print(f"participants: {participants}")  # Выводим участников
        print(f"votes: {sessions.get('votes', {})}")  # Выводим текущие голоса

        if int(voted_id) not in participants or int(voter_id) not in participants:
            self.bot.answer_callback_query(call.id, "Некорректное голосование.")
            return

        # Инициализация голосов, если они еще не созданы
        if "votes" not in sessions:
            sessions["votes"] = {}

        # Инициализация данных голосов для каждого участника, если еще не существует
        votes = sessions["votes"]
        if voted_id not in votes:
            votes[voted_id] = {"count": 0, "voters": []}

        # Проверка, что участник еще не проголосовал
        if voter_id in votes[voted_id]["voters"]:
            self.bot.answer_callback_query(call.id, "Вы уже проголосовали за этого участника.")
            return

        # Регистрируем голос
        votes[voted_id]["count"] += 1
        votes[voted_id]["voters"].append(voter_id)

        sessions["votes"] = votes
        save_sessions(sessions)

        # Подтверждаем голос участнику
        self.bot.answer_callback_query(call.id, "Ваш голос учтен!")
        self.bot.send_message(voter_id, f"Вы проголосовали за участника с ID: {voted_id}")

    def end_voting(self, votes):
        """Закрывает голосование и отправляет результаты."""
        sessions = load_sessions()  # Загружаем сессию из файла
        participants = sessions.get("participants", [])
        voting_chat_id = sessions.get("voting_chat_id")
        votes = sessions.get("votes", {}).copy()

        if not voting_chat_id:
            return

        # Формируем результаты
        result_lines = []
        max_votes = -1
        winners = []  # Для хранения участников с максимальным количеством голосов
        for user_id in participants:
            data = votes.get(str(user_id), {"count": 0, "voters": []})  # Получаем голос этого участника
            print(f"Пользователь {user_id}: {data['count']} голосов, голосующие: {data['voters']}")
            
            print(f"Получаем пользователя: {user_id}")
            try:
                user_info = self.bot.get_chat(user_id)
                username = user_info.username if user_info.username else f"ID: {user_id}"
            except Exception as e:
                print(f"Ошибка при получении данных для пользователя {user_id}: {e}")
                username = f"ID: {user_id}"
            print(f"username: {username}")

            # Если нет голосующих, выводим "Не проголосовали"
            if data["voters"]:
                voters = ", ".join([f"@{self.bot.get_chat(v).username}" if self.bot.get_chat(v).username else f"ID: {v}" for v in data["voters"]])
            else:
                voters = "Не проголосовали"
            
            result_lines.append(f"{username}: {data['count']} голосов ({voters})")
            
            # Проверяем, является ли текущий участник лидером
            if data["count"] > max_votes:
                max_votes = data["count"]
                winners = [user_id]  # Сбрасываем список и добавляем нового лидера
            elif data["count"] == max_votes:
                winners.append(user_id)  # Добавляем участника с тем же количеством голосов

        result_text = "\n".join(result_lines)

        # Логируем перед отправкой
        print(f"Результаты голосования: \n{result_text}")

        # Отправляем результаты голосования
        self.bot.send_message(voting_chat_id, f"Результаты голосования:\n{result_text}")

        if len(winners) > 1:
            try:
                winner_usernames = [
                    f"@{self.bot.get_chat(w).username}" if self.bot.get_chat(w).username else f"ID: {w}"
                    for w in winners
                ]
            except Exception as e:
                print(f"Ошибка получения информации о пользователях: {e}")
                winner_usernames = [f"ID: {w}" for w in winners]

            tie_message = (
                f"Игроки: {', '.join(winner_usernames)}\n"
                "Чтоб решить ваш спор вам следует заролить `/roll` или же аргументируйте всё решения и переголосуйте `/vote`."
            )
            self.bot.send_message(voting_chat_id, tie_message)
        else:
            winner_id = winners[0]
            try:
                user_info = self.bot.get_chat(winner_id)
                username = f"@{user_info.username}" if user_info.username else f"ID: {winner_id}"
            except Exception as e:
                username = f"ID: {winner_id}"
                print(f"Ошибка получения данных для пользователя {winner_id}: {e}")

            participants.remove(winner_id)
            self.bot.send_message(voting_chat_id, f"Нас покидает: {username}.")

        # Сбрасываем сессию
        sessions["participants"] = participants
        sessions["votes"] = {}  # Очищаем голоса (закомментировано по твоему запросу)
        save_sessions(sessions)

# Пример использования
def start_session(bot, message):
    session_manager = SessionManager(bot)

    if session_manager.create_session(message.chat.id):  # Передаем chat_id
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Участвовать", callback_data="participate"))
        markup.add(types.InlineKeyboardButton("Отказаться от участия", callback_data="withdraw"))
        markup.add(types.InlineKeyboardButton("Список участников", callback_data="list"))

        bot.send_message(
            message.chat.id,
            "Игра началась! Используйте кнопки ниже для управления участием.",
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "Сессия уже создана.")
