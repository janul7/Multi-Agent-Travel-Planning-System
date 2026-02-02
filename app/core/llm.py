from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

def get_chat_model():
    # Reads GEMINI_API_KEY / GOOGLE_API_KEY from environment
    return ChatGoogleGenerativeAI(model="gemini-3-flash-preview", temperature=0.2)

def get_embedder():
    return GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
