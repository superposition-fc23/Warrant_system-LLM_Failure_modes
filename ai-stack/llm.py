"""One way to call any model in the registry: ask(), speak(), transcribe().

Each provider uses its own official SDK. Keys come from .env (copy .env.example).
Run directly to smoke-test every model whose key is set:  .venv/bin/python llm.py
"""
import os

from dotenv import load_dotenv

load_dotenv()

# Model registry. The router picks a key from here. Costs are USD per 1M input/output tokens
# (Claude from Anthropic's price list; others are approximate, check the provider before quoting).
MODELS = {
    "opus-5.5":   {"provider": "anthropic", "id": "claude-opus-5-5",   "cost": (4.00, 20.00), "modality": "text,image"},
    "opus-5":     {"provider": "anthropic", "id": "claude-opus-5",     "cost": (5.00, 25.00), "modality": "text,image"},
    "sonnet-5.5": {"provider": "anthropic", "id": "claude-sonnet-5-5", "cost": (2.00, 10.00), "modality": "text,image"},
    "sonnet-5":   {"provider": "anthropic", "id": "claude-sonnet-5",   "cost": (2.00, 10.00), "modality": "text,image"},
    "haiku-5.5":  {"provider": "anthropic", "id": "claude-haiku-5-5",  "cost": (0.10, 0.50),  "modality": "text,image"},
    "gpt-5.6-sol": {"provider": "openai", "id": "gpt-5.6-sol",         "cost": (5.00, 30.00), "modality": "text,image"},
    "gemini-3.6-flash": {"provider": "google", "id": "gemini-3.6-flash", "cost": (1.50, 7.50), "modality": "text,image,audio"},
    "deepgram-aura": {"provider": "deepgram", "id": "aura-2-thalia-en", "cost": None, "modality": "tts"},
    "deepgram-stt":  {"provider": "deepgram", "id": "nova-3",           "cost": None, "modality": "stt"},
    "fake":       {"provider": "fake", "id": "fake-model", "cost": (1.00, 5.00), "modality": "text"},   # tests only; scripted by FAKE_SCRIPT
}

KEY_ENV = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY",
           "google": "GEMINI_API_KEY", "deepgram": "DEEPGRAM_API_KEY", "fake": None}

