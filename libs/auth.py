from libs.database import Database, AuthCookie, User
from hashlib import sha256, md5, sha512
from argon2 import PasswordHasher
from libs.config import load_reloading_config, read_config

from datetime import datetime, timezone, timedelta
from random import choice
from time import sleep
from threading import Thread

db = Database()
cfg = load_reloading_config("pyromanic.yaml")

_auth_chars = "abcdefghijklmnopqrsatuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-=#/?%!"

class Auth:
    def run_taker(self):
        Thread(target=self._check_db, daemon=True).start()
    def is_valid_cookie(self, cookie: str |None):
        if cookie is None:
            return False
        cookies = db.session().query(AuthCookie).filter(AuthCookie.key == cookie).first()
        return bool(cookies)

    def who_owns_cookie(self, cookie: str):
        cookies = db.session().query(AuthCookie).filter(AuthCookie.key == cookie).first()
        if not cookies:
            return None
        return cookies.owner

    def register_cookie(self, owner: str):
        buffer = "PYR-"
        for _ in range(64):
            buffer += choice(_auth_chars)
        expiration_time = datetime.now(timezone.utc) + timedelta(
            days=read_config(cfg(), "auth.expires.days", int),
            hours=read_config(cfg(), "auth.expires.hours", int),
            minutes=read_config(cfg(), "auth.expires.minutes", int),
            seconds=read_config(cfg(), "auth.expires.seconds", int),
        )

        cookie = AuthCookie(owner=owner, key=buffer, expires=expiration_time)
        db.session().add(cookie)
        db.session().commit()
        return buffer

    def _check_db(self):
        while 1:
            db.session().query(
                    AuthCookie
                ).filter(
                    AuthCookie.expires < datetime.now(timezone.utc)
                ).delete(synchronize_session=False)
            db.session().commit()
            sleep(60)

    def verify_user(self, username: str, password: str):
        secret = read_config(cfg(), "auth.secret", str)
        users = db.session().query(User).filter(User.name == username).first()
        if not users:
            return False
        ph = PasswordHasher()
        try:
            return ph.verify(users.password, password + secret)
        except Exception:
            return False

    def count_users(self):
        return len(db.session().query(User).all())

    def create_user(self, username: str, password: str, role: str):
        secret = read_config(cfg(), "auth.secret", str)
        ph = PasswordHasher()
        hashed_password = ph.hash(password + secret)
        user = User(name = username, password = hashed_password, role = role)
        db.session().add(user)
        db.session().commit()