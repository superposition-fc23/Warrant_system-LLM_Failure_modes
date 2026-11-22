"""Model-call guardrails, written before the call layer: retries are visible, limits hold, and the gate fails closed when the model is refused.
Every test uses the fake provider or a stubbed client, so none of them calls a real API or spends money.

    .venv/bin/python test_callguard.py
"""
import asyncio
import json
import types

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

SPANS = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(SPANS))
trace.set_tracer_provider(_provider)

import callguard  # noqa: E402
import llm  # noqa: E402

TRACER = trace.get_tracer("test")
OK = {"text": '{"ok": true}', "finish": "stop", "usage": (100, 20)}


def fresh(**limits):
    """A new guard with no sleeping, and an empty span list."""
    callguard.GUARD = callguard.Guard(callguard.Limits(**{"base_backoff": 0.0, **limits}), sleep=lambda s: None)
    SPANS.clear()
    llm.FAKE_CALLS.clear()


def named(name):
    return [s for s in SPANS.get_finished_spans() if s.name == name]


def test_retries_are_visible_one_span_per_attempt():
    fresh(max_attempts=3)
    llm.FAKE_SCRIPT[:] = [{"status": 429, "retry_after": 0}, {"status": 529}, OK]
    with TRACER.start_as_current_span("case"):
        out = llm.ask("fake", "hello", schema={"type": "object"})
    assert out == '{"ok": true}'
    attempts = named("llm.attempt")
    assert len(attempts) == 3, len(attempts)
    assert [a.attributes.get("http.response.status_code") for a in attempts] == [429, 529, 200]
    call = named("llm.call")[0]
    assert call.attributes["llm.retry_count"] == 2
    t = callguard.GUARD.totals
    assert t["retries"] == 2 and t["rate_limited"] == 1 and t["calls"] == 1, t


def test_breaker_opens_after_repeated_failures_and_stops_calling():
    fresh(max_attempts=3, breaker_threshold=3)
    llm.FAKE_SCRIPT[:] = [{"status": 429}] * 10
    try:
        llm.ask("fake", "a")
        raise AssertionError("should have failed")
    except callguard.GuardError:
        pass
    before = len(llm.FAKE_CALLS)
    try:
        llm.ask("fake", "b")
        raise AssertionError("should be refused")
    except callguard.CircuitOpen:
        pass
    assert len(llm.FAKE_CALLS) == before, "an open breaker must not reach the provider"


def test_auth_or_billing_error_opens_breaker_at_once():
    fresh(max_attempts=5)
    llm.FAKE_SCRIPT[:] = [{"status": 402}, OK]
    try:
        llm.ask("fake", "a")
        raise AssertionError("should be refused")
    except callguard.CircuitOpen:
        pass
    assert len(llm.FAKE_CALLS) == 1, "a suspended key is not retried"


def test_run_budget_stops_spending():
    fresh(run_max_usd=0.0002)
    llm.FAKE_SCRIPT[:] = [OK, OK, OK]
    llm.ask("fake", "a")
    try:
        llm.ask("fake", "b")
        llm.ask("fake", "c")
        raise AssertionError("budget should stop the run")
    except callguard.BudgetExceeded:
        pass


def test_same_prompt_repeated_in_one_trace_is_a_loop():
    fresh(repeat_max=3)
    llm.FAKE_SCRIPT[:] = [OK] * 10
    with TRACER.start_as_current_span("case"):
        for _ in range(3):
            llm.ask("fake", "same prompt")
        try:
            llm.ask("fake", "same prompt")
            raise AssertionError("fourth identical call should be a loop")
        except callguard.LoopDetected:
            pass
    with TRACER.start_as_current_span("another case"):
        llm.ask("fake", "same prompt")    # a new trace starts its own count


def test_calls_per_trace_are_capped():
    fresh(trace_max_calls=4)
    llm.FAKE_SCRIPT[:] = [OK] * 10
    with TRACER.start_as_current_span("case"):
        for i in range(4):
            llm.ask("fake", f"p{i}")
        try:
            llm.ask("fake", "p5")
            raise AssertionError("fifth call in one trace should be refused")
        except callguard.LoopDetected:
            pass


