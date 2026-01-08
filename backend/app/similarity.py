from __future__ import annotations

from dataclasses import dataclass
from math import sqrt, fabs
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class HitterVector:
    playerID: str
    name: str
    year: int
    AB: int
    features: Tuple[float, ...]  # (HR_rate, BB_rate, SO_rate, H_rate, SB_rate)


def _safe_rate(num: float, den: float) -> float:
    return float(num) / float(den) if den and den > 0 else 0.0


def build_hitter_vector(row: Dict) -> HitterVector:
    """
    row expected keys: playerID, name, year, AB, HR, BB, SO, H, SB
    """
    ab = int(row.get("AB", 0) or 0)
    hr = float(row.get("HR", 0) or 0)
    bb = float(row.get("BB", 0) or 0)
    so = float(row.get("SO", 0) or 0)
    h  = float(row.get("H", 0) or 0)
    sb = float(row.get("SB", 0) or 0)

    feats = (
        _safe_rate(hr, ab),
        _safe_rate(bb, ab),
        _safe_rate(so, ab),
        _safe_rate(h, ab),
        _safe_rate(sb, ab),
    )

    return HitterVector(
        playerID=str(row["playerID"]),
        name=str(row.get("name") or ""),
        year=int(row["year"]),
        AB=ab,
        features=feats,
    )


def cosine_similarity(a: Tuple[float, ...], b: Tuple[float, ...]) -> float:
    if len(a) != len(b):
        raise ValueError("Vectors must be same length")

    dot = sum(x * y for x, y in zip(a, b))
    na = sqrt(sum(x * x for x in a))
    nb = sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def top_k_similar(
    target: HitterVector,
    candidates: Iterable[HitterVector],
    k: int = 10,
) -> List[Tuple[HitterVector, float]]:
    scored: List[Tuple[HitterVector, float]] = []
    for c in candidates:
        if c.playerID == target.playerID:
            continue
        scored.append((c, cosine_similarity(target.features, c.features)))

    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:k]

FEATURE_NAMES = ["HR/AB", "BB/AB", "SO/AB", "H/AB", "SB/AB"]

_DIRECTION_LABELS = {
    "HR/AB": "home-run rate",
    "BB/AB": "walk rate",
    "SO/AB": "strikeout rate",
    "H/AB":  "hit rate",
    "SB/AB": "steal rate",
}

def _fmt(x: float, decimals: int = 3) -> str:
    return f"{x:.{decimals}f}"

def _direction(feature: str, delta: float) -> str:
    # delta = candidate - target
    if abs(delta) < 1e-12:
        return "about the same"
    more_or_less = "higher" if delta > 0 else "lower"
    return f"{more_or_less} { _DIRECTION_LABELS.get(feature, feature) }"

def compute_feature_deltas(
    target_features: Tuple[float, ...],
    cand_features: Tuple[float, ...],
    feature_names: List[str] = FEATURE_NAMES,
    eps: float = 1e-12,
) -> List[Dict]:
    """
    Returns feature-by-feature values with both 'closeness' and abs(delta).
    closeness = 1 / (1 + abs(delta))  -> higher means closer.
    """
    if len(target_features) != len(cand_features):
        raise ValueError("Vectors must be same length")

    out = []
    for name, t, c in zip(feature_names, target_features, cand_features):
        delta = c - t
        out.append(
            {
                "feature": name,
                "target": t,
                "candidate": c,
                "delta": delta,
                "abs_delta": fabs(delta),
                "closeness": 1.0 / (1.0 + fabs(delta) + eps),
            }
        )
    return out

def feature_closeness(
    target_features: tuple[float, ...],
    cand_features: tuple[float, ...],
    feature_names: List[str] = FEATURE_NAMES,
    eps: float = 1e-12,
) -> List[Dict]:
    """
    Produces per-feature deltas and a 'closeness' score in (0, 1].
    closeness = 1 / (1 + abs(delta))  -> higher means closer.
    """
    if len(target_features) != len(cand_features):
        raise ValueError("Vectors must be same length")

    out = []
    for name, t, c in zip(feature_names, target_features, cand_features):
        delta = c - t
        closeness = 1.0 / (1.0 + fabs(delta) + eps)
        out.append(
            {
                "feature": name,
                "target": t,
                "candidate": c,
                "delta": delta,
                "closeness": closeness,
            }
        )

    # Sort most “similar” features first
    out.sort(key=lambda d: d["closeness"], reverse=True)
    return out


def explain_similarity(target, candidate, top_similar: int = 2, top_different: int = 2) -> Dict:
    feats = compute_feature_deltas(target.features, candidate.features)

    similarities = sorted(feats, key=lambda d: d["closeness"], reverse=True)[:top_similar]
    differences  = sorted(feats, key=lambda d: d["abs_delta"], reverse=True)[:top_different]

    # Build a concise analyst-style summary
    sim_bits = [
        f"{f['feature']} is similar ({_fmt(f['target'])} vs {_fmt(f['candidate'])})"
        for f in similarities
    ]
    diff_bits = [
        f"{f['feature']} is {('higher' if f['delta'] > 0 else 'lower')} for the candidate "
        f"({_fmt(f['candidate'])} vs {_fmt(f['target'])})"
        for f in differences
    ]

    summary = ""
    if sim_bits:
        summary += "Similar: " + ", ".join(sim_bits) + ". "
    if diff_bits:
        summary += "Key differences: " + ", ".join(diff_bits) + "."

    return {
        "similarities": similarities,
        "differences": differences,
        "summary": summary.strip(),
        "all_features": feats,
    }
