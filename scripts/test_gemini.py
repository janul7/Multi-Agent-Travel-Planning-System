from google import genai

client = genai.Client()
resp = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Say hello in three words."
)
print(resp.text)
