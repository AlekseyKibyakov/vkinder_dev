'''The script with the inside logic of a bot
to find candidates for romantic dates. '''
import datetime as dt
from time import sleep
from typing import List
from vkbottle import API
from config import USER_TOKEN
from models import User, Candidate, Photo

user_api = API(USER_TOKEN)


def _string_with_born_to_age(born: str) -> int:
    ''' The function takes date of birth as a string
    and returns age as a integer '''
    today = dt.date.today()
    born_date = dt.datetime.strptime(born, "%d.%m.%Y")
    return today.year - born_date.year - ((today.month, today.day) < (
        born_date.month, born_date.day))


def _get_opposite_sex(sex_id: int) -> int:
    ''' The function takes sex_id as a intefer and returns the opposite
     value (according to VK API documentation) as a integer '''
    return 1 if sex_id == 2 else 2


async def _make_user(user_data) -> User:
    ''' The function returns an object of the User class '''
    return User(vk_id=user_data[0].id,
                first_name=user_data[0].first_name,
                last_name=user_data[0].last_name,
                age=_string_with_born_to_age(user_data[0].bdate),
                sex_id=user_data[0].sex.value,
                city_id=user_data[0].city.id)


async def _candidate_search(user, offset) -> tuple:
    ''' The function takes the data for the candidate search and the number
     for the offset in the search, and returns a tuple of candidate data
     and the offset number '''
    candidate = await user_api.users.search(age_from=user.age - 5,
                                                age_to=user.age + 5,
                                                sex=_get_opposite_sex(user.sex_id),
                                                city=user.city_id,
                                                count=1,
                                                offset=offset,
                                                fields=["can_access_closed"])

    return (candidate.items[0], offset + 1)


async def _make_candidate(candidate, user_vk_id: int) -> Candidate:
    ''' The function returns an object of the Candidate class '''
    return Candidate(vk_id=candidate.id,
                     first_name=candidate.first_name,
                     last_name=candidate.last_name,
                     vk_link=f"https://vk.com/id{candidate.id}",
                     is_favourite=False,
                     user_vk_id=user_vk_id)


async def _get_photos(candidate_vk_id: int) -> list:
    ''' The function takes the user's vk id and returns a list with data
    about the user's profile photo album '''
    photos = await user_api.photos.get(owner_id=candidate_vk_id,
                                       album_id="profile",
                                       extended=True)
    return photos.items


async def _get_top3_photo(photos: list) -> List[str]:
    ''' The function takes a list with data
    about the user's photo album in vk
    and returns a list of three items with data
    for sending photos in vk chat
    '''
    top3_photo = sorted(photos, key=lambda photo: photo.likes.count)[-1:-4:-1]
    return [
        f"photo{photo.owner_id}_{photo.id}_{photo.access_key}"
        if photo.access_key is not None
        else f"photo{photo.owner_id}_{photo.id}" for photo in top3_photo
        ]


async def _make_photo(vk_link: str, candidate_vk_id: int) -> Photo:
    ''' The function returns an object of the Photo class '''
    return Photo(vk_link=vk_link, candidate_vk_id=candidate_vk_id)
