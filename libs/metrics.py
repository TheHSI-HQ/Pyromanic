from datetime import timedelta, datetime
from typing import Callable, Any
from flask import Response, request
from types import FunctionType
from functools import wraps
from libs.config import load_reloading_config, read_config
from os.path import exists

cfg = load_reloading_config("pyromanic.yaml")

class Stopwatch:
    def __init__(self) -> None:
        self._start = datetime.now()

    def stop(self) -> timedelta:
        return datetime.now() - self._start

def flagCached():
    raise NotImplementedError()
def flagExternal():
    raise NotImplementedError()
def flagInternal():
    raise NotImplementedError()

class Metrics:
    def __init__(self) -> None:
        pass

    def write(self, url: str, time: timedelta, cached: bool=False, external: timedelta = timedelta(0)):
        microseconds = time.microseconds + time.seconds*1000000
        microseconds_worked = (time.microseconds + time.seconds*1000000) - (external.microseconds + external.seconds*1000000)
        if read_config(cfg(), "debug.record_metrics", bool):
            if not exists("./assets/metrics.csv"):
                with open("./assets/metrics.csv", 'w') as f:
                    f.write("url, duration, time, worked, cached\n")
            self.file = open("./assets/metrics.csv", 'a')
            self.file.write(f"{url}, {microseconds}, {datetime.now().isoformat()}, {microseconds_worked}, {1 if cached else 0}\n")
            self.file.close()

    def measure(self, function: Callable[[Any], Any] | Callable[[], Any]):
        @wraps(function) # pyright: ignore[reportArgumentType]
        def timer_wrapper(*args: list[Any], **kwargs: Any):
            class ValueStorage:
                def __init__(self) -> None:
                    self.cached = False
                    self.external = timedelta(0)
                    self.external_start = datetime.now()

            values = ValueStorage()

            def flagCached():
                values.cached = True

            def flagExternal():
                values.external_start = datetime.now()

            def flagInternal():
                values.external += datetime.now() - values.external_start


            func_globals = function.__globals__.copy()
            func_globals['flagCached'] = flagCached
            func_globals['flagExternal'] = flagExternal
            func_globals['flagInternal'] = flagInternal

            new_func = FunctionType(
                function.__code__, func_globals,
                name=function.__name__,
                argdefs=function.__defaults__,
                closure=function.__closure__,
            )

            stopwatch = Stopwatch()

            buffer: Response = new_func(*args, **kwargs)

            self.write(request.url, stopwatch.stop(), values.cached, values.external)
            return buffer
        return timer_wrapper