# Claude models that accept server-side refusal fallbacks (beta).
_FALLBACK_OK = {"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}

# Token usage of the last ask() call, (input, output), for traces and cost per decision.
LAST_USAGE = (0, 0)
LAST_META = {"served_model": None, "stop_reason": None}


def key_env(model_key: str) -> str | None:
    m = MODELS[model_key]
    return m.get("key_env") or KEY_ENV.get(m["provider"])


def has_key(model_key: str) -> bool:
    env = key_env(model_key)
    return env is None or bool(os.getenv(env))


# Fake provider for tests: each call pops the next item. {"status": 429, "retry_after": 0} raises like an SDK error;
# {"text": ..., "finish": "stop" | "length", "usage": (in, out)} is a reply. FAKE_CALLS records every attempt.
FAKE_SCRIPT: list = []
FAKE_CALLS: list = []


class FakeStatusError(Exception):
    def __init__(self, status, retry_after=None):
        super().__init__(f"fake provider returned {status}")
        self.status_code = status
        self.response = type("R", (), {"status_code": status, "headers": {"retry-after": str(retry_after)} if retry_after is not None else {}})()


def register_together(name: str, model_id: str, key_env_name: str, cost: tuple | None = None, reasoning: bool | str | None = False):
    """Add a Together model under a role name. cost is USD per 1M (input, output); None looks it up from Together's model list on first use.
    reasoning=False sends reasoning.enabled=false, so a hybrid model does not spend the gate's output cap on thinking; "low", "medium" or
    "high" sends reasoning_effort; None sends nothing. The API returns 200 for a control a model ignores, so check reasoning tokens on the span."""
    MODELS[name] = {"provider": "together", "id": model_id, "key_env": key_env_name, "cost": cost, "modality": "text", "reasoning": reasoning}


def _effort(v):
    """off / on / unset, a named level (low, high, xhigh, max), or a number 1 to 100 (DeepSeek V4.1 takes numbers, not "medium")."""
    named = {"on": True, "off": False, "unset": None}
    if v in named:
        return named[v]
    return int(v) if v.isdigit() else v


# Roles read from .env, so a model choice is a config change, not a code change. Each role has its own key, for cost by key.
for _role in ("GATE", "JUDGE2", "JUDGE3"):
    if os.getenv(f"TOGETHER_{_role}_MODEL"):
        register_together(f"together-{_role.lower()}", os.getenv(f"TOGETHER_{_role}_MODEL"), f"TOGETHER_{_role}_API_KEY",
                          reasoning=_effort(os.getenv(f"TOGETHER_{_role}_REASONING", "off")))


def _together_client(key_env_name):
    from openai import OpenAI
    return OpenAI(api_key=os.getenv(key_env_name), base_url=os.getenv("TOGETHER_BASE_URL", "https://api.together.ai/v1"), max_retries=0, timeout=120)


TOGETHER_CLIENT = _together_client    # tests replace this
_LOCAL = __import__("threading").local()    # per-thread extras from the last provider reply, copied onto its llm.call span
_PRICES: dict = {}


def together_models(key_env_name="TOGETHER_GATE_API_KEY") -> list:
    """Together's serverless model list with prices, straight from the API (free to call)."""
    import httpx
    r = httpx.get(os.getenv("TOGETHER_BASE_URL", "https://api.together.ai/v1") + "/models",
                  headers={"Authorization": f"Bearer {os.getenv(key_env_name)}"}, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data["data"] if isinstance(data, dict) else data


def cost_of(model_key: str) -> tuple:
    m = MODELS[model_key]
    if m.get("cost") is not None:
        return m["cost"]
    if m["provider"] == "together":
        if not _PRICES:
            for x in together_models(m["key_env"]):
                p = x.get("pricing") or {}
                if "input" in p and "output" in p:
                    _PRICES[x["id"]] = (float(p["input"]), float(p["output"]))
        if m["id"] not in _PRICES:
            raise RuntimeError(f"no price found for {m['id']}; set cost when registering it, so the budget can work")
        m["cost"] = _PRICES[m["id"]]
        return m["cost"]
    return (0.0, 0.0)


RECORD_TEXT = os.getenv("WARRANT_RECORD_TEXT", "1") == "1"    # prompts and replies on spans; callers scrub PII before calling


def _anthropic(m, prompt, system, max_tokens, effort, schema):
    import anthropic
    # Keys not scoped to a workspace need the workspace id sent as a header. The guard retries, so the SDK must not.
    ws = os.getenv("ANTHROPIC_WORKSPACE_ID")
    client = anthropic.Anthropic(default_headers={"anthropic-workspace-id": ws} if ws else None, max_retries=0)
    kwargs = dict(model=m["id"], max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}],
                  output_config={"effort": effort, **({"format": {"type": "json_schema", "schema": schema}} if schema else {})})
    if system:
        kwargs["system"] = system
    if m["id"] in _FALLBACK_OK:
        resp = client.beta.messages.create(**kwargs, betas=["server-side-fallback-2026-07-01"], fallbacks="default")
    else:
        resp = client.messages.create(**kwargs)
    if resp.stop_reason == "refusal":
        text = f"[refused: {resp.stop_details.category if resp.stop_details else 'unknown'}]"
    else:
        text = "".join(b.text for b in resp.content if b.type == "text")
    return text, resp.stop_reason, resp.model, (resp.usage.input_tokens, resp.usage.output_tokens)


def _together(m, prompt, system, max_tokens, effort, schema):
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    kwargs = dict(model=m["id"], messages=messages, max_tokens=max_tokens)
    if schema:
        kwargs["response_format"] = {"type": "json_schema", "json_schema": {"name": "reply", "schema": schema, "strict": True}}
    if isinstance(m.get("reasoning"), (str, int)) and not isinstance(m.get("reasoning"), bool):
        kwargs["reasoning_effort"] = m["reasoning"]
    elif m.get("reasoning") is not None:
        kwargs["extra_body"] = {"reasoning": {"enabled": m["reasoning"]}}
    resp = TOGETHER_CLIENT(m["key_env"]).chat.completions.create(**kwargs)
    choice = resp.choices[0]
    thought = getattr(choice.message, "reasoning", None) or getattr(choice.message, "reasoning_content", None)
    details = getattr(resp.usage, "completion_tokens_details", None)
    rtok = getattr(details, "reasoning_tokens", None) if details else None
    _LOCAL.reasoning = {"llm.reasoning_chars": len(thought) if thought else 0, **({"llm.token_count.reasoning": rtok} if rtok is not None else {})}
    stop = {"length": "max_tokens", "stop": "end_turn"}.get(choice.finish_reason, choice.finish_reason)
    return choice.message.content or "", stop, resp.model, (resp.usage.prompt_tokens, resp.usage.completion_tokens)


def _fake(m, prompt, system, max_tokens, effort, schema):
    FAKE_CALLS.append(prompt)
    item = FAKE_SCRIPT.pop(0) if FAKE_SCRIPT else {"text": "{}", "finish": "stop", "usage": (1, 1)}
    if "status" in item:
        raise FakeStatusError(item["status"], item.get("retry_after"))
    stop = {"length": "max_tokens", "stop": "end_turn"}.get(item["finish"], item["finish"])
    return item["text"], stop, "fake-model", tuple(item["usage"])


