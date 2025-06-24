import boto3, json, os
from functools import lru_cache

MODEL_ID = os.getenv("BEDROCK_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0")

@lru_cache
def _client():
    return boto3.client("bedrock-runtime")

def gen_suggestion(transcript: str) -> dict:
    prompt = (
        "You are CallMate AI, an assistant that helps support agents.\n"
        "Customer just said:\n"
        f"{transcript}\n\n"
        "Reply in JSON with keys suggestion and sentiment."
    )
    resp = _client().invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"prompt": prompt, "max_tokens": 200}),
    )
    parsed = json.loads(resp["body"].read())
    # parsed should already hold suggestion + sentiment per our prompt design
    return parsed
