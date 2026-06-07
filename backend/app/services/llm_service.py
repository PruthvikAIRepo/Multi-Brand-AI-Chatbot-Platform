"""Provider-agnostic LLM service. Supports OpenAI and Anthropic (Claude).
Switch via LLM_PROVIDER in .env — no code changes needed."""

from app.config import get_settings

settings = get_settings()


async def generate_response(
    system_prompt: str,
    messages: list[dict],
    max_tokens: int = 1000,
) -> dict:
    """Generate an AI response. Returns {content, tokens_in, tokens_out, model}."""
    if settings.LLM_PROVIDER == "openai":
        return await _openai_generate(system_prompt, messages, max_tokens)
    elif settings.LLM_PROVIDER == "anthropic":
        return await _anthropic_generate(system_prompt, messages, max_tokens)
    else:
        raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")


async def _openai_generate(system_prompt: str, messages: list[dict], max_tokens: int) -> dict:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=api_messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )

    return {
        "content": response.choices[0].message.content,
        "tokens_in": response.usage.prompt_tokens,
        "tokens_out": response.usage.completion_tokens,
        "model": settings.LLM_MODEL,
    }


async def _anthropic_generate(system_prompt: str, messages: list[dict], max_tokens: int) -> dict:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    api_messages = []
    for msg in messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    response = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        system=system_prompt,
        messages=api_messages,
        max_tokens=max_tokens,
    )

    return {
        "content": response.content[0].text,
        "tokens_in": response.usage.input_tokens,
        "tokens_out": response.usage.output_tokens,
        "model": settings.CLAUDE_MODEL,
    }
