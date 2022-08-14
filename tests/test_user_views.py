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
app.config['TESTING'] = True

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
        """Are the usernames present on the users page?"""
        with self.client as c:
            resp = c.get("/users")

            self.assertIn(f"@{self.u1.username}", str(resp.data))
            self.assertIn(f"@{self.u2.username}", str(resp.data))
            self.assertIn(f"@{self.u3.username}", str(resp.data))
            self.assertIn(f"@{self.u4.username}", str(resp.data))

    def test_users_search(self):
        """Does search display the desired username? Does search not display undesired usernames?"""
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
        """Setup sample messages and likes"""

        m1 = Message(id=111, text="delicious coffee", user_id=self.u1.id)
        m2 = Message(id=222, text="blueberry pancakes", user_id=self.u1.id)
        m3 = Message(id=333, text="maple syrup", user_id=self.u2.id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.u1.id, message_id=333)
        db.session.add(l1)
        db.session.commit()

    def test_user_show_with_likes(self):
        """Does app show correct amount of user's messages, followers, following, and likes?"""

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

            # test for a count of 0 followers
            self.assertIn("0", found[1].text)

            # test for a count of 0 following
            self.assertIn("0", found[2].text)

            # test for a count of 1 like
            self.assertIn("1", found[3].text)

    def test_add_like(self):
        """Does app successfully add a like?"""

        self.setup_likes()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            resp = c.post("/messages/222/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==222).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.u1.id)

    def test_remove_likes(self):
        """Does app successfully remove a like?"""

        self.setup_likes()

        m = Message.query.filter(Message.text=="maple syrup").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.u1.id)

        # check that u1 currently likes message
        l = Likes.query.filter(Likes.user_id==self.u1.id and Likes.message_id==m.id).one()

        self.assertIsNotNone(l)

        # toggle like to remove
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            self.assertEqual(len(likes), 0)

    def test_unauthenticated_like(self):
        """Does the app fail to toggle like if user is not authorized?"""

        self.setup_likes()

        m = Message.query.filter(Message.text=="maple syrup").one()
        self.assertIsNotNone(m)
        like_count = Likes.query.count()

        with self.client as c:
            resp = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            # number of likes has not changed
            self.assertEqual(like_count, Likes.query.count())


    ##################################################
    # Follower Tests

    def setup_followers(self):
        """Setup sample Follows"""

        f1 = Follows(user_being_followed_id=self.u1.id, user_following_id=self.u2.id)
        f2 = Follows(user_being_followed_id=self.u1.id, user_following_id=self.u3.id)
        f3 = Follows(user_being_followed_id=self.u2.id, user_following_id=self.u1.id)
        
        db.session.add_all([f1,f2,f3])
        db.session.commit()

    
    def test_user_show_with_follows(self):
        """Does the app show the correct amount of user's messages, following, followers, and likes?"""

        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.u1.id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn(f"@{self.u1.username}", str(resp.data))
            soup = BeautifulSoup(str(resp.data), "html.parser")
            found = soup.find_all("li", {"class": "stat"})
            self.assertEqual(len(found), 4)

            # test for a count of 0 messages
            self.assertIn("0", found[0].text)

            # test for a count of 1 following
            self.assertIn("1", found[1].text)

            # test for a count of 2 followers
            self.assertIn("2", found[2].text)

            # test for a count of 0 likes
            self.assertIn("0", found[3].text)

    def test_show_following(self):
        """Does the app correctly display the accounts the user is following?"""

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            resp = c.get(f"/users/{self.u1.id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser2", str(resp.data))
            self.assertNotIn("@testuser3", str(resp.data))
            self.assertNotIn(f"@{self.u1.id}", str(resp.data))

    def test_show_followers(self):
        """Does the app correctly display the accounts following the user?"""

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            resp = c.get(f"/users/{self.u1.id}/followers")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser2", str(resp.data))
            self.assertIn("@testuser3", str(resp.data))
            self.assertNotIn(f"@{self.u1.id}", str(resp.data))

    def test_unauthorized_following_page_access(self):
        """Does the app fail to display following if user is unauthorized?"""

        self.setup_followers()
        with self.client as c:
            resp = c.get(f"/users/{self.u1.id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@testuser2", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):
        """Does the app fail to display followers if user is unauthorized?"""

        self.setup_followers()
        with self.client as c:
            resp = c.get(f"/users/{self.u1.id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@testuser2", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))








        

            


