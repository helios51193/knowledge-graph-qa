import re
from collections import Counter, defaultdict
from typing import Any

import inflect
from rapidfuzz import fuzz


_inflect = inflect.engine()

LABEL_THRESHOLDS = {
    "Concept": 0.82,
    "Organization": 0.90,
    "Location": 0.92,
    "Person": 0.95,
}

LABEL_PRIORITY = {
    "Organization": 4,
    "Location": 3,
    "Person": 2,
    "Concept": 1,
}


def resolve_entities(
    entities: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]], dict[str, dict[str, int]]]:
    """
    Resolve duplicate or near-duplicate entities into canonical forms.

    Returns:
    - resolved_entities: entities enriched with canonical name/label metadata
    - canonical_map: maps raw (label, name) pairs to canonical entity info
    - label_summary: per canonical entity, counts of observed labels
    """
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for entity in entities:
        grouped[entity["label"]].append(entity)

    clusters: list[list[dict[str, Any]]] = []
    for label, group in grouped.items():
        clusters.extend(_cluster_entities(group, label))

    merged_clusters = _merge_cross_label_clusters(clusters)

    canonical_map: dict[tuple[str, str], dict[str, Any]] = {}
    resolved_entities: list[dict[str, Any]] = []
    label_summary: dict[str, dict[str, int]] = {}

    for cluster in merged_clusters:
        canonical_name = _choose_canonical_name(cluster)
        canonical_label = _choose_canonical_label(cluster)
        label_counts = _build_label_counts(cluster)
        aliases = _build_aliases(cluster)

        label_summary[canonical_name] = label_counts

        for entity in cluster:
            key = (entity["label"], entity["name"])

            canonical_info = {
                "canonical_name": canonical_name,
                "canonical_label": canonical_label,
                "label_counts": label_counts,
                "aliases": aliases,
            }
            canonical_map[key] = canonical_info

            enriched = dict(entity)
            enriched["canonical_name"] = canonical_name
            enriched["canonical_label"] = canonical_label
            enriched["label_counts"] = label_counts
            enriched["aliases"] = aliases
            resolved_entities.append(enriched)

    return resolved_entities, canonical_map, label_summary


