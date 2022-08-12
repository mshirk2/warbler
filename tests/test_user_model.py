"""User model tests."""

# run these tests like:
#
#    python -m unittest tests/test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
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

        self.u1 = User.signup(
            email="test1@test.com",
            username="testuser1",
            password="password",
            image_url=None
        )

        self.u2 = User.signup(
            email="test2@test.com",
            username="testuser2",
            password="password",
            image_url=None
        )

        self.u1.id = 123
        self.u2.id = 456

        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):

        db.session.rollback()

    def test_user_model(self):
        """Does basic model work? User should have no messages & no followers"""

        self.assertEqual(len(self.u1.messages), 0)
        self.assertEqual(len(self.u1.followers), 0)

    def test_user_model_repr(self):
        """Does the repr method work as expected?"""

        self.assertEqual("<User #123: testuser1, test1@test.com>", repr(self.u1))
        self.assertNotEqual("<User #456: testuser, test1@test.com>", repr(self.u1))


##################################################
# Following Tests

    def test_user_following(self):
        """Does is_following detect when user1 is/is not following user2?"""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_user_followed_by(self):
        """Does is_followed_by detect when user1 is/is not followed by user2?"""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    def test_user_follows(self):
        """Are follows being counted correctly?"""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)

        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)
    

##################################################
# Signup Tests

    def test_valid_signup(self):
        """Does User.create successfully create a new user given valid credentials?"""

        user_valid = User.signup("validUser", "valid@user.com", "password", None)
        user_valid.id = 789
        db.session.commit()

        self.assertIsNotNone(user_valid)
        self.assertEqual(user_valid.username, "validUser")
        self.assertEqual(user_valid.email, "valid@user.com")
        self.assertNotEqual(user_valid.password, "password")
    
    def test_invalid_username(self):
        """Does User.create fail to create a new user if username field is blank?"""

        invalid_username = User.signup(None, "username@username.com", "password", None)
        invalid_username.id = 111
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email(self):
        """Does User.create fail to create a new user if email field is blank?"""

        invalid_email = User.signup("no_email", None, "password", None)
        invalid_email.id = 222
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password(self):
        """Does User.create fail to create a new user if password field is blank?"""

        with self.assertRaises(ValueError) as context:
            User.signup("no_password", "password@password.com", None, None)
            User.signup("no_password", "password@password.com", "", None)


##################################################
# Authentication Tests

    def test_valid_authentication(self):
        user = User.authenticate(self.u1.username, "password")
        self.assertEqual(user.id, self.u1.id)

    def test_invalid_username(self):
        self.assertFalse(User.authenticate("wrongusername", "password"))

    def test_invalid_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "wrongpassword"))