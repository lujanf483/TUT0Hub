import os
import unittest

from app import create_app, get_db
from app.models.user import User


class AppStartupTestCase(unittest.TestCase):
    def test_create_app_falls_back_to_in_memory_db_when_mongo_is_unavailable(self):
        os.environ['MONGODB_URI'] = 'not-a-valid-uri'
        os.environ['MONGODB_DBNAME'] = 'tut0hub'

        app = create_app()

        self.assertIsNotNone(app)
        self.assertIsNotNone(get_db())
        self.assertTrue(hasattr(get_db(), 'users'))

    def test_user_create_and_lookup_work_in_memory_fallback(self):
        os.environ['MONGODB_URI'] = 'not-a-valid-uri'
        os.environ['MONGODB_DBNAME'] = 'tut0hub'

        create_app()
        user = User.create('demo', 'demo@example.com', 'secret123')

        self.assertEqual(user.username, 'demo')
        self.assertEqual(user.email, 'demo@example.com')
        self.assertIsNotNone(User.get_by_id(user.id))
        self.assertEqual(User.get_by_username('demo').id, user.id)


if __name__ == '__main__':
    unittest.main()
