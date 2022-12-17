import sqlalchemy as sq
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

class User(Base):
    __tablename__ = 'user'

    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    first_name = sq.Column(sq.String(length=50))
    last_name = sq.Column(sq.String(length=50))
    age = sq.Column(100 > sq.Integer > 0, unique=True)

    candidates = relationship('Candidate', backref='candidate')

    def __str__(self):
        return [self.id, self.vk_id, 
                self.first_name, self.last_name]

class Candidate(Base):
    __tablename__ = 'candidate'

    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    first_name = sq.Column(sq.String(length=50))
    last_name = sq.Column(sq.String(length=50))
    age = sq.Column(100 > sq.Integer > 0, unique=True)
    vk_link = sq.Column(sq.String, unique=True)
    is_favourite = sq.Column(sq.Boolean)

    photos = relationship('Photo', backref='photo')

    def __str__(self):
        return [self.id, self.vk_id, self.first_name, 
                self.last_name, self.age]

class Photo(Base):
    __tablename__ = 'photo'

    id = sq.Column(sq.Integer, primary_key=True)
    vk_link = sq.Column(sq.String, unique=True)
    candidate_id = sq.Column(sq.Integer, sq.ForeignKey("candidate.id"), nullable=False)

    def __str__(self):
        return [self.id, self.vk_link, 
                self.candidate_id]