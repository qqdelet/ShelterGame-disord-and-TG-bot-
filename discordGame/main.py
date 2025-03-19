import os
import json
import disnake
from disnake.ext import commands
from colorama import Fore, Style, init
from datetime import datetime

init()

intents = disnake.Intents.default()
intents.members = True  
intents.message_content = True

bot = commands.Bot(command_prefix="/", help_command=None, intents=disnake.Intents.all(), test_guilds=[1220705242014941306])
startTime = None

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
token = config['token']
guest_R_ID = config['guest_role_id']
dev_ids = config['dev_id']

@bot.event
async def on_ready():
    global startTime
    startTime = datetime.now()

    now = datetime.now()
    formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
    
    border = "═" * 40
    print(f"{Fore.LIGHTYELLOW_EX}{border}{Style.RESET_ALL}")
    print(f"Бот запущен как:{Fore.LIGHTMAGENTA_EX} {bot.user.name}{Style.RESET_ALL}")
    print(f"Версия disnake: {Fore.LIGHTGREEN_EX}{disnake.__version__}{Style.RESET_ALL}")
    print(f"Время запуска: {Fore.LIGHTWHITE_EX}{formatted_time}{Style.RESET_ALL}")
    print(f"{Fore.LIGHTYELLOW_EX}{border}{Style.RESET_ALL}")
    
    activity = disnake.Activity(name="В случае проблем читай описание.",type=disnake.ActivityType.playing,details="IDK")
    await bot.change_presence(status=disnake.Status.online, activity=activity)

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

@bot.slash_command(name="worktime", description="Показывает сколько времени активен бот.")
async def worktime(ctx):
    emb = disnake.Embed(title="Время работы бота", color=disnake.Color.from_rgb(255, 255, 255))

    uptime = datetime.now() - startTime
    formatted_uptime = format_uptime(uptime)

    emb.add_field(name="", value=f"{formatted_uptime}")

    await ctx.response.send_message(embed=emb)
    print(f"Бот уже работает на протяжении: {formatted_uptime}")

@bot.slash_command(description="Перезагрузить бота или указанный ког")
async def reload(interaction: disnake.ApplicationCommandInteraction, cog: str = None):
    if interaction.author.id not in dev_ids:
        await interaction.response.send_message("У вас нет прав для использования этой команды.", ephemeral=True)
        return

    if cog:
        try:
            bot.reload_extension(f"cogs.{cog}")
            await interaction.response.send_message(f"Ког '{cog}' успешно перезагружен.")
        except commands.ExtensionNotLoaded:
            await interaction.response.send_message(f"Ког '{cog}' не загружен.")
        except commands.ExtensionNotFound:
            await interaction.response.send_message(f"Ког '{cog}' не найден.")
        except Exception as e:
            await interaction.response.send_message(f"Ошибка при перезагрузке кога '{cog}': {str(e)}")
    else:
        try:
            for extension in list(bot.extensions.keys()):
                bot.reload_extension(extension)
            await interaction.response.send_message("Бот полностью перезагружен.")
        except Exception as e:
            await interaction.response.send_message(f"Ошибка при перезагрузке бота: {str(e)}")

@bot.slash_command(name="ping", description="Показывает задержку бота")
async def ping(ctx):
    emb = disnake.Embed(title="Ping", color=disnake.Color.from_rgb(255, 255, 255))
    pinged = round(bot.latency * 1000)
    emb.add_field(name="", value=f"{pinged} мс")  

    await ctx.response.send_message(embed=emb)   

@bot.slash_command(name="cls", description="очистка консоли")
async def cls_func(interaction): 
    member = interaction.user
    required_roles = [".", "code"]
    user_roles = [role.name.lower() for role in member.roles]
    
    if not any(role in user_roles for role in required_roles):
        await interaction.response.send_message(f"{member.mention} У вас нет необходимой роли для использования этой кнопки.", ephemeral=True)
        return
    
    else:
        await interaction.response.send_message("Консоль была очищена")
        
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Очистка консоли успешно выполнена")
        
        except Exception as e:
            print(f"Ошибка при очистке консоли: {e}")

@bot.event
async def on_message(message):
    guild_name = "DM" if not message.guild else message.guild.name
    channel_name = message.channel.name if hasattr(message.channel, 'name') else ""

    if channel_name:
        print(f'{Style.RESET_ALL}[{guild_name}] #{channel_name} - {message.author}: {message.content}')
    
    else:
        print(f'{Style.RESET_ALL}[{guild_name}] {message.author}: {message.content}')

bot.load_extensions("cogs")
bot.run(token)  