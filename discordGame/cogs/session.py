import os
import json

import disnake
from typing import List
from disnake import Embed
from disnake.ui import Button, View
from disnake.ext import commands

from colorama import Fore, Style

# Путь к файлу для хранения данных
SESSION_FILE = "sessions.json"

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

class RegistrationView(disnake.ui.View):
    def __init__(self, bot, session_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.session_id = str(session_id)  # ID сессии как строка для JSON

    @disnake.ui.button(label="Участвовать", style=disnake.ButtonStyle.success)
    async def participate_button(self, button: Button, interaction: disnake.MessageInteraction):
        user_id = str(interaction.user.id)  # ID пользователя как строка
        user_mention = interaction.user.mention

        # Загрузка текущих данных
        sessions = load_sessions()

        # Если сессии нет, создаем новую
        if self.session_id not in sessions:
            sessions[self.session_id] = []

        # Проверка, добавлен ли пользователь
        if user_id in sessions[self.session_id]:
            await interaction.response.send_message(f"{user_mention}, вы уже участвуете!", ephemeral=True)
        else:
            sessions[self.session_id].append(user_id)  # Добавляем пользователя
            save_sessions(sessions)  # Сохраняем изменения
            await interaction.response.send_message(f"{user_mention}, вы успешно добавлены в список участников!", ephemeral=True)

    @disnake.ui.button(label="Отказаться от участия", style=disnake.ButtonStyle.danger)
    async def withdraw_button(self, button: Button, interaction: disnake.MessageInteraction):
        user_id = str(interaction.user.id)  # ID пользователя как строка
        user_mention = interaction.user.mention

        # Загрузка текущих данных
        sessions = load_sessions()

        # Проверка, есть ли сессия
        if self.session_id not in sessions or user_id not in sessions[self.session_id]:
            await interaction.response.send_message(f"{user_mention}, вы не участвуете в этой сессии!", ephemeral=True)
        else:
            sessions[self.session_id].remove(user_id)  # Убираем пользователя из списка
            save_sessions(sessions)  # Сохраняем изменения
            await interaction.response.send_message(f"{user_mention}, вы успешно отказались от участия.", ephemeral=True)

    @disnake.ui.button(label="Список участников", style=disnake.ButtonStyle.primary)
    async def list_button(self, button: Button, interaction: disnake.MessageInteraction):
        sessions = load_sessions()  # Загружаем данные

        # Получаем список участников
        participants = sessions.get(self.session_id, [])
        if not participants:
            await interaction.response.send_message("Список участников пуст.", ephemeral=True)
        else:
            participants_list = "\n".join(f"<@{user_id}>" for user_id in participants)
            await interaction.response.send_message(f"Участники сессии:\n{participants_list}", ephemeral=True)

class SessionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_session_storage()  # Инициализация хранилища

    @commands.slash_command(description="Создать игровую сессию с кнопками")
    async def start_session(self, inter: disnake.ApplicationCommandInteraction):
        embed = disnake.Embed(
            title="Бункер",
            description=("""
                ```
Вам предстоит провести в бункере 1 год, пережидая самый опасный период катастрофы.
В бункере есть вода, еда и спальные места. Каждый раунд вы будете исследовать ваш бункер
и постепенно открывать карты Бункера с новой информацией.
                ```
            """),
            color=disnake.Color.blue()
        )
        embed.set_footer(text="/help -- чтоб прочитать правила и суть игры")
        
        # Уникальный ID сессии (можно использовать автоинкремент или GUID)
        session_id = 1  # Здесь можно использовать генерацию уникальных ID
        view = RegistrationView(self.bot, session_id)
        
        await inter.response.send_message(embed=embed, view=view)

def setup(bot: commands.Bot):
    bot.add_cog(SessionCog(bot))
    print(f'{Fore.LIGHTRED_EX}{__name__} {Fore.GREEN}+{Style.RESET_ALL}')
