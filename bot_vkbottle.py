from dataclasses import dataclass
from vkbottle import API, Keyboard, EMPTY_KEYBOARD, Text, KeyboardButtonColor
from vkbottle.bot import Message, Bot
from loguru import logger

from config import GROUP_TOKEN, USER_TOKEN
from maintenance import string_with_born_to_age


api = API(GROUP_TOKEN)
user_api = API(USER_TOKEN)
bot = Bot(api=api)
bot.candidate_number = 0

@dataclass
class User:
    """Class for keeping info about user"""
    vk_id: int
    first_name: str
    last_name: str
    age: int
    sex_id: int 
    city_id: int

@dataclass
class Candidate:
    """Class for keeping info about candidate"""
    vk_id: int
    first_name: str
    last_name: str
    vk_link: str
    is_favourite: bool

    def __str__(self):
        return f"{self.first_name}, {self.last_name}, {self.vk_link}"


async def _candidates_search(age: int, sex_id: int, city_id: str) -> list:
    sex_id = 1 if sex_id == 2 else 2
    candidates = await user_api.users.search(age_from=age - 5,age_to=age + 5,
                                             sex=sex_id, city=city_id,
                                             count=1000)
    return candidates


async def _show_candidate(candidates: list, candidate_number: int):
    return Candidate(vk_id=candidates.items[candidate_number].id,
        first_name=candidates.items[candidate_number].first_name,
        last_name=candidates.items[candidate_number].last_name,
        vk_link=f"https://vk.com/id{candidates.items[candidate_number].id}",
        is_favourite=False)


async def _show_photo(candidate_id: int) -> str:
    photos = await user_api.photos.get(owner_id=candidate_id,
        album_id="profile",
        extended=True,
        photo_sizes=True)
    return photos.items


@bot.on.message(payload={"command": "start"})
@bot.on.message(text="/start")
async def start_hadler(message: Message):
    keyboard = (
        Keyboard(one_time=True, inline=False)
        .add(Text("Да", {"command": "/get_user_info"}),
         color=KeyboardButtonColor.POSITIVE)
        .add(Text("Нет", {"command": "/exit"}),
         color=KeyboardButtonColor.NEGATIVE)
    ).get_json()

    await message.answer("Ищешь пару?", keyboard=keyboard)


@bot.on.message(payload={"command": "/get_user_info"})
async def get_user_info_handler(message: Message):
    keyboard = (
        Keyboard(one_time=True, inline=False)
        .add(Text("Покажи", {"command": "/show_candidate"}),
         color=KeyboardButtonColor.POSITIVE)
        .add(Text("Выход", {"command": "/exit"}),
         color=KeyboardButtonColor.NEGATIVE)
    ).get_json()

    user_data = await bot.api.users.get(message.from_id,
     fields=["city", "sex", "bdate"])

    #TODO: тут вызвать функцию, которая парсит user_data для добавления в бд
    #TODO: тут вызвать функцию для добавления user в бд по данным спарсенным функцией выше

    user = User(vk_id=user_data[0].id,
                first_name=user_data[0].first_name,
                last_name=user_data[0].last_name,
                age=string_with_born_to_age(user_data[0].bdate),
                sex_id=user_data[0].sex.value,
                city_id=user_data[0].city.id)

    #TODO: (?) тут вызвать функцию получние из бд данных юзера, которая возвращает объект user класса User

    candidates = await _candidates_search(age=user.age,
                                         sex_id=user.sex_id,
                                         city_id=user.city_id)
    await message.answer("Начинаю поиск...",
                        keyboard=keyboard)


@bot.on.message(payload={"command": "/show_candidate"})
async def show_candidate_handler(message: Message):
    keyboard = (
        Keyboard(one_time=True, inline=False)
        .add(Text("Покажи", {"command": "/show_candidate"}),
         color=KeyboardButtonColor.POSITIVE)
        .add(Text("Выход", {"command": "/exit"}),
         color=KeyboardButtonColor.NEGATIVE)
    ).get_json()

    #TODO: (?) тут вызвать функцию получния из бд данных юзера, которая возвращает объект user класса User

    candidates = await _candidates_search(age=30, sex_id=2, city_id=40)
    candidate = await _show_candidate(candidates, bot.candidate_number)
    photos = await _show_photo(candidate.vk_id)
    #TODO: тут вызвать функцию получения топ-3 фото кандидата

    bot.candidate_number += 1
    await message.answer(f"По твоим параметрам нашлось {len(candidates.items)} человек.\n Вот {bot.candidate_number}-ый:\n{candidate}",
        keyboard=keyboard)


@bot.on.message(payload={"command": "/exit", "candidate_number": any})
async def exit_handler(message: Message):
    await message.answer("Жаль, что ты уходишь. Приходи ещё. "\
        "Чтобы начать снова напиши /start",
        keyboard=EMPTY_KEYBOARD)


@bot.on.message()
async def echo_handler(message: Message):
    await message.answer("Я всего лишь бот. Я не могу понять такие сложные "\
        "вещи. Напиши /start, чтобы магия началась.")