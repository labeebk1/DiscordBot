import datetime
from typing_extensions import Required
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    casino = Column(Integer, ForeignKey('casino.id'))
    name = Column(String)
    level = Column(Integer)
    wallet = Column(Integer)
    bank = Column(Integer)
    shields = Column(Integer)
    diamond = Column(Boolean)
    last_work = Column(DateTime)
    last_hourly = Column(DateTime)
    last_daily = Column(DateTime)
    last_rob = Column(DateTime)

    def __repr__(self):
        return "<User(name='%s')>" % (self.name)

class Profession(Base):
    __tablename__ = 'profession'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    profession_id = Column(Integer)

class Miner(Base):
    __tablename__ = 'miner'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    level = Column(Integer)
    balance = Column(Integer)
    last_worked = Column(DateTime)

class Casino(Base):
    __tablename__ = 'casino'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    level = Column(Integer)
    balance = Column(Integer)

class Ticket(Base):
    __tablename__ = 'ticket'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    level = Column(Integer)

if __name__ == '__main__':
    engine = create_engine('sqlite:///gamble.db', echo = True)
    Base.metadata.create_all(engine)
