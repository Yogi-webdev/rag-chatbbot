import os
import time
from google import genai
from dotenv import load_dotenv
import requests

load_dotenv()

client = genai.Client()
GEMINI_MODEL_NAMES = [
    model.strip()
    for model in os.getenv("GEMINI_MODEL", "gemini-2.0-flash").split(",")
    if model.strip()
]

if not GEMINI_MODEL_NAMES:
    GEMINI_MODEL_NAMES = ["gemini-2.0-flash"]

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def _call_groq(prompt):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing")

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 700
        },
        timeout=60
    )

    if response.status_code != 200:
        raise RuntimeError(f"Groq error: {response.status_code}: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"]


def generate_answer(question, context, conversation_history):
    if not context:
        return "I couldn't find relevant information in the uploaded files."

    history_text = ""

    for item in conversation_history:

        history_text += f"""
Previous user question:
{item["question"]}

Previous assistant answer:
{item["answer"]}
"""

    prompt = f"""
You are a document-based question answering chatbot.

IMPORTANT RULES:

1. Answer the user's question using ONLY information
   contained in the uploaded file context. When the context contains
   excerpts from multiple files, reference and synthesize information
   from all relevant files.

2. You may use previous conversation only to understand
   what the user is referring to.

3. Do NOT use outside knowledge.

4. Do NOT invent facts.

5. If the uploaded file context does not contain enough
   information to answer the question, say exactly:

"I couldn't find that information in the uploaded files."

6. Keep the answer clear, well-structured, and concise.

Previous conversation:
{history_text}

Uploaded file context:
{context}

Current user question:
{question}
"""

    for attempt in range(4):

        for model_name in GEMINI_MODEL_NAMES:
            try:

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

                return response.text

            except Exception as e:

                error = str(e)

                if "429" in error or "RESOURCE_EXHAUSTED" in error or "quota" in error.lower():
                    print(f"Gemini model {model_name} hit quota. Trying Groq fallback...")
                    try:
                        return _call_groq(prompt)
                    except Exception as groq_error:
                        print(f"Groq fallback failed: {groq_error}")
                        continue

                if "503" in error or "UNAVAILABLE" in error:
                    wait_time = 2 ** attempt
                    print(
                        f"\nGemini is temporarily busy on {model_name}. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                    break

                return f"Error generating answer: {e}"

        if attempt < 3:
            time.sleep(1)

    try:
        return _call_groq(prompt)
    except Exception as groq_error:
        return (
            "Gemini API quota has been exceeded and Groq fallback is unavailable. "
            "Add a GROQ_API_KEY and set GROQ_MODEL in .env, or wait for the Gemini quota to reset."
        )