"""Run Bedrock's classifier and applicable filing-analysis stages."""

import json
from pathlib import Path

from agents import call_model
from stage_inputs import build_stage_inputs


PROMPTS_DIR = Path(__file__).with_name("prompts")
STAGES_DIR = Path(__file__).with_name("stages")


def _parse_yaml_value(value):
    """Parse the small YAML value subset used in stage frontmatter."""
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return [item.strip() for item in value[1:-1].split(",") if item.strip()]
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _parse_stage_file(path):
    """Return frontmatter fields and prompt text from one stage Markdown file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Stage file has no YAML frontmatter: {path}")

    _, frontmatter, prompt = text.split("---\n", 2)
    metadata = {}
    for line in frontmatter.splitlines():
        key, value = line.split(":", 1)
        metadata[key] = _parse_yaml_value(value)
    metadata["prompt"] = prompt.lstrip("\n")
    metadata["path"] = path
    return metadata


def load_stages():
    """Load every stage definition, sorted numerically by its frontmatter id."""
    stages = [_parse_stage_file(path) for path in STAGES_DIR.glob("*.md")]
    return sorted(stages, key=lambda stage: float(stage["id"]))


def _metric_fields(metrics):
    """Return field names that are present AND non-None."""
    return {key for key, value in metrics.items() if value is not None}


def _stage_mock_id(stage_id):
    """Map a numeric stage id to its fixture filename stem."""
    return f"stage_{str(stage_id).replace('.', '_')}"


def run_audit(ticker):
    """Classify *ticker*, run supported stages, and record unavailable stages."""
    metrics = build_stage_inputs(ticker)
    classifier_prompt = (PROMPTS_DIR / "classifier.md").read_text(encoding="utf-8")
    classification = json.loads(
        call_model(
            classifier_prompt,
            json.dumps({"ticker": ticker.upper(), "metrics": metrics}),
            stage_id="classifier",
        )
    )

    sector_type = classification["sector_type"]
    available_fields = _metric_fields(metrics)
    stage_results = []
    stages_missing = []
    for stage in load_stages():
        if sector_type not in stage["applies_to"]:
            stages_missing.append(
                {
                    "id": stage["id"],
                    "name": stage["name"],
                    "reason": f"not applicable to sector type {sector_type}",
                }
            )
            continue

        missing_requires = [
            field for field in stage["requires"] if field not in available_fields
        ]
        if missing_requires:
            stages_missing.append(
                {
                    "id": stage["id"],
                    "name": stage["name"],
                    "reason": "missing required metrics",
                    "missing_requires": missing_requires,
                }
            )
            continue

        stage_result = json.loads(
            call_model(
                stage["prompt"],
                json.dumps({"ticker": ticker.upper(), "metrics": metrics}),
                stage_id=_stage_mock_id(stage["id"]),
            )
        )
        stage_results.append(
            {
                "id": stage["id"],
                "name": stage["name"],
                "disqualifying": sector_type in stage["disqualifying_for"],
                "result": stage_result,
            }
        )

    return {
        "ticker": ticker.upper(),
        "classification": classification,
        "stage_results": stage_results,
        "stages_missing": stages_missing,
    }


if __name__ == "__main__":
    print(json.dumps(run_audit("AAPL"), indent=2))
