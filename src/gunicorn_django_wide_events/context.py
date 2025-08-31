from collections import UserDict


class Context(UserDict):
    def __str__(self):
        return " ".join([f"{k}={v}" for k, v in self.data.items()])

    def reset(self):
        self.data = {}

context = Context()
