import os
import logging
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import Column, String, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Uncomment this if running locally with a .env file,
# otherwise ensure that TOKEN has been exported to $PATH
# env_path = Path(".") / ".env"
# load_dotenv(dotenv_path=env_path, verbose=True)

TOKEN = os.getenv("TOKEN")
# DB = os.getenv("DB")
DATABASE_URL = os.environ["DATABASE_URL"]

db = create_engine(DATABASE_URL)
base = declarative_base()


class User(base):
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True)
    portfolio = Column(String)
    watchlist = Column(String)
    is_subscribed = Column(Boolean, default=True)

    def __repr__(self):
        return "<User(user_id='%s', portfolio='%s', watchlist='%s', " \
               "is_subscribed='%s')>" % (self.user_id, self.portfolio,
                                         self.watchlist, self.is_subscribed)

    def __call__(self):
        return {
            "portfolio": self.portfolio,
            "watchlist": self.watchlist,
            "is_subscribed": self.is_subscribed
        }


def get_user(session: Session, user_id: int) -> User:
    """Queries a user from the database

    Args:
        user_id (int): User's telegram ID

    Returns:
        User: Instance of User class
    """
    logger.info(f"Retrieving user info for {user_id}")
    curr_user = session.query(User).filter_by(user_id=user_id).first()

    # Prepare a new User object if the user is not found in DB
    if not curr_user:
        return User(user_id=user_id)

    return curr_user


def update_userdb(session: Session, user: User) -> None:
    """Creates a User object within session before commit()

    Args:
        user_id (int): User's telegram ID
    """
    try:
        session.add(user)
        session.commit()
        logger.info(f"Successfully updated db with {user}")
    except Exception as e:
        logger.error(f"{e}")


def get_subscribers(session: Session):
    subscribers = session.query(User).filter_by(is_subscribed=True).all()
    return subscribers
