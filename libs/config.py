from yaml import safe_load, YAMLObject
from pathlib import Path
from typing import Any, Type, TypeVar
from hashlib import sha256
from time import sleep
from threading import Thread
from typing import Callable
from os.path import exists, splitext

def load_config(filename: str) -> YAMLObject:
    # Prefer xyz.dev.yaml over xyz.yaml
    dev_path =  Path('.') / 'config' / (splitext(filename)[0] + ".dev" + splitext(filename)[1])
    path =  Path('.') / 'config' / filename

    if exists(dev_path):
        with open(dev_path, 'r') as f:
            return safe_load(f.read())
    else:
        with open(path, 'r') as f:
            return safe_load(f.read())

def load_reloading_config(filename: str) -> Callable[[], YAMLObject]:
    class config:
        def __init__(self) -> None:
            self._cfg = load_config(filename)
            self._hash = sha256(str(self._cfg).encode()).hexdigest
            Thread(target=self.__ticker__,daemon=True).start()
        def __ticker__(self):
            while True:
                try:
                    self.__tick__()
                except Exception:
                    pass
                sleep(5)
        def __tick__(self):
            self._cfg = load_config(filename)
        def get(self) -> YAMLObject:
            return self._cfg
    return config().get

T = TypeVar("T")

def read_config(
    config: YAMLObject,
    path: str,
    expected_type: Type[T]
) -> T:
    split_path = path.split('.')
    val: Any = config
    for p in split_path:
        if p not in val:
            raise ValueError(
                f"{path} was not found!"
            )
        val = val[p]

    if isinstance(val, expected_type):
        return val  # type: ignore[return-value]  # (mypy sees it's T)
    raise ValueError(
        f"{path} is of type {type(val).__name__} not {expected_type.__name__} as expected!"
    )

def nullable_read_config(
    config: YAMLObject,
    path: str,
    expected_type: Type[T]
) -> T | None:
    split_path = path.split('.')
    val: Any = config
    for p in split_path:
        if p not in val:
            return None
        val = val[p]

    if isinstance(val, expected_type):
        return val  # type: ignore[return-value]  # (mypy sees it's T)
    return None