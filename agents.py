"""Small staged workflow using the OpenAI Responses API."""

import json
import os
from pathlib import Path

import requests


RESPONSES_URL = "https://api.openai.com/v1/responses"
MODEL = "gpt-5.6-terra"
MOCK_MODE = os.environ.get("BEDROCK_MOCK") == "1"
MOCKS_DIR = Path(__file__).with_name("mocks")


def call_model(system_prompt, user_content, stage_id=None):
    """Return a stage response, loading a local JSON fixture in mock mode."""
    if MOCK_MODE:
        if not stage_id:
            raise ValueError("stage_id is required when BEDROCK_MOCK=1")
        ticker = os.environ.get("BEDROCK_TICKER", "AAPL").upper()
        mock_path = MOCKS_DIR / ticker / f"{stage_id}.json"
        if not mock_path.exists():
            mock_path = MOCKS_DIR / f"{stage_id}.json"
        try:
            mock_response = json.loads(mock_path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"No mock response for stage '{stage_id}': {mock_path}"
            ) from error
        return json.dumps(mock_response, indent=2)

    api_key = os.environ["OPENAI_API_KEY"]
    response = requests.post(
        RESPONSES_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "instructions": system_prompt,
            "input": user_content,
        },
    )
    response.raise_for_status()
    result = response.json()
    return "".join(
        content["text"]
        for item in result.get("output", [])
        if item.get("type") == "message"
        for content in item.get("content", [])
        if content.get("type") == "output_text"
    )


if __name__ == "__main__":
    classifier_response = call_model(
        "Classify the company into the analysis workflow types. Return JSON only.",
        "Company: Apple Inc. (AAPL)",
        stage_id="classifier",
    )
    classification = json.loads(classifier_response)
    print("Classifier:")
    print(classifier_response)

    stage_2_response = call_model(
        "Produce the Type B Stage 2 business-quality analysis. Return JSON only.",
        json.dumps({"company": "Apple Inc.", "classification": classification}),
        stage_id="stage_2",
    )
    print("\nStage 2:")
    print(stage_2_response)
