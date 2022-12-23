from time import sleep
from typing import List
from vkbottle import API, Keyboard, EMPTY_KEYBOARD, Text, KeyboardButtonColor, PhotoMessageUploader, CtxStorage
from vkbottle.bot import Message, Bot
from loguru import logger

import db_interaction
from config import GROUP_TOKEN
from models import User, Candidate, Photo
from maintenance import _make_user, _candidate_search, _make_candidate, _get_photos, _make_photo, _get_top3_photo


api = API(GROUP_TOKEN)
bot = Bot(api=api)
ctx_storage = CtxStorage()
ctx_storage.set("candidate_number", 0)


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

    user = await _make_user(user_data)
    db_interaction.add_person_to_db(user)
    db_interaction.commit_session()
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

    candidate_number = ctx_storage.get("candidate_number")
    user = db_interaction.get_from_db(vk_id=message.from_id, model=User)
    candidate_from_vk = await _candidate_search(age=user.age,
                                        sex_id=user.sex_id,
                                        city_id=user.city_id,
                                        offset=candidate_number)

    # def _candidate_can_access_closed_checker(candidate_from_vk):
    #     if not candidate_from_vk.can_access_closed:


    candidate = await _make_candidate(candidate_from_vk, message.from_id)
    db_interaction.add_person_to_db(candidate)
    db_interaction.commit_session()
    photos = await _get_photos(candidate.vk_id)
    top3_photo = await _get_top3_photo(photos)
    for photo_data in top3_photo:
            photo = await _make_photo(photo_data, candidate.vk_id)
            db_interaction.add_photos_to_db(photo)
            db_interaction.commit_session()

    candidate_number += 1
    ctx_storage.set("candidate_number", candidate_number)
    await message.answer(f"{candidate.first_name} {candidate.last_name}\n Ссылка на профиль: {candidate.vk_link}",
                         attachment=top3_photo,
                         keyboard=keyboard)