from typing import List
from vkbottle import API, Keyboard, EMPTY_KEYBOARD, Text, KeyboardButtonColor, PhotoMessageUploader, CtxStorage
from vkbottle.bot import Message, Bot
from loguru import logger

import db_interaction
from config import GROUP_TOKEN, USER_TOKEN
from models import User, Candidate, Photo
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
                                             count=1000, fields=["is_closed"],
                                             is_closed=False)
    return candidates.items


async def _make_candidate(candidate, user_vk_id: int) -> Candidate:
    return Candidate(vk_id=candidate.id,
                     first_name=candidate.first_name,
                     last_name=candidate.last_name,
                     vk_link=f"https://vk.com/id{candidate.id}",
                     is_favourite=False,
                     user_vk_id=user_vk_id)


async def _make_photo(vk_link:str, candidate_vk_id: int) -> Photo:
    return Photo(vk_link=vk_link, candidate_vk_id=candidate_vk_id)


async def _get_photos(candidate_id: int) -> List:
    photos = await user_api.photos.get(owner_id=candidate_id,
                                       album_id="profile",
                                       extended=True)
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
    db_interaction.commit_session()
    candidates = await _candidates_search(age=user.age,
                                          sex_id=user.sex_id,
                                          city_id=user.city_id)

    for candidate in candidates:
        candidate = await _make_candidate(candidate, user.vk_id)
        db_interaction.add_person_to_db(candidate)
        all_photos = await _get_photos(candidate.vk_id)
        top3_photo = await _get_top3_photo(all_photos)

        for photo_data in top3_photo:
            photo = await _make_photo(photo_data, candidate.vk_id)
            db_interaction.add_photos_to_db(photo)
    db_interaction.commit_session()

    await message.answer("Начинаю поиск...", keyboard=keyboard)


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

    #TODO: тут сделать проверку, не закончились ли кандидаты, а если закончились,
    # то await message.answer("Просмотрены все кандидаты на данный момент")

    candidate_dict = db_interaction.get_candidate_with_photo(candidate_number)
    attachment = candidate["photos"]
    await message.answer(f"По твоим параметрам нашлось n человек.\n Вот {candidate_number}-ый:\n{candidate['candidate'].first_name} {candidate['candidate'].last_name}\n Ссылка на профиль: {candidate['candidate'].vk_link}",
        attachment=attachment,
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