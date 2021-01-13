import os
import logging

from sqlalchemy import create_engine
from sqlalchemy import Column, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]

db = create_engine(DATABASE_URL)
base = declarative_base()


class User(base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    portfolio = Column(String)
    watchlist = Column(String)

    def __repr__(self):
        return "<User(user_id='%s', portfolio='%s', watchlist='%s')>" % (
            self.user_id, self.portfolio, self.watchlist
        )

    def __call__(self):
        return {
            "portfolio": self.portfolio,
            "watchlist": self.watchlist
        }


Session = sessionmaker(db)
session = Session()


def get_user(user_id: int) -> User:
    """Queries a user from the database

    Args:
        user_id (int): User's telegram ID

    Returns:
        User: Instance of User class
    """
    logger.info(f"Retrieving user info for {user_id}")
    curr_user = session.query(User).filter_by(user_id=user_id).first()

    return curr_user


def update_userdb(user: User) -> None:
    """Creates a User object within session before commit()

    Args:
        user_id (int): User's telegram ID
    """
    try:
        session.add(user)
        session.commit()
        logger.info(f"Successfully updated db with {user}")
    except:
        logger.error(f"Failed to update for user {user.user_id}!")
