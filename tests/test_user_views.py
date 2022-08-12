import pytest
from flask_bcrypt import Bcrypt
from models import db, connect_db, User, Message, Follows
from app import app

bcrypt = Bcrypt()