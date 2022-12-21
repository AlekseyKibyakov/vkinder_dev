import sqlalchemy as sq
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()

def create_tables(engine):
    Base.metadata.create_all(engine)


class User(Base):
    __tablename__ = 'user'

    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    first_name = sq.Column(sq.VARCHAR(1500))
    last_name = sq.Column(sq.VARCHAR(50))
    age = sq.Column(sq.SmallInteger)
    sex_id = sq.Column(sq.SmallInteger)
    city_id = sq.Column(sq.VARCHAR(25))

    def __str__(self):
        return [self.id, self.vk_id, 
                self.first_name, self.last_name,
                self.age, self.sex_id, self.city_id]


class Candidate(Base):
    __tablename__ = 'candidate'

    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    first_name = sq.Column(sq.VARCHAR(1500))
    last_name = sq.Column(sq.VARCHAR(50))
    vk_link = sq.Column(sq.VARCHAR(200))
    is_favourite = sq.Column(sq.Boolean)

    user_id = sq.Column(sq.Integer, sq.ForeignKey("user.id"), nullable=False)

    user = relationship('User', backref='candidates')

    def __str__(self):
        return [self.id, self.vk_id, self.first_name, 
                self.last_name]


class Photo(Base):
    __tablename__ = 'photo'

    id = sq.Column(sq.Integer, primary_key=True)
    vk_link = sq.Column(sq.String, unique=True)
    candidate_id = sq.Column(sq.Integer, sq.ForeignKey("candidate.id"), nullable=False)

    candidate = relationship('Candidate', backref='photos')

    def __str__(self):
        return [self.id, self.vk_link, 
                self.candidate_id]