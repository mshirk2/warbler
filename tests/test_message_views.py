"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest tests/test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

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

        self.client = app.test_client()

        self.u1 = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.u1.id = 111
 
        db.session.commit()

    def tearDown(self):
        db.session.rollback()


    ##################################################
    # Add Message Tests

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
    
    def test_add_without_user(self):
        """Does app fail to post a message if there is no user in session?"""

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Greetings"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_invalid_user(self):
        """Does app fail to post a message if wrong user is in session?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 99222224 # user does not exist

            resp = c.post("/messages/new", data={"text": "Greetings"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


    ##################################################
    # Show Message Tests

    def setup_messages(self):

        m1 = Message(id=222, text="testtest", user_id=self.u1.id)
        db.session.add(m1)
        db.session.commit()
    
    def test_message_show(self):
        """Does app successfully show message if valid user is logged in?"""

        self.setup_messages()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            resp = c.get("/messages/222")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testtest", str(resp.data))

    def test_invalid_message_show(self):
        """Does app fail to show message that doesn't exist? Does it display 404 page?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            resp = c.get('/messages/3584684568744325', follow_redirects=True)

            self.assertEqual(resp.status_code, 404)
            self.assertIn("That page does not exist!", str(resp.data))


    ##################################################
    # Delete Message Tests

    def test_message_delete(self):
        """Does message delete successfully when user is authorized?"""

        self.setup_messages()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            resp = c.post('/messages/222/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            m = Message.query.get(222)
            self.assertIsNone(m)

    def test_message_delete_unauthorized(self):
        """Does app fail to delete a message when the user is not authorized?"""

        self.setup_messages()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 95467865484

            resp = c.post('/messages/222/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
            
            m = Message.query.get(222)
            self.assertIsNotNone(m)

    def test_message_without_user(self):
        """Does app fail to delete a message when user is not signed in?"""

        self.setup_messages()

        with self.client as c:
            resp = c.post('/messages/222/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
            
            m = Message.query.get(222)
            self.assertIsNotNone(m)

