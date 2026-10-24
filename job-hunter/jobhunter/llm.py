"""Shared Claude client setup: resume context and the call wrapper."""

import base64
from pathlib import Path

import anthropic

_client = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def resume_block(cfg: dict) -> dict:
    """The resume as a content block, marked for prompt caching so it is billed once per run."""
    resume = cfg.get("resume", {})
    text_path = resume.get("text")
    if text_path and Path(text_path).exists():
        return {
            "type": "text",
            "text": f"<resume>\n{Path(text_path).read_text()}\n</resume>",
            "cache_control": {"type": "ephemeral"},
        }
    pdf_path = resume.get("pdf")
    if pdf_path and Path(pdf_path).exists():
        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": base64.standard_b64encode(Path(pdf_path).read_bytes()).decode(),
            },
            "title": "Candidate resume",
            "cache_control": {"type": "ephemeral"},
        }
    raise SystemExit("No resume found. Set resume.pdf (and optionally resume.text) in config.yaml.")


def parse(cfg: dict, system: str, content: list, schema, max_tokens: int = 4000):
    """Structured-output call. Returns a validated `schema` instance, or None if Claude declined."""
    scoring = cfg.get("scoring", {})
    response = client().beta.messages.parse(
        model=scoring.get("model", "claude-opus-5-5"),
        max_tokens=max_tokens,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": scoring.get("effort", "low")},
        system=system,
        messages=[{"role": "user", "content": content}],
        output_format=schema,
    )
    if response.stop_reason == "refusal":
        return None
    return response.parsed_output
