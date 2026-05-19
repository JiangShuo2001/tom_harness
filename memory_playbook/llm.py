"""Slim LLM call wrapper. Only depends on ``openai`` and stdlib."""
import time
import random

import openai


def timed_llm_call(client, api_provider, model, prompt, *,
                   max_tokens=1024, use_json_mode=False,
                   temperature=0.0, max_retries=5, base_sleep=5.0):
    """Call an OpenAI-compatible chat completion endpoint with retries.

    Returns ``(response_text, call_info)`` where *call_info* carries
    lightweight metadata (no prompt/response bodies).
    """
    if api_provider == "openai":
        tokens_key = "max_completion_tokens"
    else:
        tokens_key = "max_tokens"

    api_params = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        tokens_key: max_tokens,
    }
    if use_json_mode:
        api_params["response_format"] = {"type": "json_object"}

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            t0 = time.time()
            response = client.chat.completions.create(**api_params)
            call_time = time.time() - t0

            content = response.choices[0].message.content if response.choices else None
            if not content:
                raise RuntimeError("Empty response from API")

            call_info = {
                "model": model,
                "prompt_length": len(prompt),
                "response_length": len(content),
                "prompt_num_tokens": getattr(response.usage, "prompt_tokens", 0),
                "response_num_tokens": getattr(response.usage, "completion_tokens", 0),
                "call_time": call_time,
            }
            return content, call_info

        except (openai.RateLimitError, openai.APITimeoutError,
                openai.APIConnectionError, openai.InternalServerError,
                RuntimeError) as exc:
            last_exc = exc
            if attempt < max_retries:
                sleep = base_sleep * (2 ** (attempt - 1)) + random.uniform(0, 1)
                time.sleep(sleep)

    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_exc}")
