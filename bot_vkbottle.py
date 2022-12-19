import requests
from dataclasses import dataclass
from os import remove
from vkbottle import API, Keyboard, EMPTY_KEYBOARD, Text, KeyboardButtonColor, PhotoMessageUploader
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
bot.candidate_number = 0
bot.user = "" # это времяночка

async def _candidates_search(age: int, sex_id: int, city_id: str) -> List:
    sex_id = 1 if sex_id == 2 else 2
    candidates = await user_api.users.search(age_from=age - 5,age_to=age + 5,
                                             sex=sex_id, city=city_id,
                                             count=1000)
    return candidates


async def _show_candidate(candidates: List, candidate_number: int, user_id: int):
    candidate = Candidate(vk_id=candidates.items[candidate_number].id,
        first_name=candidates.items[candidate_number].first_name,
        last_name=candidates.items[candidate_number].last_name,
        vk_link=f"https://vk.com/id{candidates.items[candidate_number].id}",
        is_favourite=False,
        user_id=user_id)
    
    db_interaction.add_person_to_db(candidate)                                           
    return candidate

async def _show_photo(candidate_id: int) -> str:
    photos = await user_api.photos.get(owner_id=candidate_id,
        album_id="profile",
        extended=True,
        photo_sizes=True)
    return photos.items


async def _get_attachment(top3_photos_list: List[str]) -> List:
    attachment = []
    photo_uploader = PhotoMessageUploader(bot.api)
    for index, photo_link in enumerate(top3_photos_list):
        file_name = f"img{index}.jpg"
        r = requests.get(photo_link)
        with open(file_name, 'wb') as download_file:
            for chunk in r.iter_content(chunk_size=128):
                download_file.write(chunk)
        upload_photo = await photo_uploader.upload(file_name)
        attachment.append(upload_photo)
        remove(file_name)
    return attachment


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

    bot.user = User(vk_id=user_data[0].id,
                first_name=user_data[0].first_name,
                last_name=user_data[0].last_name,
                age=string_with_born_to_age(user_data[0].bdate),
                sex_id=user_data[0].sex.value,
                city_id=user_data[0].city.id)

    db_interaction.add_person_to_db(bot.user)
    candidates = await _candidates_search(age=bot.user.age,
                                         sex_id=bot.user.sex_id,
                                         city_id=bot.user.city_id)
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

    #это времяночка:
    candidates = await _candidates_search(age=bot.user.age,
                                         sex_id=bot.user.sex_id,
                                         city_id=bot.user.city_id)

    if bot.candidate_number >= len(candidates.items):
        await message.answer("Просмотрены все кандидаты на данный момент")

    candidate = await _show_candidate(candidates, bot.candidate_number)


    bot.candidate_number += 1
    # photos = await _show_photo(candidate.vk_id)

    #TODO: тут вызвать функцию получения топ-3 фото кандидата
   
    #это "времяночка". тут должно быть top3_photots = await _get_top3_photos(candidate.id)
    top3_photos = ["https://sun7.userapi.com/sun7-13/s/v1/ig1/zpeeTSzA3_sBvdm5kRIzwWhc8_TDP0ZZ0jSuxN9k2jJJRYz5d2cy6AlV5Te9RwvbFS9YYPgG.jpg?size=1620x1620&quality=96&type=album",
    "https://sun7.userapi.com/sun7-16/s/v1/ig2/kR7reE48qlTNv_FrQevoIB8mL_05b6tNogjosGPm_1krpP1BbY9fLKnGItpIEimy04wG9Ayf-uvIhr7dDSD_vp_P.jpg?size=863x1080&quality=96&type=album",
    "https://sun9-east.userapi.com/sun9-44/s/v1/ig1/-PFsHNz6vqWLcAyCIMpDxeOKybmfWbSgOjETWblUFFUV27TkLBWmnE19Ctem0jhRVy6NhiSZ.jpg?size=960x1280&quality=96&type=album"]

    attachment = await _get_attachment(top3_photos)
    
    await message.answer(f"По твоим параметрам нашлось {len(candidates.items)} человек.\n Вот {bot.candidate_number}-ый:\n{candidate}",
        attachment=attachment,
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