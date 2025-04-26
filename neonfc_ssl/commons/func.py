from time import time


class RunEvery:
    def __init__(self, interval):
        self.__interval = interval
        self.__last_call = time()

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            if time() - self.__last_call >= self.__interval:
                out = func(*args, **kwargs)
                self.__last_call = time()
                return out
        return wrapped
