import sqlite3
import logging
from time import time

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

# create logger
logger = logging.getLogger(__name__)


class DBHelper:
    def __init__(self, dbname="settings.db"):
        self.dbname = dbname

    def run_sql(self, sql, args=None, select=False):
        with sqlite3.connect(self.dbname, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            if args:
                cur.execute(sql, args)
            else:
                cur.execute(sql)

            if select:
                return cur.fetchone()

            return conn.commit()

    def setup(self):
        try:
            stmt = """CREATE TABLE IF NOT EXISTS users
                      (
                      id integer primary key,
                      user_id integer unique,
                      username text,
                      first_name text,
                      last_name text,
                      show_info integer,
                      max_result integer,
                      result_type text,
                      total_request integer,
                      time_stamp integer
                      )"""
            self.run_sql(stmt)
        except Exception as e:
            logger.info('setup error in sqlite.')

    def get_user(self, user_id):
        try:
            stmt = "SELECT * FROM users WHERE user_id = (?)"
            args = (user_id,)

            result = self.run_sql(stmt, args, True)
            return result
        except Exception as e:
            logger.error('can\'t get_user')

    def add_user(self, user_id, username, first_name, last_name):
        try:
            self.setup()
            stmt = """INSERT INTO users
                      (
                      user_id, username, first_name, last_name, show_info,
                      max_result, result_type, total_request, time_stamp
                      )
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            args = (
                user_id,
                username,
                first_name,
                last_name,
                1, 5, 'all', 0,
                int(time()))
            self.run_sql(stmt, args)
        except Exception as e:
            logger.warning('there is already a user with this id')

    def update_user(self, user_id, setting, value):
        try:
            stmt = "UPDATE users SET {} = (?) WHERE user_id = (?)".\
                    format(setting)
            args = (value, user_id)
            self.run_sql(stmt, args)
        except Exception as e:
            logger.error('update_user error in sqlite')
