"""Message model tests."""

# run these tests like:
#
#    python -m unittest tests/test_message_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app
app.config['TESTING'] = True

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test Message Model"""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.u1 = User.signup(
            email="test1@test.com",
            username="testuser1",
            password="password",
            image_url=None
        )
        self.u1.id = 123

        self.u2 = User.signup(
            email="test2@test.com",
            username="testuser2",
            password="password",
            image_url=None
        )
        self.u2.id = 456

        self.m1 = Message(
            text="testtest",
            user_id=self.u1.id
        )

        self.m2 = Message(
            text="testtest2",
            user_id=self.u2.id
        )

        db.session.add_all([self.m1, self.m2])
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Does basic model work? User should have 1 message."""

        self.assertEqual(len(self.u1.messages), 1)
        self.assertEqual(self.u1.messages[0].text, "testtest")

    def test_message_likes(self):
        """Do likes append successfully?"""

        self.u1.likes.append(self.m2)
        db.session.commit()

        like = Likes.query.filter(Likes.user_id == self.u1.id).all()
        self.assertEqual(len(like), 1)
        self.assertEqual(like[0].message_id, self.m2.id)
