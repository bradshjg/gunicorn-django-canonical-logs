"""Logfmt formatter, parts of the implementation from josheppinette/python-logfmte under MIT license

See https://github.com/josheppinette/python-logfmter/blob/83199b506708d2180a437612c79ea5a5c03d70ce/LICENSE.txt

Differs from the above in that all values are quoted and "-" is used to represent None
"""

import re

from gunicorn_django_canonical_logs.event_context import EventContext


class LogFmt:
    @classmethod
    def format_string(cls, value: str) -> str:
        """
        Process the provided string with any necessary quoting and/or escaping.
        """
        value = re.sub(r"\s+", " ", value).strip()

        needs_dquote_escaping = '"' in value

        if needs_dquote_escaping:
            value = value.replace('"', '\\"')

        return f'"{value}"' if value else '"-"'

    @classmethod
    def format_value(cls, value) -> str:
        """
        Map the provided value to the proper logfmt formatted string.
        """
        coerced_value = value

        if value is None:
            coerced_value = ""

        if isinstance(value, bool):
            coerced_value = "true" if value else "false"

        return cls.format_string(format(coerced_value))

    @classmethod
    def normalize_key(cls, key: str) -> str:
        """
        Return a string whereby any spaces are converted to underscores and
        newlines are escaped.

        If the provided key is empty, then return a single underscore. This
        function is used to prevent any logfmt parameters from having invalid keys.

        As a choice of implementation, we normalize any keys instead of raising an
        exception to prevent raising exceptions during logging. The goal is to never
        impede logging. This is especially important when logging in exception handlers.
        """
        if not key:
            return "_"

        return key.replace(" ", "_").replace("\n", "\\n")

    @classmethod
    def format(cls, context: EventContext) -> str:
        """String representation for logging

        All keys/values are cast to strings via __format__.

        2 modes are supported:

        * unprefixed: dict[k_n: str, v_n: str] -> "k1=v1 k2=v2"
        * prefixed: dict[k: str, dict[k_n: str, v_n: str]] -> "k_k1=v1 k_k2=v2"
        """
        tokens = []
        for k, v in context.raw_items():
            for dict_k, dict_v in v.items():
                tokens += [f"{k}_{dict_k}", dict_v]

        return " ".join(
            [
                "=".join([cls.normalize_key(pair[0]), cls.format_value(pair[1])])
                for pair in zip(*([iter(tokens)] * 2), strict=False)
            ]
        )
