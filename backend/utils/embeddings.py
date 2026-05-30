"""
Hosted embedding helper.

The backend runs on a 512 MB instance, which is too small to load a local
PyTorch / sentence-transformers model. Instead we call the HuggingFace
Inference API for the SAME model (all-MiniLM-L6-v2), so embeddings stay
384-dimensional and remain compatible with the existing MongoDB vectors.

Requires the env var HF_TOKEN (a free token from
https://huggingface.co/settings/tokens).
"""
import os
import time
import requests

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
HF_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_MODEL}"

# Keep batches small so request bodies stay well within API limits.
_BATCH_SIZE = 32
_TIMEOUT = 120


def _headers():
    headers = {"Content-Type": "application/json"}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"
    return headers


def _embed_batch(batch, max_retries=4):
    """Embed a list of strings, retrying while the model warms up (503)."""
    payload = {"inputs": batch, "options": {"wait_for_model": True}}
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(HF_URL, headers=_headers(), json=payload, timeout=_TIMEOUT)
            # 503 = model is loading on HF's side; wait and retry.
            if resp.status_code == 503:
                time.sleep(5 * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:  # noqa: BLE001 - surface a clean error to caller
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"HuggingFace embedding request failed: {last_err}")


def embed_texts(texts):
    """
    Return embeddings for `texts`.

    - If `texts` is a single string, returns a single vector (list[float]).
    - If `texts` is a list of strings, returns a list of vectors.
    """
    single = isinstance(texts, str)
    inputs = [texts] if single else list(texts)

    if not inputs:
        return [] if not single else []

    vectors = []
    for i in range(0, len(inputs), _BATCH_SIZE):
        vectors.extend(_embed_batch(inputs[i:i + _BATCH_SIZE]))

    return vectors[0] if single else vectors
