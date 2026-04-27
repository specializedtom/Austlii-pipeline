from __future__ import annotations


def resolution_accuracy(gold: list[dict], pred: list[dict]) -> float:
    if not gold:
        return 0.0
    pred_by_id = {row["input_id"]: set(row.get("matched_source_ids", [])) for row in pred}
    correct = 0
    for row in gold:
        expected = set(row.get("matched_source_ids", []))
        if pred_by_id.get(row["input_id"], set()) == expected:
            correct += 1
    return correct / len(gold)