def _openai(m, prompt, system, max_tokens, effort, schema):
    from openai import OpenAI
    resp = OpenAI(max_retries=0).responses.create(model=m["id"], instructions=system or None, input=prompt)
    u = getattr(resp, "usage", None)
    return resp.output_text, "end_turn", m["id"], ((u.input_tokens, u.output_tokens) if u else (0, 0))


def _google(m, prompt, system, max_tokens, effort, schema):
    from google import genai
    from google.genai import types
    config = types.GenerateContentConfig(system_instruction=system) if system else None
    resp = genai.Client().models.generate_content(model=m["id"], contents=prompt, config=config)
    return resp.text, "end_turn", m["id"], (0, 0)


_PROVIDERS = {"anthropic": _anthropic, "together": _together, "fake": _fake, "openai": _openai, "google": _google}


def ask(model_key: str, prompt: str, system: str = "", max_tokens: int = 16000, effort: str = "medium", schema: dict | None = None, meta: dict | None = None) -> str:
    """Send one text prompt, return the text answer. Pass meta to get usage per call, which parallel calls need.
    Every call goes through callguard: retries as separate spans, rate and budget limits, loop detection. A refused call raises callguard.GuardError."""
    import callguard
    from opentelemetry import trace
    m = MODELS[model_key]
    if m["modality"] in ("tts", "stt"):
        raise ValueError(f"{model_key} is a {m['modality']} model; use speak() or transcribe()")
    if not has_key(model_key):
        raise RuntimeError(f"{key_env(model_key)} is not set in .env, so {model_key} can't be called")
    with trace.get_tracer("warrant.llm").start_as_current_span("llm.call") as sp:
        for k, v in {"openinference.span.kind": "LLM", "llm.provider": m["provider"], "llm.model_name": m["id"], "llm.max_tokens": max_tokens}.items():
            sp.set_attribute(k, v)
        if RECORD_TEXT:
            msgs = ([("system", system)] if system else []) + [("user", prompt)]
            for i, (role, content) in enumerate(msgs):
                sp.set_attribute(f"llm.input_messages.{i}.message.role", role)
                sp.set_attribute(f"llm.input_messages.{i}.message.content", content)
        _LOCAL.reasoning = {}
        text, stop, served, usage = callguard.GUARD.call(m["provider"], prompt, lambda: _PROVIDERS[m["provider"]](m, prompt, system, max_tokens, effort, schema), sp)
        cin, cout = cost_of(model_key)
        usd = (usage[0] * cin + usage[1] * cout) / 1e6
        callguard.GUARD.spend(usd, *usage)
        for k, v in {"llm.token_count.prompt": usage[0], "llm.token_count.completion": usage[1], "llm.response.model": served or "",
                     "llm.finish_reason": stop or "", "cost_usd": round(usd, 6), **getattr(_LOCAL, "reasoning", {})}.items():
            sp.set_attribute(k, v)
        if RECORD_TEXT:
            sp.set_attribute("llm.output_messages.0.message.role", "assistant")
            sp.set_attribute("llm.output_messages.0.message.content", text)
    global LAST_USAGE, LAST_META
    LAST_USAGE = tuple(usage)
    LAST_META = {"served_model": served, "stop_reason": stop}
    if meta is not None:
        meta.update(LAST_META, usage=LAST_USAGE)
    return text


def speak(text: str, out_path: str = "speech.mp3", model_key: str = "deepgram-aura") -> str:
    """Text to speech with Deepgram Aura. Returns the saved audio file path."""
    from deepgram import DeepgramClient
    audio = DeepgramClient().speak.v1.audio.generate(text=text, model=MODELS[model_key]["id"])
    with open(out_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return out_path


def transcribe(audio_path: str, model_key: str = "deepgram-stt") -> str:
    """Speech to text for a recorded file. (Flux is for live streams over a WebSocket; see README.)"""
    from deepgram import DeepgramClient
    with open(audio_path, "rb") as f:
        resp = DeepgramClient().listen.v1.media.transcribe_file(
            request=f.read(), model=MODELS[model_key]["id"], smart_format=True)
    return resp.results.channels[0].alternatives[0].transcript


if __name__ == "__main__":
    for key, m in MODELS.items():
        if m["modality"] in ("tts", "stt"):
            continue
        if m["provider"] == "fake":
            continue
        if not has_key(key):
            print(f"{key:18} skipped, no {key_env(key)}")
            continue
        try:
            print(f"{key:18} {ask(key, 'Reply with exactly: ok', max_tokens=2000, effort='low').strip()[:60]}")
        except Exception as e:
            print(f"{key:18} ERROR {type(e).__name__}: {str(e)[:120]}")
    if os.getenv("DEEPGRAM_API_KEY"):
        path = speak("Your action was held: the governing belief is out of date.")
        print(f"deepgram-aura      saved {path}; transcribed back: {transcribe(path)!r}")
    else:
        print("deepgram           skipped, no DEEPGRAM_API_KEY")