def apply_entity_resolution_to_relations(
    relations: list[dict[str, Any]],
    canonical_map: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Rewrite relation endpoints to use canonical entity names and labels.
    """
    resolved_relations: list[dict[str, Any]] = []

    for relation in relations:
        source_key = (relation.get("source_label", "Entity"), relation["source"])
        target_key = (relation.get("target_label", "Entity"), relation["target"])

        normalized_relation = dict(relation)

        source_info = canonical_map.get(source_key)
        target_info = canonical_map.get(target_key)

        if source_info:
            normalized_relation["source"] = source_info["canonical_name"]
            normalized_relation["source_label"] = source_info["canonical_label"]

        if target_info:
            normalized_relation["target"] = target_info["canonical_name"]
            normalized_relation["target_label"] = target_info["canonical_label"]

        resolved_relations.append(normalized_relation)

    return resolved_relations


def _build_aliases(cluster: list[dict[str, Any]]) -> list[str]:
    """
    Collect all distinct surface forms observed in a resolved entity cluster.
    """
    return sorted(
        {
            entity["name"].strip()
            for entity in cluster
            if entity.get("name") and entity["name"].strip()
        }
    )


def _cluster_entities(
    entities: list[dict[str, Any]],
    label: str,
) -> list[list[dict[str, Any]]]:
    """
    Cluster entities within the same label using similarity-based merging.
    """
    clusters: list[list[dict[str, Any]]] = []

    for entity in entities:
        placed = False

        for cluster in clusters:
            if _should_merge(entity, cluster, label):
                cluster.append(entity)
                placed = True
                break

        if not placed:
            clusters.append([entity])

    return clusters


def _merge_cross_label_clusters(
    clusters: list[list[dict[str, Any]]],
) -> list[list[dict[str, Any]]]:
    """
    Merge clusters across labels when names are strong enough matches.

    This helps reconcile cases where the same surface form was extracted under
    different labels, such as an entity oscillating between Person and Organization.
    """
    merged: list[list[dict[str, Any]]] = []

    for cluster in clusters:
        placed = False

        for existing in merged:
            if _should_merge_clusters(cluster, existing):
                existing.extend(cluster)
                placed = True
                break

        if not placed:
            merged.append(list(cluster))

    return merged


def _should_merge(
    entity: dict[str, Any],
    cluster: list[dict[str, Any]],
    label: str,
) -> bool:
    """
    Decide whether an entity should join an existing same-label cluster.
    """
    if label == "Person":
        if any(_looks_like_person_alias(entity, other) for other in cluster):
            return True

    threshold = LABEL_THRESHOLDS.get(label, 0.95)
    scores = [_entity_similarity(entity, other) for other in cluster]

    return max(scores, default=0.0) >= threshold


def _looks_like_person_alias(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    """
    Detect common short-form person aliases such as surname-only references.

    This intentionally uses a conservative rule:
    - one side must be a single token
    - the other side must be a short multi-token form
    - the single token must match the final token of the longer name
    """
    if left.get("label") != "Person" or right.get("label") != "Person":
        return False

    left_norm = _normalize_surface(left.get("name", ""))
    right_norm = _normalize_surface(right.get("name", ""))

    if not left_norm or not right_norm or left_norm == right_norm:
        return False

    left_tokens = [token for token in left_norm.split() if token]
    right_tokens = [token for token in right_norm.split() if token]

    if not left_tokens or not right_tokens:
        return False

    if len(left_tokens) == 1 and len(right_tokens) in {2, 3}:
        return left_tokens[0] == right_tokens[-1]

    if len(right_tokens) == 1 and len(left_tokens) in {2, 3}:
        return right_tokens[0] == left_tokens[-1]

    return False


def _should_merge_clusters(
    left_cluster: list[dict[str, Any]],
    right_cluster: list[dict[str, Any]],
) -> bool:
    """
    Decide whether two clusters from different labels should be merged.
    """
    scores: list[float] = []

    for left in left_cluster:
        for right in right_cluster:
            scores.append(_entity_similarity(left, right))

    if not scores:
        return False

    best_score = max(scores)

    # Cross-label merging is intentionally more conservative than same-label merging.
    return best_score >= 0.94


def _entity_similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    """
    Compute a similarity score between two entity mentions.
    """
    left_name = left["name"]
    right_name = right["name"]

    left_norm = _normalize_surface(left_name)
    right_norm = _normalize_surface(right_name)

    if left_norm == right_norm:
        return 1.0

    left_singular = _singularize_phrase(left_norm)
    right_singular = _singularize_phrase(right_norm)

    exact_singular = 1.0 if left_singular == right_singular else 0.0
    fuzzy_ratio = fuzz.token_sort_ratio(left_norm, right_norm) / 100.0
    singular_ratio = fuzz.token_sort_ratio(left_singular, right_singular) / 100.0
    token_overlap = _token_overlap(left_singular, right_singular)

    context_bonus = 0.03 if left.get("chunk_id") == right.get("chunk_id") else 0.0

    score = (
        0.40 * exact_singular
        + 0.25 * fuzzy_ratio
        + 0.25 * singular_ratio
        + 0.10 * token_overlap
        + context_bonus
    )

    if _looks_like_plural_variant(left_norm, right_norm):
        score += 0.05

    score += _person_name_variant_score(
        left_norm,
        right_norm,
        left.get("label"),
        right.get("label"),
    )

    return min(score, 1.0)


def _normalize_surface(text: str) -> str:
    """
    Normalize a surface form for similarity comparison.
    """
    value = str(text or "").strip().lower()
    value = re.sub(r"[^a-z0-9\s\-']", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"^(the|a|an)\s+", "", value)
    return value


def _singularize_phrase(text: str) -> str:
    """
    Singularize the final token of a phrase to reduce simple number variants.
    """
    words = text.split()
    if not words:
        return text

    if len(words) == 1:
        return _singularize_word(words[0])

    words[-1] = _singularize_word(words[-1])
    return " ".join(words)


def _singularize_word(word: str) -> str:
    """
    Singularize a single word when `inflect` recognizes it as plural.
    """
    singular = _inflect.singular_noun(word)
    return singular if singular else word


def _token_overlap(left: str, right: str) -> float:
    """
    Compute Jaccard-style token overlap between two normalized phrases.
    """
    left_tokens = set(left.split())
    right_tokens = set(right.split())

    if not left_tokens or not right_tokens:
        return 0.0

    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return intersection / union


def _looks_like_plural_variant(left: str, right: str) -> bool:
    """
    Detect simple plural/singular surface variation.
    """
    return (
        left == right + "s"
        or right == left + "s"
        or _singularize_phrase(left) == _singularize_phrase(right)
    )


def _choose_canonical_name(cluster: list[dict[str, Any]]) -> str:
    """
    Select the canonical display name for a resolved entity cluster.

    Person entities prefer fuller names, while non-person entities prefer the
    shortest stable surface form.
    """
    names = [entity["name"].strip() for entity in cluster if entity.get("name")]
    if not names:
        return ""

    label_counts = Counter(
        entity.get("label", "Concept")
        for entity in cluster
        if entity.get("label")
    )
    dominant_label = max(
        label_counts.keys(),
        key=lambda label: (label_counts[label], LABEL_PRIORITY.get(label, 0)),
        default="Concept",
    )

    if dominant_label == "Person":
        candidates = sorted(names, key=lambda name: (-len(name), name.lower()))
        return candidates[0]

    candidates = sorted(names, key=lambda name: (len(name), name.lower()))
    canonical = candidates[0]

    singular_candidate = _restore_case(
        _singularize_phrase(_normalize_surface(canonical)),
        canonical,
    )

    return singular_candidate or canonical


def _choose_canonical_label(cluster: list[dict[str, Any]]) -> str:
    """
    Choose the canonical label using observed counts and label priority.
    """
    counts = Counter(
        entity.get("label", "Concept")
        for entity in cluster
        if entity.get("label")
    )

    if not counts:
        return "Concept"

    return max(
        counts.keys(),
        key=lambda label: (counts[label], LABEL_PRIORITY.get(label, 0)),
    )


def _build_label_counts(cluster: list[dict[str, Any]]) -> dict[str, int]:
    """
    Build a complete label-count summary for a resolved cluster.
    """
    counts = {
        "Organization": 0,
        "Location": 0,
        "Person": 0,
        "Concept": 0,
    }

    observed = Counter(
        entity.get("label", "Concept")
        for entity in cluster
        if entity.get("label")
    )

    for label, count in observed.items():
        counts[label] = count

    return counts


def _restore_case(normalized_text: str, original_text: str) -> str:
    """
    Restore a normalized phrase to something closer to the original case style.
    """
    if not normalized_text:
        return original_text

    if original_text.isupper():
        return normalized_text.upper()

    if original_text[:1].isupper():
        return " ".join(word.capitalize() for word in normalized_text.split())

    return normalized_text


def _person_name_variant_score(
    left: str,
    right: str,
    left_label: str | None = None,
    right_label: str | None = None,
) -> float:
    """
    Add a small bonus for conservative person-name suffix matches.
    """
    if left_label != "Person" or right_label != "Person":
        return 0.0

    left_tokens = left.split()
    right_tokens = right.split()

    if not left_tokens or not right_tokens:
        return 0.0

    if len(left_tokens) == 1 and len(right_tokens) in {2, 3} and left_tokens[0] == right_tokens[-1]:
        return 0.12

    if len(right_tokens) == 1 and len(left_tokens) in {2, 3} and right_tokens[0] == left_tokens[-1]:
        return 0.12

    return 0.0
