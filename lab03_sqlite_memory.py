
import sqlite3

from langchain_ollama import ChatOllama
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage
)


# 1. Connect to Ollama
llm = ChatOllama(
    model="qwen2.5:3b",
    base_url="http://host.docker.internal:11434"
)


# 2. Connect to SQLite database
conn = sqlite3.connect("conversation.db")
cursor = conn.cursor()


# 3. Create messages table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        content TEXT NOT NULL
    )
""")

conn.commit()


# 4. Load previous conversation
messages = [
    SystemMessage(
        content="You are a helpful assistant. "
                "Use the conversation history to answer questions."
                "You can answer in 1 sentence."
    )
]

cursor.execute(
    "SELECT role, content FROM messages ORDER BY id"
)

for role, content in cursor.fetchall():

    if role == "user":
        messages.append(HumanMessage(content=content))

    elif role == "assistant":
        messages.append(AIMessage(content=content))


# 5. Start conversation
print("AI Assistant Started!")
print("Type 'exit' to stop.\n")


while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    # Save user message
    cursor.execute(
        "INSERT INTO messages (role, content) VALUES (?, ?)",
        ("user", user_input)
    )
    conn.commit()

    messages.append(HumanMessage(content=user_input))

    # Get AI response
    response = llm.invoke(messages)

    # Save AI response
    cursor.execute(
        "INSERT INTO messages (role, content) VALUES (?, ?)",
        ("assistant", response.content)
    )
    conn.commit()

    messages.append(response)

    print("\nAgent:", response.content)
    print()


# 6. Close database connection
conn.close()

print("Conversation saved successfully!")
