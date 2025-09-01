import re
from collections import UserDict

valid_unquoted_regex = re.compile(r"^[a-zA-Z0-9_\-]+$")


def quote(token):
    if valid_unquoted_regex.match(token):
        return token
    return f'"{token}"'


class EventContext(UserDict):
    """Context available to loggers or"""

    def __str__(self):
        """String representation for logging

        All keys/values are cast to strings via __format__.

        2 modes are supported:

        * unprefixed: dict[k_n: str, v_n: str] -> "k1=v1 k2=v2"
        * prefixed: dict[k: str, dict[k_n: str, v_n: str]] -> "k_k1=v1 k_k2=v2"
        """
        tokens = []
        for k, v in self.data.items():
            if v is None:
                continue
            if isinstance(v, dict):
                for dict_k, dict_v in v.items():
                    tokens += [f"{k}_{dict_k}", format(dict_v)]
            else:
                tokens += [format(k), format(v)]

        formatted = map(quote, tokens)

        return " ".join(["=".join(pair) for pair in zip(*([iter(formatted)] * 2))])

    def reset(self):
        self.data = {}


context = EventContext()
