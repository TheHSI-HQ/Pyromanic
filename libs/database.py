from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

from logging import warning
from base64 import b64decode

from libs.config import load_reloading_config, read_config

cfg = load_reloading_config("pyromanic.yaml")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    password = Column(String)
    role = Column(String)

    def __repr__(self):
        return f"<User(name={self.name}, password={self.password}, role={self.role})>"

class AuthCookie(Base):
    __tablename__ = 'auth_cookies'
    id = Column(Integer, primary_key=True)
    owner = Column(String)
    key = Column(String)
    expires = Column(DateTime)

    def __repr__(self):
        return f"<AuthCookie(owner={self.owner}, key={self.key}, expires={self.expires})>"

class Database:
    def __init__(self) -> None:
        match read_config(cfg(), "database.type", str).lower():
            case "sqlite":
                self._sqlite()
            case "mysql":
                self._mysql()
            case "postgres" | "postgresql":
                self._postgresql()
            case _:
                raise ValueError("Database Type is invalid")
        self._generate_session()

    def _parse_password(self, password: str) -> str:
        if password.startswith("b64|"):
            return b64decode(password).decode()
        warning("Please use a Base64 encoded Database Password")
        return password

    def _sqlite(self):
        self.type = "sqlite"
        file = read_config(cfg(), "database.file", str)
        print(self._parse_password(read_config(cfg(), "database.password", str)))
        self.raw = create_engine(f"sqlite:///{file}", echo=True)

    def _mysql(self):
        self.type = "mysql"
        database = read_config(cfg(), "database.database", str)
        host = read_config(cfg(), "database.host", str)
        user = read_config(cfg(), "database.user", str)
        password = self._parse_password(read_config(cfg(), "database.password", str))
        self.raw = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{database}", echo=True)

    def _postgresql(self):
        self.type = "postgresql"
        database = read_config(cfg(), "database.database", str)
        host = read_config(cfg(), "database.host", str)
        user = read_config(cfg(), "database.user", str)
        password = self._parse_password(read_config(cfg(), "database.password", str))

        self.raw = create_engine(f"postgresql://{user}:{password}@{host}/{database}", echo=True)

    def _generate_session(self):
        Base.metadata.create_all(self.raw)
        Session = sessionmaker(bind=self.raw)
        self._session = Session()

    def session(self):
        return self._session