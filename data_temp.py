from models import User, Candidate, Photo
import db_interaction as db
from pprint import pprint

user1 = User(
    vk_id = 1446622,
    first_name = 'John',
    last_name = 'Smith',
    age = 20,
    sex_id = 2,
    city_id = 5    
)

candidate1 = Candidate(
    vk_id = 2222222,
    first_name = 'Kate',
    last_name = 'Kate',
    vk_link = 'vk.com/kate',
    is_favourite = True,
    user_id = 1
)

candidate2 = Candidate(
    vk_id = 3333333,
    first_name = 'Mary',
    last_name = 'Mary',
    vk_link = 'vk.com/mary',
    is_favourite = False,
    user_id = 1
)

candidate3 = Candidate(
    vk_id = 4444444,
    first_name = 'Jane',
    last_name = 'Jane',
    vk_link = 'vk.com/jane',
    is_favourite = True,
    user_id = 1
)

photo1_c1 = Photo(
    vk_link = 'photo1_c1',
    candidate_vk_id = 2222222
)
photo2_c1 = Photo(
    vk_link = 'photo2_c1',
    candidate_vk_id = 2222222
)
photo3_c1 = Photo(
    vk_link = 'photo3_c1',
    candidate_vk_id = 2222222
)
photo1_c2 = Photo(
    vk_link = 'photo1_c2',
    candidate_vk_id = 3333333
)
photo2_c2 = Photo(
    vk_link = 'photo2_c2',
    candidate_vk_id = 3333333
)
photo3_c2 = Photo(
    vk_link = 'photo3_c2',
    candidate_vk_id = 3333333
)
photo1_c3 = Photo(
    vk_link = 'photo1_c3',
    candidate_vk_id = 4444444
)
photo2_c3 = Photo(
    vk_link = 'photo2_c3',
    candidate_vk_id = 4444444
)
photo3_c3 = Photo(
    vk_link = 'photo3_c3',
    candidate_vk_id = 4444444
)

candidates = [candidate1, candidate2, candidate3]

photos = {'photos_c1': [
    photo1_c1,
    photo2_c1,
    photo3_c1,
],
'photos_c2': [
    photo1_c2,
    photo2_c2,
    photo3_c2,
],
'photos_c3': [
    photo1_c3,
    photo2_c3,
    photo3_c3
]}

db.add_person_to_db(user1) 

for c in candidates:
    # добавление кандидатов в БД, можно подставить в ф-цию,
    # где юзер нажимает показать следующего или добавляет в избранные
    db.add_person_to_db(c)

for p in photos.values():
    # добавление фото в БД, можно вызывать после добавления кандидата
    db.add_photos_to_db(p)

db.commit_session()
# получаем список избранных, можно вытягивать из них любые аттрибуты (фотки и т.д.)
db.change_is_favourite(3333333)

favourites = db.show_favourite_list()

pprint(favourites)

print(db.get_from_db(1446622, User).age)
print(db.get_from_db(1446622, User).sex_id)
print(db.get_from_db(1446622, User).city_id)

print(db.get_from_db(2222222, Candidate).vk_link)

db.close_session()
