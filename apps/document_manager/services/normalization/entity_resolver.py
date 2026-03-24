import re
from collections import Counter, defaultdict

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


def resolve_entities(entities):
    """
    Returns:
    - resolved_entities: entity list with canonical_name and canonical_label
    - canonical_map: maps raw (label, name) pairs to canonical entity info
    - label_summary: per canonical entity, counts of observed labels
    """
    grouped = defaultdict(list)

    for entity in entities:
        grouped[entity["label"]].append(entity)

    clusters = []
    for label, group in grouped.items():
        clusters.extend(_cluster_entities(group, label))

    merged_clusters = _merge_cross_label_clusters(clusters)

    canonical_map = {}
    resolved_entities = []
    label_summary = {}

    for cluster in merged_clusters:
        canonical_name = _choose_canonical_name(cluster)
        canonical_label = _choose_canonical_label(cluster)
        label_counts = _build_label_counts(cluster)

        label_summary[canonical_name] = label_counts

        for entity in cluster:
            key = (entity["label"], entity["name"])

            canonical_info = {
                "canonical_name": canonical_name,
                "canonical_label": canonical_label,
                "label_counts": label_counts,
            }
            canonical_map[key] = canonical_info

            enriched = dict(entity)
            enriched["canonical_name"] = canonical_name
            enriched["canonical_label"] = canonical_label
            enriched["label_counts"] = label_counts
            resolved_entities.append(enriched)

    return resolved_entities, canonical_map, label_summary


def apply_entity_resolution_to_relations(relations, canonical_map):
    resolved_relations = []

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


def _cluster_entities(entities, label):
    clusters = []

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


def _merge_cross_label_clusters(clusters):
    """
    Merge clusters across labels when the names are strong matches.
    This is what lets us reconcile:
    - Moonkeep as Person
    - Moonkeep as Organization
    """
    merged = []

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


def _should_merge(entity, cluster, label):
    threshold = LABEL_THRESHOLDS.get(label, 0.95)

    scores = [
        _entity_similarity(entity, other)
        for other in cluster
    ]

    return max(scores, default=0.0) >= threshold


def _should_merge_clusters(left_cluster, right_cluster):
    scores = []

    for left in left_cluster:
        for right in right_cluster:
            scores.append(_entity_similarity(left, right))

    if not scores:
        return False

    best_score = max(scores)

    # Be conservative when merging across labels.
    return best_score >= 0.94


def _entity_similarity(left, right):
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

    context_bonus = 0.0
    if left.get("chunk_id") == right.get("chunk_id"):
        context_bonus = 0.03

    score = (
        0.40 * exact_singular +
        0.25 * fuzzy_ratio +
        0.25 * singular_ratio +
        0.10 * token_overlap +
        context_bonus
    )

    if _looks_like_plural_variant(left_norm, right_norm):
        score += 0.05

    return min(score, 1.0)


def _normalize_surface(text):
    value = str(text or "").strip().lower()
    value = re.sub(r"[^a-z0-9\s\-']", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"^(the|a|an)\s+", "", value)
    return value


def _singularize_phrase(text):
    words = text.split()
    if not words:
        return text

    if len(words) == 1:
        return _singularize_word(words[0])

    words[-1] = _singularize_word(words[-1])
    return " ".join(words)


def _singularize_word(word):
    singular = _inflect.singular_noun(word)
    return singular if singular else word


def _token_overlap(left, right):
    left_tokens = set(left.split())
    right_tokens = set(right.split())

    if not left_tokens or not right_tokens:
        return 0.0

    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return intersection / union


def _looks_like_plural_variant(left, right):
    return (
        left == right + "s"
        or right == left + "s"
        or _singularize_phrase(left) == _singularize_phrase(right)
    )


def _choose_canonical_name(cluster):
    names = [entity["name"].strip() for entity in cluster if entity.get("name")]
    if not names:
        return ""

    candidates = sorted(names, key=lambda name: (len(name), name.lower()))
    canonical = candidates[0]

    singular_candidate = _restore_case(
        _singularize_phrase(_normalize_surface(canonical)),
        canonical,
    )

    return singular_candidate or canonical


def _choose_canonical_label(cluster):
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


def _build_label_counts(cluster):
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


def _restore_case(normalized_text, original_text):
    if not normalized_text:
        return original_text

    if original_text.isupper():
        return normalized_text.upper()

    if original_text[:1].isupper():
        return " ".join(word.capitalize() for word in normalized_text.split())

    return normalized_text


