import datetime as dt
from typing import List
from vkbottle import API
from config import USER_TOKEN
from models import User, Candidate, Photo


user_api = API(USER_TOKEN)

def _string_with_born_to_age(born: str) -> int:
    today = dt.date.today()
    born = dt.datetime.strptime(born, "%d.%m.%Y")
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _get_opposite_sex(sex_id: int) -> int:
    return 1 if sex_id == 2 else 2


async def _make_user(user_data):
    return User(vk_id=user_data[0].id,
                first_name=user_data[0].first_name,
                last_name=user_data[0].last_name,
                age=_string_with_born_to_age(user_data[0].bdate),
                sex_id=user_data[0].sex.value,
                city_id=user_data[0].city.id)


async def _candidate_search(age: int, sex_id: int, city_id: str, offset: int):
    candidate = await user_api.users.search(age_from=age - 5,
                                            age_to=age + 5,
                                            sex=_get_opposite_sex(sex_id),
                                            city=city_id,
                                            count=1,
                                            offset=offset,
                                            fields=["can_access_closed"])

    return candidate.items[0]
        

async def _make_candidate(candidate, user_vk_id: int) -> Candidate:
    return Candidate(vk_id=candidate.id,
                     first_name=candidate.first_name,
                     last_name=candidate.last_name,
                     vk_link=f"https://vk.com/id{candidate.id}",
                     is_favourite=False,
                     user_vk_id=user_vk_id)


async def _get_photos(candidate_vk_id: int) -> list:
    photos = await user_api.photos.get(owner_id=candidate_vk_id,
                                       album_id="profile",
                                       extended=True)
    return photos.items


async def _get_top3_photo(photos: list) -> List[str]:
    top3_photo = sorted(photos, key=lambda photo: photo.likes.count)[-1:-4:-1]
    return [f"photo{photo.owner_id}_{photo.id}" for photo in top3_photo]


async def _make_photo(vk_link:str, candidate_vk_id: int) -> Photo:
    return Photo(vk_link=vk_link, candidate_vk_id=candidate_vk_id)