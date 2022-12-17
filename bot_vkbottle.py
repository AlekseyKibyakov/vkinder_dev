from dataclasses import dataclass
from vkbottle import API, Keyboard, EMPTY_KEYBOARD, Text, KeyboardButtonColor
from vkbottle.bot import Message, Bot
from loguru import logger

from config import GROUP_TOKEN
from maintenance import string_with_born_to_age


api = API(GROUP_TOKEN)
bot = Bot(api=api)

@dataclass
class User:
    """Class for keeping info about user"""
    vk_id: int
    first_name: str
    last_name: str
    age: int
    sex: int 
    city: str


@bot.on.message(text="/start")
async def start_hadler(message: Message):
    keyboard = (
        Keyboard(one_time=True, inline=False)
        .add(Text("Да", {"command": "/get_user_info"}), color=KeyboardButtonColor.POSITIVE)
        .add(Text("Нет", {"command": "/exit"}), color=KeyboardButtonColor.NEGATIVE)
    ).get_json()

    await message.answer(
            "Ищешь пару?",
            keyboard=keyboard)


@bot.on.message(payload={"command": "/get_user_info"})
async def get_user_info_handler(message: Message):
    user_data = await bot.api.users.get(message.from_id, fields=["city", "sex", "bdate"])

    #TODO: тут вызвать функцию, которая парсит user_data для добавления в бд
    #TODO: тут вызвать функцию для добавления user в бд по данным спарсенным функцией выше

    user = User(vk_id=user_data[0].id,
                first_name=user_data[0].first_name,
                last_name=user_data[0].last_name,
                age=string_with_born_to_age(user_data[0].bdate),
                sex=user_data[0].sex.value,
                city=user_data[0].city.title)
    await message.answer(user)


@bot.on.message(payload={"command": "/exit"})
async def exit_handler(message: Message):
    await message.answer("Жаль, что ты уходишь. Приходи ещё. "\
        "Чтобы начать снова напиши /start",
        keyboard=EMPTY_KEYBOARD)


@bot.on.message()
async def echo_handler(message: Message):
    await message.answer("Я всего лишь бот. Я не могу понять такие сложные "\
        "вещи. Напиши /start, чтобы магия началась.")

# bot.run_forever()
