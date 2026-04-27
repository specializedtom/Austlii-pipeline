from __future__ import annotations


def status_accuracy(gold: list[dict], pred: list[dict]) -> float:
    if not gold:
        return 0.0
    pred_by_id = {row["source_id"]: row.get("status") for row in pred}
    correct = sum(1 for row in gold if pred_by_id.get(row["source_id"]) == row.get("status"))
    return correct / len(gold)
