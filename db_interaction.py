from typing import List
import sqlalchemy as sq
from models import create_tables, User, Candidate, Photo
from sqlalchemy.orm import sessionmaker

from config import DB_LOGIN


DSN = f'postgresql://{DB_LOGIN["login"]}:{DB_LOGIN["password"]}@{DB_LOGIN["host"]}:{DB_LOGIN["port"]}/{DB_LOGIN["database"]}'

engine = sq.create_engine(DSN)
create_tables(engine)
Session = sessionmaker(bind=engine)
session = Session()

def _check_is_in_db(item):
    if isinstance(item, User):
        for user in session.query(User).all():
            if user.vk_id == item.vk_id:
                return True
    elif isinstance(item, Candidate): 
        for candidate in session.query(Candidate).all():
            if candidate.vk_id == item.vk_id:
                return True
    elif isinstance(item, Photo): 
        for photo in session.query(Photo).all():
            if photo.vk_link == item.vk_link:
                return True
    return False

def add_person_to_db(person):
    '''Add person to database 
    (no matter user or candidate)'''
    if _check_is_in_db(person):
        session.close()
        return
    else:
        session.add(person)
        

def add_photos_to_db(photo: Photo):
    '''Add photos to database. 
    Can be called after adding each candidate'''
    if _check_is_in_db(photo):
        return
    session.add(photo)

def show_favourite_list():
    '''Receiving list of favourite candidates 
    in format [candidate, [candidate_photos]]'''
    fav_list = []
    for c in session.query(Candidate).join(Photo.candidate).\
        filter(Candidate.is_favourite == True):
        photo_list = []
        for p in session.query(Photo).join(Candidate.photos).\
            filter(Photo.candidate_vk_id == c.vk_id):
            photo_list.append(p)
        fav_list.append([c, photo_list])
    return fav_list

def get_from_db(vk_id:int, model):
    '''Get object from database. 
    model is User or Candidate'''
    return session.query(model).filter(model.vk_id == vk_id).first()

def get_from_db_with_id(id:int, model):
    '''Get object from database. 
    model is User or Candidate'''
    return session.query(model).filter(model.id == id).first()

def change_is_favourite(vk_id:int):
    '''Add/Del candidate to/from favourites'''
    candidate = session.query(Candidate).filter(Candidate.vk_id == vk_id)
    if candidate.first().is_favourite == False:
        candidate.update({Candidate.is_favourite: True})
    else:
        candidate.update({Candidate.is_favourite: False})
    session.commit()

def show_candidate_list():
    '''Receiving list of favourite candidates 
    in format [candidate, [candidate_photos]]'''
    fav_list = []
    for c in session.query(Candidate).join(Photo.candidate):
        photo_list = []
        for p in session.query(Photo).join(Candidate.photos).\
            filter(Photo.candidate_vk_id == c.vk_id):
            photo_list.append(p)
        fav_list.append([c, photo_list])
    return fav_list


def get_candidate_with_photo(id:int) -> dict:
    candidate = session.query(Candidate).filter(model.id == id).first()
    photo_list = []
    for photo in session.query(Photo).join(Candidate.photos).\
        filter(Photo.candidate_vk_id == candidate.vk_id):
            photo_list.append(photo)
    return {"candidate": candidate, "photos": photo_list}

def commit_session():
    session.commit()

def close_session():
    session.close()

        



