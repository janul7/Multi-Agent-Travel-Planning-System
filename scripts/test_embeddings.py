from google import genai

client = genai.Client()
res = client.models.embed_content(
    model="gemini-embedding-001",
    contents="hello world",
)
print(len(res.embeddings[0].values))
