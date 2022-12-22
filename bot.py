import io
import requests
from os import remove
from vkbottle import API, Keyboard, EMPTY_KEYBOARD, Text, KeyboardButtonColor, PhotoMessageUploader, CtxStorage
from vkbottle.bot import Message, Bot
from loguru import logger
from typing import List

from config import GROUP_TOKEN, USER_TOKEN
from models import User, Candidate, Photo
import db_interaction
from maintenance import string_with_born_to_age


api = API(GROUP_TOKEN)
user_api = API(USER_TOKEN)
bot = Bot(api=api)
ctx_storage = CtxStorage()
ctx_storage.set("candidate_number", 0)

async def _candidates_search(age: int, sex_id: int, city_id: str) -> List:
    sex_id = 1 if sex_id == 2 else 2
    candidates = await user_api.users.search(age_from=age - 5,age_to=age + 5,
                                             sex=sex_id, city=city_id,
                                             count=1000)
    return candidates


async def _show_candidate(candidates: List, user_id: int, candidate_number: int, is_favourite=False ):
    candidate = Candidate(vk_id=candidates.items[candidate_number].id,
        first_name=candidates.items[candidate_number].first_name,
        last_name=candidates.items[candidate_number].last_name,
        vk_link=f"https://vk.com/id{candidates.items[candidate_number].id}",
        is_favourite=is_favourite,
        user_id=user_id)
    return candidate


async def _show_photo(candidate_id: int):
    photos = await user_api.photos.get(owner_id=candidate_id,
        album_id="profile",
        extended=True,
        photo_sizes=True)
    return photos.items


async def _get_top3_photo(photos: List) -> List[str]:
        top3_photo = sorted(photos, key=lambda photo: photo.likes.count)[-1:-4:-1]
        return [f"photo{photo.owner_id}_{photo.id}" for photo in top3_photo]


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

    user = User(vk_id=user_data[0].id,
                first_name=user_data[0].first_name,
                last_name=user_data[0].last_name,
                age=string_with_born_to_age(user_data[0].bdate),
                sex_id=user_data[0].sex.value,
                city_id=user_data[0].city.id)
    db_interaction.add_person_to_db(user)
    ctx_storage.set("user", user)

    # TODO: может быть , тут найти и глобально сохранить candidates
    candidates = await _candidates_search(age=user.age,
                                            sex_id=user.sex_id,
                                            city_id=user.city_id)
    ctx_storage.set("candidates", candidates)

    await message.answer("Начинаю поиск...",
                        keyboard=keyboard)


@bot.on.message(payload={"command": "/show_candidate"})
async def show_candidate_handler(message: Message):
    keyboard = (
        Keyboard(one_time=True, inline=False)
        .add(Text("Покажи", {"command": "/show_candidate"}),
         color=KeyboardButtonColor.POSITIVE)
        .add(Text("Добавить в избранные", {"command": "/favourite_add"}),
         color=KeyboardButtonColor.PRIMARY)
        .add(Text("Список избранных", {"command": "/favourite_list"}),
         color=KeyboardButtonColor.SECONDARY)
        .add(Text("Выход", {"command": "/exit"}),
         color=KeyboardButtonColor.NEGATIVE)
    ).get_json()

    user = db_interaction.get_from_db(message.from_id, User)
    candidates = ctx_storage.get("candidates")
    candidate_number = ctx_storage.get("candidate_number")

    if candidate_number >= len(candidates.items):
        await message.answer("Просмотрены все кандидаты на данный момент")

    candidate = await _show_candidate(candidates, user.id, candidate_number)
    ctx_storage.set("candidate", candidate)
    db_interaction.add_person_to_db(candidate)         
    candidate_number += 1
    ctx_storage.set("candidate_number", candidate_number)
    photos = await _show_photo(candidate.vk_id)
    attachment = await _get_top3_photo(photos)
    await message.answer(f"По твоим параметрам нашлось {len(candidates.items)} человек.\n Вот {candidate_number}-ый:\n{candidate.first_name} {candidate.last_name}\n Ссылка на профиль: {candidate.vk_link}",
        attachment=attachment,
        keyboard=keyboard)

@bot.on.message(payload={"command": "/favourite_add"})
async def exit_handler(message: Message):
    keyboard = (
        Keyboard(one_time=True, inline=False)
        .add(Text("Покажи ещё", {"command": "/show_candidate"}),
         color=KeyboardButtonColor.POSITIVE)
        .add(Text("Выход", {"command": "/exit"}),
         color=KeyboardButtonColor.NEGATIVE)
    ).get_json()
    candidate = ctx_storage.get("candidate")
    db_interaction.change_is_favourite(candidate.vk_id)
    await message.answer(f"Добавил {candidate.first_name} {candidate.last_name} в избранные",
        keyboard=keyboard)


@bot.on.message(payload={"command": "/favourite_list"})
async def exit_handler(message: Message):
    keyboard = (
        Keyboard(one_time=True, inline=False)
        .add(Text("Покажи ещё", {"command": "/show_candidate"}),
         color=KeyboardButtonColor.POSITIVE)
        .add(Text("Выход", {"command": "/exit"}),
         color=KeyboardButtonColor.NEGATIVE)
    ).get_json()
    candidates = db_interaction.show_favourite_list()
    await message.answer(f"Вот список избранных:\n{candidates}",
        keyboard=keyboard)


@bot.on.message(payload={"command": "/exit"})
async def exit_handler(message: Message):
    db_interaction.close_session()
    await message.answer("Жаль, что ты уходишь. Приходи ещё. "\
        "Чтобы начать снова напиши /start",
        keyboard=EMPTY_KEYBOARD)


@bot.on.message()
async def echo_handler(message: Message):
    await message.answer("Я всего лишь бот. Я не могу понять такие сложные "\
        "вещи. Напиши /start, чтобы магия началась.")