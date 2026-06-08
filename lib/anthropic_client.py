import os
from anthropic import Anthropic

# Model tiers
BRAIN          = "claude-opus-4-7"             # planning, judgment, advisor calls
EXECUTOR_LIGHT = "claude-haiku-4-5-20251001"   # masking, dummy data (mechanical)
EXECUTOR_HEAVY = "claude-sonnet-4-6"           # requirements, wireframe (complex generation)

_client = None


def get_client() -> Anthropic:
    global _client
    if _client is None:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        _client = Anthropic(api_key=key)
    return _client


def call_with_tool(
    system: str,
    user_message: str,
    tool_name: str,
    tool_schema: dict,
    model: str,
    max_tokens: int = 4096,
) -> dict:
    """Force the model to call a specific tool; returns tool input dict."""
    client = get_client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        tools=[{
            "name": tool_name,
            "description": "Submit structured output for this stage.",
            "input_schema": tool_schema,
        }],
        tool_choice={"type": "tool", "name": tool_name},
        messages=[{"role": "user", "content": user_message}],
    )
    block = next(
        (b for b in response.content if b.type == "tool_use" and b.name == tool_name),
        None,
    )
    if not block:
        raise RuntimeError(f"Model did not call tool '{tool_name}'")
    return block.input


def consult_advisor(context: str, question: str) -> str:
    """
    Two-model advisor pattern: sends context + question to Opus, returns guidance.

    This mirrors the advisor tool contract (section 2 of the plan) without requiring
    beta access. When the advisor tool is confirmed, replace this body with an
    advisor_tool call using header 'advisor-tool-2026-03-01'.

    Call timing (from the plan):
      - Before substantive work (not for orientation/file-reading)
      - When stuck (contract failing, approach not converging)
      - After output is written, to confirm the stage looks complete
    """
    max_tokens = int(os.environ.get("ADVISOR_MAX_TOKENS", "2048"))
    client = get_client()
    response = client.messages.create(
        model=BRAIN,
        max_tokens=max_tokens,
        system=(
            "You are a strategic advisor for a Power BI automation pipeline. "
            "Read the context and answer the question. "
            "Keep guidance under 120 words. Be direct. No preamble."
        ),
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        }],
    )
    return response.content[0].text
