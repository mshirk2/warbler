"""User model tests."""

# run these tests like:
#
#    python -m unittest tests/test_user_model.py


import os
from unittest import TestCase
from models import db, User, Message, Follows

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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_model_repr(self):
        """Does the repr method work as expected?"""

        u = User(
            id=1,
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        
        db.session.add(u)
        db.session.commit()

        self.assertEqual("<User #1: testuser, test@test.com>", repr(u))
        self.assertNotEqual("<User #2: testuser, test@test.com>", repr(u))

    def test_user_following(self):
        """Does is_following successfully detect when:
        1. user1 is following user2?
        2. user1 is not following user2?
        3. user2 is following user1
        4. user2 is not following user1"""

        u1 = User(
            id=1,
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )       

        u2 = User(
            id=2,
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1, u2)
        db.session.commit()

        self.assertFalse(u1.is_following(u2))
        u1.following.append(u2)
        self.assertTrue(u1.is_following(u2))

        self.assertFalse(u2.is_following(u1))
        u2.following.append(u1)
        self.assertTrue(u2.is_following(u1))

    def test_user_create(self):
        """Does User.create successfully create a new user given valid credentials? Does User.create fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?"""