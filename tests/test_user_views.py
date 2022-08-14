"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest tests/test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
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

        self.u3 = User.signup(
            email="test3@test.com",
            username="testuser3",
            password="password",
            image_url=None
        )

        self.u4 = User.signup(
            email="test4@test.com",
            username="testuser4",
            password="password",
            image_url=None
        )

        self.u1.id = 111
        self.u2.id = 222
        self.u3.id = 333
        self.u4.id = 444

        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):

        db.session.rollback()

    def test_users_index(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn(f"@{self.u1.username}", str(resp.data))
            self.assertIn(f"@{self.u2.username}", str(resp.data))
            self.assertIn(f"@{self.u3.username}", str(resp.data))
            self.assertIn(f"@{self.u4.username}", str(resp.data))

    def test_users_search(self):
        with self.client as c:
            resp = c.get(f"/users?q={self.u1.username}")

            self.assertIn(f"@{self.u1.username}", str(resp.data))
            self.assertNotIn(f"@{self.u2.username}", str(resp.data))
            self.assertNotIn(f"@{self.u3.username}", str(resp.data))
            self.assertNotIn(f"@{self.u4.username}", str(resp.data))

    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.u1.id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"@{self.u1.username}", str(resp.data))

    
##################################################
# Like Tests

    def setup_likes(self):
        m1 = Message(id=111, text="delicious coffee", user_id=self.u1.id)
        m2 = Message(id=222, text="blueberry pancakes", user_id=self.u1.id)
        m3 = Message(id=333, text="maple syrup", user_id=self.u2.id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.u1.id, message_id=333)
        db.session.add(l1)
        db.session.commit()

    def test_user_show_with_likes(self):
        self.setup_likes()

        with self.client as c:
            resp = c.get(f"/users/{self.u1.id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn(f"@{self.u1.username}", str(resp.data))
            soup = BeautifulSoup(str(resp.data), "html.parser")
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 2 messages
            self.assertIn("2", found[0].text)

            


