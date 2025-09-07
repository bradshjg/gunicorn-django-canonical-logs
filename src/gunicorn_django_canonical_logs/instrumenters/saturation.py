from gunicorn_django_canonical_logs.event_context import Context
from gunicorn_django_canonical_logs.instrumenters.base import BaseInstrumenter
from gunicorn_django_canonical_logs.instrumenters.registry import register_instrumenter
from gunicorn_django_canonical_logs.monitors.saturation import CurrentSaturationStats


@register_instrumenter
class SaturationInstrumenter(BaseInstrumenter):
    def call(self):
        Context.update(namespace="g", context=CurrentSaturationStats.get())
