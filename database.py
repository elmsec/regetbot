import peewee
from datetime import datetime

# DB CONNECTION (SQLite)
DB = peewee.SqliteDatabase('settings.db')


class BaseDatabaseModel(peewee.Model):
    """
        Base database model
        to prevent DRY for 'class Meta:'
    """
    class Meta:
        database = DB


class User(BaseDatabaseModel):
    """
        User model for the database.
        It contains all users who used the bot
    """
    telegram_id = peewee.IntegerField(unique=True)
    first_name = peewee.CharField(max_length=100)
    last_name = peewee.CharField(max_length=100, null=True)
    username = peewee.CharField(max_length=40, null=True)
    show_info = peewee.BooleanField(default=True)
    max_result = peewee.IntegerField(default=5)
    result_type = peewee.CharField(max_length=20, default='all')
    total_request = peewee.IntegerField(default=0)
    timestamp = peewee.DateTimeField(default=datetime.now())
