#!/usr/bin/env python3
"""The Director deep module for first-frame decisions.

The module is deliberately pure: it receives a locked script projection and a
first-frame Segment, then returns a new, executable visual plan.  It never
mutates or writes the locked script.  Prompt compilation consumes this output
instead of making camera, composition, performance, or continuity decisions
itself.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping


VARIANTS = ("A", "B")


def _digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _text(value: Any, fallback: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _variant_delta(segment: Mapping[str, Any], variant: str, explicit: str | None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    variants = segment.get("director_variants")
    if isinstance(variants, Mapping):
        value = variants.get(variant)
        if isinstance(value, Mapping):
            delta = value.get("variant_delta")
            if isinstance(delta, str) and delta.strip():
                return delta.strip()
        if isinstance(value, str) and value.strip():
            return value.strip()
    return (
        "Prioritize proof clarity and product-contact visibility; preserve the locked script semantics and proof order."
        if variant == "A"
        else "Prioritize reaction readability and wider scene context; preserve the locked script semantics and proof order."
    )


def direct_segment(
    segment: Mapping[str, Any],
    *,
    variant: str = "A",
    variant_delta: str | None = None,
) -> dict[str, Any]:
    """Resolve one Segment into a Director-owned first-frame decision.

    The locked Beat timeline remains separate metadata. The `first_frame`
    object defines only the entering state at local t=0.
    """

    if variant not in VARIANTS:
        raise ValueError(f"Director variant must be A or B, got {variant!r}")
    raw_first_frame = segment.get("first_frame")
    if not isinstance(raw_first_frame, Mapping):
        raise ValueError("Director requires exactly one first_frame decision")
    human_presence = raw_first_frame.get("human_presence")
    if human_presence not in {"none", "one_hand", "partial_person", "full_person"}:
        raise ValueError("Director first_frame has invalid human_presence")
    first_frame = {
        "time": 0,
        "static_moment": _text(
            raw_first_frame.get("static_moment"),
            "One frozen, directly observable entering-state instant at local t=0.",
        ),
        "camera": _text(raw_first_frame.get("camera"), "Natural eye-level phone framing."),
        "composition": _text(
            raw_first_frame.get("composition"),
            "Keep the entering product state and relevant subject/action context unobstructed in frame.",
        ),
        "performance": _text(
            raw_first_frame.get("performance"),
            "No visible human performance." if human_presence == "none" else f"Use natural {human_presence} performance only.",
        ),
        "continuity": _text(
            raw_first_frame.get("continuity"),
            "Carry forward the approved Segment entering state without an unexplained change.",
        ),
        "human_presence": human_presence,
    }

    continuity_values = segment.get("visual_continuity")
    if not isinstance(continuity_values, list) or not all(
        isinstance(value, str) and value.strip() for value in continuity_values
    ):
        raise ValueError("Director requires non-empty visual_continuity")

    return {
        "module": "Director",
        "variant": variant,
        "variant_delta": _variant_delta(segment, variant, variant_delta),
        "visual_continuity": [value.strip() for value in continuity_values],
        "first_frame": first_frame,
        "script_mutation": "forbidden",
    }


def direct_plan(
    plan: Mapping[str, Any],
    *,
    locked_script: Mapping[str, Any] | None = None,
    variant: str = "A",
) -> dict[str, Any]:
    """Direct every first-frame Segment without mutating the locked script."""

    script_snapshot = deepcopy(locked_script) if locked_script is not None else None
    before = _digest(script_snapshot) if isinstance(script_snapshot, Mapping) else None
    result = deepcopy(dict(plan))
    segments = result.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError("Director requires a non-empty plan.segments list")
    result["director"] = {
        "module": "Director",
        "variant": variant,
        "script_mutation": "forbidden",
    }
    result["director_segments"] = []
    for segment in segments:
        if not isinstance(segment, Mapping):
            raise ValueError("Director plan segments must be objects")
        result["director_segments"].append(direct_segment(segment, variant=variant))
    if isinstance(script_snapshot, Mapping) and before != _digest(script_snapshot):
        raise RuntimeError("Director mutated the locked script projection")
    return result
