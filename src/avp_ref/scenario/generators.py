"""Deterministic built-in AVS parameter generators."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .errors import CompileDiagnostic, ParameterResolutionError

Generator = Callable[[Mapping[str, Any], random.Random], Any]


def _integer(spec: Mapping[str, Any], rng: random.Random) -> int:
    return rng.randint(int(spec["min"]), int(spec["max"]))


def _uniform(spec: Mapping[str, Any], rng: random.Random) -> float:
    return rng.uniform(float(spec["min"]), float(spec["max"]))


def _enum(spec: Mapping[str, Any], rng: random.Random) -> Any:
    values = list(spec.get("values", ()))
    if not values:
        raise ValueError("enum generator requires non-empty values")
    return values[rng.randrange(len(values))]


def _weighted(spec: Mapping[str, Any], rng: random.Random) -> Any:
    choices = list(spec.get("choices", ()))
    if not choices:
        raise ValueError("weighted generator requires choices")
    values = [item["value"] for item in choices]
    weights = [float(item["weight"]) for item in choices]
    return rng.choices(values, weights=weights, k=1)[0]


@dataclass(frozen=True, slots=True)
class GeneratorRegistry:
    """Registry of deterministic generators with explicit implementation version."""

    version: str = "builtin-generators@1"

    def generate(self, parameter: str, spec: Mapping[str, Any], seed: int) -> Any:
        generator_type = str(spec.get("type", ""))
        generators: dict[str, Generator] = {
            "integer": _integer,
            "uniform": _uniform,
            "enum": _enum,
            "weighted": _weighted,
        }
        generator = generators.get(generator_type)
        if generator is None:
            raise ParameterResolutionError(
                f"unsupported generator '{generator_type}' for parameter '{parameter}'",
                (
                    CompileDiagnostic(
                        "AVS-GEN-001",
                        f"unsupported deterministic generator '{generator_type}'",
                        f"$.parameters.{parameter}.generator.type",
                    ),
                ),
            )
        try:
            return generator(spec, random.Random(seed))
        except (KeyError, TypeError, ValueError) as exc:
            raise ParameterResolutionError(
                f"invalid generator for parameter '{parameter}'",
                (CompileDiagnostic("AVS-GEN-002", str(exc), f"$.parameters.{parameter}.generator"),),
            ) from exc
