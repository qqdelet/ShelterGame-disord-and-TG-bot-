import json
import random
import disnake
from disnake.ext import commands
from disnake.ui import Button, View
from colorama import Fore, Style

class cardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="swap_job", description="Выбрать профессию")
    async def swap_job(self, inter: disnake.CommandInteraction):
        # Загружаем данные о профессиях
        with open("cards.json", "r", encoding="utf-8") as f:
            cards_data = json.load(f)
        
        job_cards = list(cards_data['job_car'])  # Берём доступные профессии
        random.shuffle(job_cards)  # Перемешиваем профессии

        # Выбираем 3 профессии для выбора
        chosen_jobs = job_cards[:3]

        # Создаем кнопки с уникальными custom_id для каждой профессии
        job_buttons = [
            Button(label=chosen_jobs[0], custom_id=f"job_{chosen_jobs[0]}", style=disnake.ButtonStyle.primary),
            Button(label=chosen_jobs[1], custom_id=f"job_{chosen_jobs[1]}", style=disnake.ButtonStyle.primary),
            Button(label=chosen_jobs[2], custom_id=f"job_{chosen_jobs[2]}", style=disnake.ButtonStyle.primary),
        ]

        # Создаем embed с тремя профессиями
        embed = disnake.Embed(
            title="Выберите профессию",
            description="Выберите одну из предложенных профессий:",
            color=disnake.Color.gold()
        )
        embed.timestamp = disnake.utils.utcnow()

        # Создаем и отправляем View с кнопками в ЛС
        view = View()
        for button in job_buttons:
            view.add_item(button)

        await inter.user.send(embed=embed, view=view)
        await inter.response.send_message("Вы получили сообщение с выбором профессии в ЛС.", ephemeral=True)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        custom_id = inter.data['custom_id']  # Доступ к custom_id

        if custom_id.startswith("job_"):
            # Получаем профессию из custom_id
            chosen_job = custom_id.split("_")[1]

            # Загружаем данные о профессиях
            with open("cards.json", "r", encoding="utf-8") as f:
                cards_data = json.load(f)

            job_cards = list(cards_data['job_car'])
            
            if chosen_job in job_cards:
                job_cards.remove(chosen_job)  # Убираем выбранную профессию из списка

                # Обновляем файл с оставшимися профессиями
                with open("cards.json", "w", encoding="utf-8") as f:
                    cards_data['job_car'] = job_cards
                    json.dump(cards_data, f, ensure_ascii=False, indent=4)

                # Отправляем подтверждение в ЛС
                job_embed = disnake.Embed(
                    title="Вы выбрали профессию",
                    description=f"Ваша профессия: **{chosen_job}**",
                    color=disnake.Color.yellow()
                )
                job_embed.timestamp = disnake.utils.utcnow()

                await inter.user.send(embed=job_embed)  # Отправляем сообщение в ЛС

                # Подтверждение в канале, где была вызвана команда (если нужно)
                await inter.response.send_message(f"Вы выбрали профессию: **{chosen_job}**", ephemeral=True)

    @commands.slash_command(name="distribute_cards", description="Раздать игровые карты")
    async def distribute_cards(self, inter: disnake.CommandInteraction, send_special_cards: bool = False):
        # Загружаем данные о картах
        with open("cards.json", "r", encoding="utf-8") as f:
            cards_data = json.load(f)

        # Получаем участников из текущей сессии
        session_participants = self.get_session_participants()

        # Проверяем, достаточно ли уникальных карт для всех участников
        if len(session_participants) > len(cards_data['heals_cards']) or len(session_participants) > len(cards_data['age_cards']):
            await inter.response.send_message("Недостаточно уникальных карт для всех участников.")
            return

        # Перемешиваем карты
        heal_cards = list(cards_data['heals_cards'].keys())
        random.shuffle(heal_cards)

        age_cards = list(cards_data['age_cards'])
        random.shuffle(age_cards)

        job_cards = list(cards_data['job_car'])
        random.shuffle(job_cards)

        baggage_cards = list(cards_data['baggage_cards'])
        random.shuffle(baggage_cards)

        hobby_cards = list(cards_data['hobby_cards'])
        random.shuffle(hobby_cards)

        fact_cards = list(cards_data['fact_cards'])
        random.shuffle(fact_cards)

        game_mode_cards = list(cards_data['game_mode_card'].keys())
        random.shuffle(game_mode_cards)

        special_cards = list(cards_data['special_cards'])
        random.shuffle(special_cards)

        # Отправляем сценарий игры всем участникам
        game_mode_card = game_mode_cards[0]  # Берём одну карту режима игры для всех
        game_embed = disnake.Embed(
            title="Сценарий игры", 
            description=cards_data['game_mode_card'][game_mode_card],
            color=disnake.Color.dark_blue()  # Ночной цвет
        )
        await inter.response.send_message(embed=game_embed)

        # Роздаём карты участникам
        for i, participant in enumerate(session_participants):
            heal_card = heal_cards[i]
            age_card = age_cards[i]
            job_card = job_cards[i]
            baggage_card = baggage_cards[i]
            hobby_card = hobby_cards[i]
            fact_card = fact_cards[i]
            special_card = special_cards[i] if send_special_cards else None  # Определяем, отправлять ли специальную карту

            # Отправляем карты игрокам с разными цветами эмбедов
            # Здоровье - красный
            heal_embed = disnake.Embed(
                title="Здоровье", 
                description=f"{heal_card}: {cards_data['heals_cards'][heal_card]}", 
                color=disnake.Color.red()
            )
            heal_embed.timestamp = disnake.utils.utcnow()
            # Возраст - зеленый
            age_embed = disnake.Embed(
                title="Возраст", 
                description=age_card, 
                color=disnake.Color.green()
            )
            age_embed.timestamp = disnake.utils.utcnow()
            # Профессия - желтый
            job_embed = disnake.Embed(
                title="Профессия", 
                description=job_card, 
                color=disnake.Color.yellow()
            )
            job_embed.timestamp = disnake.utils.utcnow()
            # Снаряжение - коричневый
            baggage_embed = disnake.Embed(
                title="Снаряжение", 
                description=baggage_card, 
                color=disnake.Color.from_rgb(139, 69, 19)  # Коричневый
            )
            baggage_embed.timestamp = disnake.utils.utcnow()
            # Хобби - фиолетовый
            hobby_embed = disnake.Embed(
                title="Хобби", 
                description=hobby_card, 
                color=disnake.Color.purple()
            )
            hobby_embed.timestamp = disnake.utils.utcnow()
            # Факт - темно-синий
            fact_embed = disnake.Embed(
                title="Факт", 
                description=fact_card, 
                color=disnake.Color.from_rgb(0, 0, 139)  # Темно-синий
            )
            fact_embed.timestamp = disnake.utils.utcnow()
            # Специальная карта - темно-желтый, если она должна быть отправлена
            special_embed = None
            if special_card:
                special_embed = disnake.Embed(
                    title="Специальная карта", 
                    description=f"{special_card['title']}: {special_card['description']}", 
                    color=disnake.Color.from_rgb(204, 204, 0)  # Темно-желтый
                )
                special_embed.timestamp = disnake.utils.utcnow()

            # Отправляем игрокам карты
            try:
                user = await self.bot.fetch_user(participant)
                await user.send(embed=heal_embed)
                await user.send(embed=age_embed)
                await user.send(embed=job_embed)
                await user.send(embed=baggage_embed)
                await user.send(embed=hobby_embed)
                await user.send(embed=fact_embed)
                if special_embed:
                    await user.send(embed=special_embed)
            except disnake.errors.NotFound:
                await inter.response.send_message(f"Не удалось найти пользователя {participant}, не отправлена карта.")

        await inter.followup.send("Карты были успешно розданы всем участникам сессии.")

    def get_session_participants(self):
        # Загружаем сессии из файла
        with open("sessions.json", "r", encoding="utf-8") as f:
            sessions_data = json.load(f)

        # Получаем участников из статической сессии (сессия 1)
        session_participants = sessions_data["1"]
        
        return session_participants

def setup(bot: commands.Bot):
    bot.add_cog(cardCog(bot))
    print(f'{Fore.LIGHTRED_EX}{__name__} {Fore.GREEN} + {Style.RESET_ALL}')
