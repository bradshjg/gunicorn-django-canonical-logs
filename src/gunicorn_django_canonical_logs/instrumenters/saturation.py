from gunicorn_django_canonical_logs.event_context import Context
from gunicorn_django_canonical_logs.instrumenters.protocol import InstrumenterProtocol
from gunicorn_django_canonical_logs.instrumenters.registry import register_instrumenter
from gunicorn_django_canonical_logs.monitors.saturation import CurrentSaturationStats


@register_instrumenter
class SaturationInstrumenter(InstrumenterProtocol):
    def call(self, _req, _resp, _environ):
        Context.update(namespace="g", context=CurrentSaturationStats.get())
