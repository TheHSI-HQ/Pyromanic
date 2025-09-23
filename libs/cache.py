from typing import Any
from datetime import datetime, timedelta
from libs.config import load_reloading_config, read_config
from time import sleep
from threading import Thread

cfg = load_reloading_config('pyromanic.yaml')

class CachedElement:
    def __init__(self, route: str, inputs: list[Any], response: Any) -> None:
        duration = read_config(cfg(), 'cache.duration', int)
        self.route: str = route
        self.inputs: list[Any] = inputs
        self.expires: datetime = datetime.now() + timedelta(seconds=duration)
        self.response: Any = response

    def amIExpired(self):
        if not read_config(cfg(), "cache.enabled", bool):
            return True
        return (self.expires - datetime.now()).days < 0

    def matches(self, route: str, inputs: list[Any]):
        if not read_config(cfg(), "cache.enabled", bool):
            return False
        same = route == self.route
        if not same:
            return same
        if len(inputs) != len(self.inputs):
            return False
        for i in range(len(inputs)):
            same &= inputs[i] == self.inputs[i]
        return same

class Cache:
    def __init__(self) -> None:
        self._cache: list[CachedElement] = []
        Thread(target=self.__ticker__,daemon=True).start()

    def __tick__(self):
        updated_cache: list[CachedElement] = []
        if not read_config(cfg(), "cache.enabled", bool):
            self._cache = updated_cache
            return
        for cached in self._cache:
            if not cached.amIExpired():
                updated_cache.append(cached)
        self._cache = updated_cache

    def __ticker__(self):
        while True:
            try:
                self.__tick__()
            except Exception:
                pass
            sleep(30)

    def has(self, route: str):
        if not read_config(cfg(), "cache.enabled", bool):
            return False
        for cached in self._cache:
            if cached.route == route:
                return True
        return False

    def has_with_input(self, route: str, inputs: list[Any]):
        if not read_config(cfg(), "cache.enabled", bool):
            return False
        for cached in self._cache:
            if cached.matches(route, inputs):
                return True
        return False

    def get(self, route: str):
        if not read_config(cfg(), "cache.enabled", bool):
            return "", 422
        for cached in self._cache:
            if cached.route == route:
                return cached.response
        return "", 422

    def get_with_input(self, route: str, inputs: list[Any]):
        if not read_config(cfg(), "cache.enabled", bool):
            return "", 422
        for cached in self._cache:
            if cached.matches(route, inputs):
                return cached.response
        return "", 422

    def set(self, route: str, inputs: list[Any], response: Any):
        if not read_config(cfg(), "cache.enabled", bool):
            return
        self._cache.append(CachedElement(route, inputs, response))