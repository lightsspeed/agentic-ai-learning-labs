
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# Connect to Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    temperature=0
)

# Ask a question
response = llm.invoke(
    "Explain what an AI agent is with one DevOps example."
)

# Print response
print(response.content)