def test_a_cut_off_reply_reports_max_tokens():
    fresh()
    llm.FAKE_SCRIPT[:] = [{"text": '{"ok": tr', "finish": "length", "usage": (100, 2000)}]
    meta = {}
    llm.ask("fake", "a", meta=meta)
    assert meta["stop_reason"] == "max_tokens", meta


def test_prompt_and_reply_are_on_the_span():
    fresh()
    llm.FAKE_SCRIPT[:] = [OK]
    llm.ask("fake", "the user prompt", system="the system prompt")
    a = named("llm.call")[0].attributes
    assert a["openinference.span.kind"] == "LLM"
    assert a["llm.input_messages.0.message.content"] == "the system prompt"
    assert a["llm.input_messages.1.message.content"] == "the user prompt"
    assert a["llm.output_messages.0.message.content"] == '{"ok": true}'
    assert a["llm.token_count.prompt"] == 100 and a["llm.token_count.completion"] == 20


def test_together_request_and_reply_mapping():
    fresh()
    seen = {}

    def create(**kw):
        seen.update(kw)
        msg = types.SimpleNamespace(content='{"a": 1}')
        return types.SimpleNamespace(model="served-id", choices=[types.SimpleNamespace(message=msg, finish_reason="length")],
                                     usage=types.SimpleNamespace(prompt_tokens=50, completion_tokens=7))
    client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create)))
    llm.register_together("tg-test", "org/model-x", "TOGETHER_TEST_KEY", cost=(1.0, 2.0))
    llm.TOGETHER_CLIENT = lambda key_env: client
    import os
    os.environ["TOGETHER_TEST_KEY"] = "test-not-a-real-key"
    meta = {}
    out = llm.ask("tg-test", "u", system="s", max_tokens=123, schema={"type": "object"}, meta=meta)
    assert out == '{"a": 1}'
    assert seen["model"] == "org/model-x" and seen["max_tokens"] == 123
    assert seen["messages"] == [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
    rf = seen["response_format"]
    assert rf["type"] == "json_schema" and rf["json_schema"]["schema"] == {"type": "object"} and rf["json_schema"]["strict"] is True
    assert meta["stop_reason"] == "max_tokens" and meta["served_model"] == "served-id" and meta["usage"] == (50, 7)
    assert seen["extra_body"] == {"reasoning": {"enabled": False}}, "hybrid models must not think inside the gate's output cap by default"


def test_reasoning_effort_is_sent_as_a_top_level_parameter():
    fresh()
    seen = {}

    def create(**kw):
        seen.update(kw)
        msg = types.SimpleNamespace(content="{}", reasoning_content="thinking")
        usage = types.SimpleNamespace(prompt_tokens=5, completion_tokens=50, completion_tokens_details=types.SimpleNamespace(reasoning_tokens=45))
        return types.SimpleNamespace(model="m", choices=[types.SimpleNamespace(message=msg, finish_reason="stop")], usage=usage)
    llm.TOGETHER_CLIENT = lambda key_env: types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create)))
    llm.register_together("tg-medium", "org/model-y", "TOGETHER_TEST_KEY", cost=(1.0, 2.0), reasoning="medium")
    llm.ask("tg-medium", "u")
    assert seen["reasoning_effort"] == "medium" and "extra_body" not in seen
    assert named("llm.call")[0].attributes["llm.token_count.reasoning"] == 45


def test_gate_holds_when_the_model_is_refused():
    import warrant
    d = json.load(open("evals/crm_cases.json"))
    case = next(c for c in d["cases"] if c["id"] == "CT-01")    # a clean case that acts when the model answers
    fresh(breaker_threshold=1, max_attempts=1)
    llm.FAKE_SCRIPT[:] = [{"status": 500}] * 20
    warrant.COMPARE_MODEL = "fake"
    rec = asyncio.run(warrant.run(case, d["now"], d["people"], d["authority"]))
    assert rec["decision"] != "act", rec["decision"]
    tools = [s for s in SPANS.get_finished_spans() if s.name.startswith("mcp.tool ")]
    assert tools and all(s.attributes["openinference.span.kind"] == "TOOL" and "output.value" in s.attributes for s in tools if s.name != "mcp.tool authority_get_limits")
    assert named("gate.decide")[0].attributes["openinference.span.kind"] == "DECISION"
    assert any("llm.refused" in s.attributes for s in named("llm.compare")), "the refusal is recorded on the compare span"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok", t.__name__)
    print(f"{len(tests)} passed")
