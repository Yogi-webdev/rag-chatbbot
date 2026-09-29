from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()


def get_embedding(text):

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )

    return result.embeddings[0].values