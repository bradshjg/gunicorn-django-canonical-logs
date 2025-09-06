from gunicorn_django_wide_events.event_context import Context
from gunicorn_django_wide_events.instrumenters.base import BaseInstrumenter
from gunicorn_django_wide_events.instrumenters.instrumenters import register_instrumenter
from gunicorn_django_wide_events.monitors.saturation import CurrentSaturationStats


@register_instrumenter
class SaturationInstrumenter(BaseInstrumenter):
    def call(self):
        Context.update(namespace="g", context=CurrentSaturationStats.get())
