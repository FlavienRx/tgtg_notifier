import os
import sqlite3


class DbWrapper:
    def __init__(self):
        # Init database
        base_path = os.path.dirname(os.path.realpath(__file__))
        self.db = sqlite3.connect(os.path.join(base_path, "database.db"))
        self.db.row_factory = sqlite3.Row
        self.cursor = self.db.cursor()

        # Create users table if not exists
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS users (
                email text UNIQUE, 
                user_id int UNIQUE, 
                access_token text, 
                refresh_token text, 
                send_notif_on text, 
                slack_token text, 
                slack_user_id int, 
                telegram_token text, 
                telegram_chan_id int,
                discord_webhook_url text
            )"""
        )

        # Create favorite_stores table if not exists
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS favorite_stores (
                user_id int,
                store_id int,
                nb_item int,
                UNIQUE(user_id, store_id)
            )"""
        )

    def close(self):
        self.db.close()

    def get_users(self):
        # Get user favorite stores
        self.cursor.execute("SELECT * FROM users")
        users = self.cursor.fetchall()

        if not users:
            raise Exception("No users configured")

        return users

    def update_user(self, email, user_id, access_token, refresh_token):
        # Update a user
        self.cursor.execute(
            """UPDATE users SET user_id=?, access_token=?, refresh_token=? 
            WHERE email=?""",
            (user_id, access_token, refresh_token, email),
        )
        # Save (commit) the changes
        self.db.commit()

    def user_favorite_stores(self, user_id):
        # Get user favorite stores
        self.cursor.execute("SELECT * FROM favorite_stores WHERE user_id=?", (user_id,))
        return self.cursor.fetchall()

    def update_create_favorite_store(self, user_id, store_id, items_available):
        # Update or create favorite store
        try:
            self.cursor.execute(
                """INSERT INTO favorite_stores(user_id, store_id, nb_item)
                VALUES(?, ?, ?)""",
                (
                    user_id,
                    store_id,
                    items_available,
                ),
            )

        except sqlite3.IntegrityError:
            self.cursor.execute(
                """UPDATE favorite_stores SET nb_item=?
                WHERE user_id=? and store_id=?""",
                (items_available, user_id, store_id),
            )

        # Save (commit) the changes
        self.db.commit()
