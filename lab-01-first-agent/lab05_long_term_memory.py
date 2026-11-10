
import sqlite3

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# 1. Connect to Ollama
llm = ChatOllama(
    model="qwen2.5:3b",
    base_url="http://host.docker.internal:11434"
)

# 2. Connect to memory database
conn = sqlite3.connect("long_term_memory.db")
cursor = conn.cursor()

# 3. Create memory table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        memory TEXT NOT NULL
    )
""")

conn.commit()


# 4. Save a memory
def save_memory(memory):

    cursor.execute(
        """
        INSERT INTO memories (category, memory)
        VALUES (?, ?)
        """,
        ("general", memory)
    )

    conn.commit()

    print("Memory saved successfully!")


# 5. Load saved memories
def load_memories():

    cursor.execute(
        "SELECT id, category, memory FROM memories ORDER BY id"
    )

    return cursor.fetchall()


# 6. Delete a memory
def delete_memory(memory_id):

    cursor.execute(
        "DELETE FROM memories WHERE id = ?",
        (memory_id,)
    )

    conn.commit()

    if cursor.rowcount > 0:
        print("Memory deleted.")
    else:
        print("Memory not found.")


# 7. Start agent
print("\nLong-Term Memory Agent Started!")
print("Commands:")
print("/remember <fact>")
print("/memories")
print("/forget <id>")
print("/exit\n")


while True:

    user_input = input("You: ").strip()

    if not user_input:
        continue

    # Exit
    if user_input == "/exit":
        break

    # Save memory
    if user_input.startswith("/remember "):

        memory = user_input.replace("/remember ", "", 1).strip()

        if memory:
            save_memory(memory)

        continue

    # Display memories
    if user_input == "/memories":

        memories = load_memories()

        print("\nSaved Memories:")

        for memory_id, category, memory in memories:
            print(f"{memory_id}. [{category}] {memory}")

        print()
        continue

    # Delete memory
    if user_input.startswith("/forget "):

        try:
            memory_id = int(user_input.split(" ", 1)[1])
            delete_memory(memory_id)

        except ValueError:
            print("Please provide a valid memory ID.")

        continue

    # Load long-term memories
    memories = load_memories()

    memory_context = "\n".join(
        [memory[2] for memory in memories]
    )

    # Build system instructions
    system_prompt = """
    You are a helpful AI assistant.

    Use the user's saved memories when they are relevant.
    Do not invent personal information.
    If a fact is not available, say you do not know.
    you can answer in 1-2 sentences.
    """

    if memory_context:
        system_prompt += (
            "\n\nUser's saved memories:\n" + memory_context
        )

    # Build messages for this interaction
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]

    # Get response
    response = llm.invoke(messages)

    print("\nAgent:", response.content)
    print()


conn.close()

print("Memory database closed.")
