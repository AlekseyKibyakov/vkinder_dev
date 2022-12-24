'''
The script with the logic of the bot to find candidates for romantic dates
'''
from time import sleep
from vkbottle import API, Keyboard, EMPTY_KEYBOARD, Text, KeyboardButtonColor,\
 CtxStorage
from vkbottle.bot import Message, Bot

import db_interaction
from config import GROUP_TOKEN
from models import User
from maintenance import _make_user, _candidate_search, _make_candidate,\
    _get_photos, _make_photo, _get_top3_photo


api = API(GROUP_TOKEN)
bot = Bot(api=api)
ctx_storage = CtxStorage()


@bot.on.message(payload={"command": "start"})
@bot.on.message(text="/start")
async def start_handler(message: Message):
    ''' The function-handler for greeting the user.'''
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
    ''' The function-handler for collecting data from the user.'''
    keyboard = (
        Keyboard(one_time=True, inline=False)
        .add(Text("Покажи", {"command": "/show_candidate"}),
             color=KeyboardButtonColor.POSITIVE)
        .add(Text("Выход", {"command": "/exit"}),
             color=KeyboardButtonColor.NEGATIVE)
    ).get_json()

    user_data = await bot.api.users.get(message.from_id, fields=[
        "city", "sex", "bdate"])

    user = await _make_user(user_data)
    db_interaction.add_person_to_db(user)
    db_interaction.commit_session()
    ctx_storage.set(f"offset_{message.from_id}", 0)
    await message.answer("Начинаю поиск...", keyboard=keyboard)


@bot.on.message(payload={"command": "/show_candidate"})
async def show_candidate_handler(message: Message):
    ''' The function-handler for finding a candidate
    and sending candidate data to the user.'''
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

    offset = ctx_storage.get(f"offset_{message.from_id}")
    user = db_interaction.get_from_db(vk_id=message.from_id, model=User)
    candidate_from_vk, offset = await _candidate_search(age=user.age,
                                                        sex_id=user.sex_id,
                                                        city_id=user.city_id,
                                                        offset=offset)

    candidate = await _make_candidate(candidate_from_vk, message.from_id)

    photos = await _get_photos(candidate_from_vk.id)
    top3_photo = await _get_top3_photo(photos)

    db_interaction.add_person_to_db(candidate)
    db_interaction.commit_session()
    for photo_data in top3_photo:
        photo = await _make_photo(photo_data, candidate.vk_id)
        db_interaction.add_photos_to_db(photo)
        db_interaction.commit_session()

    offset += 1
    ctx_storage.set(f"offset_{message.from_id}", offset)
    ctx_storage.set(f"candidate_{message.from_id}", candidate)
    await message.answer(
        f"{candidate.first_name} {candidate.last_name}\n{candidate.vk_link}",
        attachment=top3_photo,
        keyboard=keyboard)


@bot.on.message(payload={"command": "/favourite_add"})
async def favourite_add_handler(message: Message):
    ''' The function-handler for adding a candidate to the favorites list.'''
    keyboard = (
        Keyboard(one_time=True, inline=False)
        .add(Text("Покажи ещё", {"command": "/show_candidate"}),
             color=KeyboardButtonColor.POSITIVE)
        .add(Text("Выход", {"command": "/exit"}),
             color=KeyboardButtonColor.NEGATIVE)
    ).get_json()
    candidate = ctx_storage.get(f"candidate_{message.from_id}")
    db_interaction.change_is_favourite(candidate.vk_id)
    await message.answer(
        f"Добавил {candidate.first_name} {candidate.last_name} в избранные",
        keyboard=keyboard)


@bot.on.message(payload={"command": "/favourite_list"})
async def favourite_list_handler(message: Message):
    ''' The function-handler for displaying showing the list of favorites.'''
    keyboard = (
        Keyboard(one_time=True, inline=False)
        .add(Text("Покажи ещё", {"command": "/show_candidate"}),
             color=KeyboardButtonColor.POSITIVE)
        .add(Text("Выход", {"command": "/exit"}),
             color=KeyboardButtonColor.NEGATIVE)
    ).get_json()
    candidates = db_interaction.show_favourite_list()

    for candidate in candidates:
        await message.answer(
            f"Вот список избранных:\n{candidate[0].first_name} \
                {candidate[0].last_name}\n{candidate[0].vk_link}\n",
            attachment=[photo.vk_link for photo in candidate[1]],
            keyboard=keyboard)
        sleep(0.5)


@bot.on.message(payload={"command": "/exit"})
async def exit_handler(message: Message):
    ''' The function-handler to say goodbye to the user '''
    db_interaction.close_session()
    await message.answer(
        "Жаль, что ты уходишь. Приходи ещё. \
            Чтобы начать снова напиши /start",
        keyboard=EMPTY_KEYBOARD)


@bot.on.message()
async def echo_handler(message: Message):
    ''' Simple function-handler with echo logic'''
    await message.answer("Я всего лишь бот. Я не могу понять такие сложные \
        вещи. Напиши /start, чтобы магия началась.")
