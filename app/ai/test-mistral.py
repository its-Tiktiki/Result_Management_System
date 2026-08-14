"""
Quick test script for calling the Mistral API.

NOTE ON IMPORTS:
The line you gave — `from mistralai.client import Mistral` — is from the
OLD (pre-1.0) mistralai SDK, which used `mistralai.client.MistralClient`.
That class no longer exists in the current SDK (2.x).

Current SDK (installed here: mistralai 2.9.2) uses:
    from mistralai import Mistral

If you specifically need the old API shape for some reason, pin an old
version instead: pip install "mistralai<1.0"

Usage:
    export MISTRAL_API_KEY="your-key-here"
    python test_mistral.py
"""

import os
from mistralai.client import Mistral

def main():
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set the MISTRAL_API_KEY environment variable before running this script."
        )

    model = "mistral-small-latest"  # or "mistral-small-latest", "open-mistral-7b", etc.

    client = Mistral(api_key=api_key)

    response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Explain Quantum Computing to a 3 years old baby.",
            },
        ],
    )

    print("Response from Mistral:")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()