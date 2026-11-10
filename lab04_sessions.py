
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

# 2. Connect to SQLite
conn = sqlite3.connect("sessions.db")
cursor = conn.cursor()

# 3. Create messages table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL
    )
""")

conn.commit()

# 4. Ask for a session ID
session_id = input("Enter session ID: ").strip()

if not session_id:
    print("Session ID cannot be empty.")
    conn.close()
    raise SystemExit

# 5. Load messages for this session only
messages = [
    SystemMessage(
        content="You are a helpful assistant. "
                "Use the conversation history to answer."
                "You can answer in 1 sentence."
    )
]

cursor.execute(
    """
    SELECT role, content
    FROM messages
    WHERE session_id = ?
    ORDER BY id
    """,
    (session_id,)
)

for role, content in cursor.fetchall():

    if role == "user":
        messages.append(HumanMessage(content=content))

    elif role == "assistant":
        messages.append(AIMessage(content=content))


print(f"\nAI Assistant Started!")
print(f"Session: {session_id}")
print("Type 'exit' to stop.\n")

# 6. Start conversation
while True:

    user_input = input("You: ").strip()

    if user_input.lower() == "exit":
        break

    if not user_input:
        continue

    # Save user message
    cursor.execute(
        """
        INSERT INTO messages (session_id, role, content)
        VALUES (?, ?, ?)
        """,
        (session_id, "user", user_input)
    )

    conn.commit()

    messages.append(HumanMessage(content=user_input))

    # Get AI response
    response = llm.invoke(messages)

    # Save AI response
    cursor.execute(
        """
        INSERT INTO messages (session_id, role, content)
        VALUES (?, ?, ?)
        """,
        (session_id, "assistant", response.content)
    )

    conn.commit()

    messages.append(response)

    print("\nAgent:", response.content)
    print()

conn.close()

print("Conversation saved successfully!")
