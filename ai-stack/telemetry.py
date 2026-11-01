"""OpenTelemetry tracing for Warrant, exported as JSON lines so a run's spans can be read, diffed and committed.

In a pilot the same spans go to the customer's own collector (OTLP) instead of a file; Warrant is not a tracing product.
"""
import json

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult


class JsonlExporter(SpanExporter):
    def __init__(self, path):
        self.f = open(path, "a")

    def export(self, spans):
        for s in spans:
            self.f.write(json.dumps({
                "trace_id": f"{s.context.trace_id:032x}", "span_id": f"{s.context.span_id:016x}",
                "parent_id": f"{s.parent.span_id:016x}" if s.parent else None, "name": s.name,
                "start_ns": s.start_time, "end_ns": s.end_time, "attrs": dict(s.attributes or {}),
                "status": s.status.status_code.name}) + "\n")
        self.f.flush()
        return SpanExportResult.SUCCESS

    def shutdown(self):
        self.f.close()


_provider = None


def setup(path):
    """Send spans to a JSONL file. Call once per run."""
    global _provider
    if _provider is None:
        _provider = TracerProvider()
        trace.set_tracer_provider(_provider)
    _provider.add_span_processor(SimpleSpanProcessor(JsonlExporter(path)))


tracer = trace.get_tracer("warrant")


def load(path):
    """Spans grouped by trace, each with start and duration in ms relative to its trace's first span."""
    spans = [json.loads(l) for l in open(path)]
    by_id = {s["span_id"]: s["name"] for s in spans}
    out = {}
    for s in spans:
        out.setdefault(s["trace_id"], []).append(s)
    for tid, group in out.items():
        t0 = min(s["start_ns"] for s in group)
        out[tid] = sorted([{"name": s["name"], "start_ms": round((s["start_ns"] - t0) / 1e6, 1),
                            "dur_ms": round((s["end_ns"] - s["start_ns"]) / 1e6, 1), "attrs": s["attrs"],
                            "parent": by_id.get(s["parent_id"])} for s in group], key=lambda x: x["start_ms"])
    return out
