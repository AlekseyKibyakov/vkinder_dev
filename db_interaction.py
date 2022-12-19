from models import create_tables, User, Candidate, Photo
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sq

db_log_in = {'login': 'postgres', 'password': '1'}

DSN = f'postgresql://{db_log_in["login"]}:{db_log_in["password"]}@localhost:5432/vkinder_db'

engine = sq.create_engine(DSN)
create_tables(engine)
Session = sessionmaker(bind=engine)
session = Session()

def add_person_to_db(person):
    '''Add person to database 
    (no matter user or candidate)'''
    for user, candidate in session.query(User).all(), session.query(Candidate).all():
        #If person is in db already - add nothing
        if user.vk_id == person.vk_id or candidate.vk_id == person.vk_id:
            session.close()
            return
    session.add(person)
    session.commit()
    session.close()

def add_photos_to_db(photos):
    '''Add photos to database. 
    Can be called after adding each candidate'''
    for p in photos:
        session.add(p)
    session.commit()
    session.close()

def show_favourite_list():
    '''Receiving list of favourite candidates 
    in format [candidate, [candidate_photos]]'''
    fav_list = []
    for c in session.query(Candidate).join(Photo.candidate).\
        filter(Candidate.is_favourite == True):
        photo_list = []
        for p in session.query(Photo).join(Candidate.photos).\
            filter(Photo.candidate_id == c.id):
            photo_list.append(p)
        fav_list.append([c, photo_list])
    session.close()
    return fav_list




