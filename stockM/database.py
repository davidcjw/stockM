import os

from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


DATABASE_URL = os.environ["DATABASE_URL"]

db = create_engine(DATABASE_URL)
base = declarative_base()


class User(base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    portfolio = Column(String)
    watchlist = Column(String)

    def __repr__(self):
        return "<User(name='%s', portfolio='%s', watchlist='%s')>" % (
            self.user_id, self.portfolio, self.watchlist
        )


Session = sessionmaker(db)
session = Session()


# Query user
def get_user(user_id):
    curr_user = session.query(User).filter_by(user_id=user_id).first()
    return curr_user
