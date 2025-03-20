import json
import random
from telebot import types

class CardManager:
    def __init__(self, bot):
        self.bot = bot
        self.cards_data = self.load_cards()

    def load_cards(self):
        """Загружает данные из файла cards.json."""
        with open("cards.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def send_job_selection(self, chat_id):
        """Отправляет выбор профессии пользователю."""
        job_cards = list(self.cards_data['job_car'])
        random.shuffle(job_cards)
        chosen_jobs = job_cards[:3]  # Выбираем три профессии

        markup = types.InlineKeyboardMarkup()
        for job in chosen_jobs:
            markup.add(types.InlineKeyboardButton(job, callback_data=f"job_{job}"))

        self.bot.send_message(chat_id, "Выберите одну из предложенных профессий:", reply_markup=markup)

    def handle_job_selection(self, call):
        """Обрабатывает выбор профессии."""
        chosen_job = call.data.split("_")[1]
        self.bot.answer_callback_query(call.id, f"Вы выбрали профессию: {chosen_job}")
        self.bot.send_message(call.message.chat.id, f"Ваша профессия: {chosen_job}")

    def distribute_cards(self, chat_id, participants, send_special_cards=False):
        """Распределяет карточки среди участников и отправляет их."""
        # Проверяем, достаточно ли уникальных карт
        if (
            len(participants) > len(self.cards_data['heals_cards']) or
            len(participants) > len(self.cards_data['age_cards']) or
            len(participants) > len(self.cards_data['job_car']) or
            len(participants) > len(self.cards_data['baggage_cards']) or
            len(participants) > len(self.cards_data['hobby_cards']) or
            len(participants) * 2 > len(self.cards_data['fact_cards'])
        ):
            self.bot.send_message(chat_id, "Недостаточно уникальных карт для всех участников.")
            return

        # Перемешиваем карты
        heal_cards = list(self.cards_data['heals_cards'].keys())
        random.shuffle(heal_cards)

        age_cards = list(self.cards_data['age_cards'])
        random.shuffle(age_cards)

        job_cards = list(self.cards_data['job_car'])
        random.shuffle(job_cards)

        baggage_cards = list(self.cards_data['baggage_cards'])
        random.shuffle(baggage_cards)

        hobby_cards = list(self.cards_data['hobby_cards'])
        random.shuffle(hobby_cards)

        fact_cards = list(self.cards_data['fact_cards'])
        random.shuffle(fact_cards)

        # Работа с игровым сценарием (game_mode_card)
        if isinstance(self.cards_data['game_mode_card'], list):
            # Выбираем случайный сценарий из списка
            game_mode_card = random.choice(self.cards_data['game_mode_card'])
            sent_message = self.bot.send_message(chat_id, f"Сценарий игры: {game_mode_card}")
            
            # Закрепляем отправленное сообщение
            self.bot.pin_chat_message(chat_id, sent_message.message_id)
        else:
            self.bot.send_message(chat_id, "Ошибка: данные сценариев игры некорректны.")


        # Специальные карты
        special_cards = list(self.cards_data['special_cards'])
        random.shuffle(special_cards)

        for i, participant in enumerate(participants):
            if i >= len(heal_cards):  # Если карт меньше, чем участников
                break

            # Раздача уникальных карт
            heal_card = heal_cards.pop()
            age_card = age_cards.pop()
            job_card = job_cards.pop()
            baggage_card = baggage_cards.pop()
            hobby_card = hobby_cards.pop()
            fact_card_1 = fact_cards.pop()  # Первый факт
            fact_card_2 = fact_cards.pop()  # Второй факт
            special_card = special_cards.pop() if send_special_cards else None  # Если отправлять спец карту

            try:
                # Отправляем карты игрокам
                self.bot.send_message(participant, f"💉 Здоровье:\n{heal_card} - {self.cards_data['heals_cards'][heal_card]}")
                self.bot.send_message(participant, f"🎂 Возраст:\n{age_card}")
                self.bot.send_message(participant, f"👔 Профессия:\n{job_card}")
                self.bot.send_message(participant, f"🎒 Снаряжение:\n{baggage_card}")
                self.bot.send_message(participant, f"🎨 Хобби:\n{hobby_card}")
                self.bot.send_message(participant, f"📜 Факт#1:\n{fact_card_1}")
                self.bot.send_message(participant, f"📜 Факт#2:\n{fact_card_2}")
                if special_card:
                    self.bot.send_message(participant, f"⚡ Специальная карта:\n{special_card}")
            except Exception as e:
                self.bot.send_message(chat_id, f"Не удалось отправить карты участнику {participant}: {str(e)}")
                print(f"Ошибка при отправке карт участнику {participant}: {str(e)}")




# Подключение к основному боту
def setup(bot):
    card_manager = CardManager(bot)

    # Загрузим данные о сессии заранее
    def load_session():
        with open('sessions.json', 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        return session_data

    session_data = load_session()  # Загружаем данные о сессии сразу при инициализации

    @bot.message_handler(commands=['swap_job'])
    def handle_swap_job(message):
        card_manager.send_job_selection(message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("job_"))
    def handle_job_click(call):
        card_manager.handle_job_selection(call)

    @bot.message_handler(commands=['distribute_cards'])
    def handle_distribute_cards(message):
        # Проверяем, если в сообщении есть слово "special", то включаем специальные карты
        send_special_cards = 'special' in message.text.lower()
        participants = session_data['participants']  # Список участников из загруженной сессии
        card_manager.distribute_cards(message.chat.id, participants, send_special_cards)

