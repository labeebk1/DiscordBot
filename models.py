import datetime
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    level = Column(Integer)
    wallet = Column(Integer)
    bank = Column(Integer)
    shields = Column(Integer)

    def __repr__(self):
        return "<User(name='%s')>" % (self.name)

class Timestamp(Base):
    __tablename__ = 'timestamp'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    last_worked = Column(DateTime)

class Hourly(Base):
    __tablename__ = 'hourly'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    last_worked = Column(DateTime)  

class Rob(Base):
    __tablename__ = 'rob'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    last_worked = Column(DateTime)  

if __name__ == '__main__':
    engine = create_engine('sqlite:///gamble.db', echo = True)
    Base.metadata.create_all(engine)
