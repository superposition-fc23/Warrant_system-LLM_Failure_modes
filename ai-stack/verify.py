"""Recheck the arithmetic behind a model's conflict in code (arm A+verify).

A conflict that rests on numbers or dates carries a claim {left, op, right}. Each side is a small expression: numbers, + - * /,
pct(p, base) for p% of base, and days(from, to) for the days between two ISO dates. Code evaluates it. A claim that is false drops
the conflict, the way a citation of a record that doesn't exist is dropped. A conflict with no claim, an expression code can't read,
or a number that isn't in the proposal or the records is kept: verification only ever removes a conflict it can prove wrong.
"""
import ast
import operator
import re
from datetime import date

CHECKABLE_KINDS = {"amount", "contract_terms", "entitlement"}    # never injection, payment risk, duplicates, authority or currency
FREE_CONSTANTS = {0.0, 1.0, 100.0}
OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "!=": None}    # a claim states a violation, so "==" is not one
_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
_DATE = re.compile(r"(?<![\"'\d])(\d{4}-\d{2}-\d{2})(?![\"'\d])")


def _quote_dates(expr):
    return _DATE.sub(r'"\1"', expr)


def _walk(node, numbers, dates):
    if isinstance(node, ast.Expression):
        return _walk(node.body, numbers, dates)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        numbers.append(float(node.value))
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_walk(node.operand, numbers, dates)
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        return _BIN[type(node.op)](_walk(node.left, numbers, dates), _walk(node.right, numbers, dates))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords and len(node.args) == 2:
        if node.func.id == "pct":
            return _walk(node.args[0], numbers, dates) / 100.0 * _walk(node.args[1], numbers, dates)
        if node.func.id == "days" and all(isinstance(a, ast.Constant) and isinstance(a.value, str) for a in node.args):
            a, b = (date.fromisoformat(x.value) for x in node.args)
            dates.extend(x.value for x in node.args)
            return float((b - a).days)
    raise ValueError("not allowed")


def evaluate(expr, numbers=None, dates=None):
    """The value of a claim side, or None if it isn't a plain expression this module allows."""
    try:
        return _walk(ast.parse(_quote_dates(str(expr)), mode="eval"), numbers if numbers is not None else [], dates if dates is not None else [])
    except Exception:
        return None


def _in_text(n, text):
    forms = {f"{int(n)}", f"{int(n):,}"} if n == int(n) else {repr(n), f"{n:g}"}
    return any(re.search(rf"(?<![\d.]){re.escape(f)}(?![\d])", text) for f in forms)


def _grounded(numbers, dates, text):
    return all(n in FREE_CONSTANTS or _in_text(abs(n), text) for n in numbers) and all(d in text for d in dates)


def judge(claim, text):
    """True or False when code can decide the claim from numbers in text; None when it can't."""
    if not isinstance(claim, dict) or claim.get("op") not in OPS:
        return None
    numbers, dates = [], []
    left, right = evaluate(claim.get("left"), numbers, dates), evaluate(claim.get("right"), numbers, dates)
    if left is None or right is None or not _grounded(numbers, dates, text):
        return None
    op = claim["op"]
    if op == "!=":
        return abs(left - right) > 1e-6 * max(1.0, abs(left), abs(right))
    return OPS[op](left, right)


def check(data, text):
    """Drop conflicts whose claim code proves false. Returns (data with the kept conflicts, the refuted conflicts)."""
    kept, refuted = [], []
    for c in data.get("conflicts", []):
        verdict = judge(c.get("claim"), text) if c.get("kind") in CHECKABLE_KINDS else None
        (refuted if verdict is False else kept).append(c)
    return {**data, "conflicts": kept}, refuted
