
import sqlite3

from langchain_ollama import ChatOllama
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage
)


# --------------------------------------------------
# 1. OLLAMA CONFIGURATION
# --------------------------------------------------

llm = ChatOllama(
    model="qwen2.5:3b",
    base_url="http://host.docker.internal:11434",
    temperature=0
)


# --------------------------------------------------
# 2. DATABASE CONFIGURATION
# --------------------------------------------------

conn = sqlite3.connect("auto_memory.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        memory TEXT NOT NULL
    )
""")

conn.commit()


# --------------------------------------------------
# 3. AUTOMATIC MEMORY EXTRACTION
# --------------------------------------------------

def extract_memories(user_input):

    prompt = """
    You are a memory extraction assistant.

    Extract useful, long-term facts explicitly stated
    by the user.

    Allowed categories:
    profile, skill, preference, goal, project

    Rules:
    - Preserve the exact meaning.
    - Do not invent facts.
    - Do not extract ordinary questions.
    - Do not extract greetings.
    - Do not convert preferences into skills.
    - Do not convert skills into projects.
    - Never extract passwords or API keys.
    - Keep facts short and clear.

    Examples:

    User: I am a DevOps engineer.
    profile: User works as a DevOps engineer.

    User: My favorite DevOps tool is Terraform.
    preference: User's favorite DevOps tool is Terraform.

    User: I know AWS and Kubernetes.
    skill: User has knowledge of AWS and Kubernetes.

    User: I want to become a Platform Architect.
    goal: User wants to become a Platform Architect.

    If nothing is worth remembering, output:
    NONE

    Output only the facts.
    """

    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=user_input)
    ])

    return response.content.strip()


# --------------------------------------------------
# 4. SAVE MEMORIES
# --------------------------------------------------

def save_memories(extracted_text):

    if extracted_text.upper() == "NONE":
        print("No useful memories found.")
        return

    allowed_categories = {
        "profile",
        "skill",
        "preference",
        "goal",
        "project"
    }

    saved_count = 0

    for line in extracted_text.splitlines():

        if ":" not in line:
            continue

        category, memory = line.split(":", 1)

        category = category.strip().lower()
        memory = memory.strip()

        if category not in allowed_categories:
            continue

        if not memory:
            continue

        # Check whether this memory already exists
        cursor.execute("""
            SELECT id FROM memories
            WHERE LOWER(memory) = LOWER(?)
        """, (memory,))

        existing = cursor.fetchone()

        if existing:
            print(f"Already exists: {memory}")
            continue

        # Save new memory
        cursor.execute("""
            INSERT INTO memories (category, memory)
            VALUES (?, ?)
        """, (category, memory))

        saved_count += 1

    conn.commit()

    print(f"New memories saved: {saved_count}")


# --------------------------------------------------
# 5. LOAD MEMORIES
# --------------------------------------------------

def load_memories():

    cursor.execute("""
        SELECT category, memory
        FROM memories
        ORDER BY id
    """)

    return cursor.fetchall()


# --------------------------------------------------
# 6. DISPLAY MEMORIES
# --------------------------------------------------


def show_memories():

    cursor.execute("""
        SELECT id, category, memory
        FROM memories
        ORDER BY id
    """)

    memories = cursor.fetchall()

    print("\n========== SAVED MEMORIES ==========")

    if not memories:
        print("No memories found.")

    for memory_id, category, memory in memories:
        print(f"[{memory_id}] [{category}] {memory}")

    print("===================================\n")



# --------------------------------------------------
# 7. DELETE MEMORY
# --------------------------------------------------

def delete_memory(memory_id):

    cursor.execute("""
        DELETE FROM memories
        WHERE id = ?
    """, (memory_id,))

    conn.commit()

    if cursor.rowcount > 0:
        print("Memory deleted successfully.")
    else:
        print("Memory not found.")


# --------------------------------------------------
# 8. CONVERSATION HISTORY
# --------------------------------------------------

conversation_history = []


# --------------------------------------------------
# 9. START AI AGENT
# --------------------------------------------------

print("\n===================================")
print("       AI MEMORY AGENT")
print("===================================")

print("Commands:")
print("/memories       - Show saved memories")
print("/forget <id>    - Delete a memory")
print("/exit           - Exit agent")
print()


while True:

    user_input = input("You: ").strip()

# Handle accidentally repeated terminal prompt text
    if user_input.startswith("You: "):
        user_input = user_input[5:].strip()

    if not user_input:
        continue

    # Exit application
    if user_input == "/exit":
        break

    # Show saved memories
    if user_input == "/memories":
        show_memories()
        continue

    # Delete memory
    if user_input.startswith("/forget "):

        try:
            memory_id = int(user_input.split(" ", 1)[1])
            delete_memory(memory_id)

        except ValueError:
            print("Please provide a valid memory ID.")

        continue

    try:

        # ------------------------------------------
        # STEP A: EXTRACT MEMORIES
        # ------------------------------------------

        print("\n[1/3] Extracting memories...")

        extracted_text = extract_memories(user_input)

        print("Extraction result:")
        print(extracted_text)

        # ------------------------------------------
        # STEP B: SAVE MEMORIES
        # ------------------------------------------

        save_memories(extracted_text)

        # ------------------------------------------
        # STEP C: LOAD SAVED MEMORIES
        # ------------------------------------------

        memories = load_memories()

        memory_context = "\n".join(
            [
                f"{category}: {memory}"
                for category, memory in memories
            ]
        )

        # ------------------------------------------
        # STEP D: BUILD SYSTEM PROMPT
        # ------------------------------------------

        system_prompt = """
        You are a helpful AI assistant.

        Answer the user's questions clearly.

        Use saved user memories when relevant.

        Do not invent personal information.

        If the answer is not available in memory,
        clearly say that you do not know.
        """

        if memory_context:
            system_prompt += (
                "\n\nUSER'S SAVED MEMORIES:\n"
                + memory_context
            )

        # ------------------------------------------
        # STEP E: BUILD MESSAGE HISTORY
        # ------------------------------------------

        messages = [
            SystemMessage(content=system_prompt)
        ]

        messages.extend(conversation_history)

        messages.append(
            HumanMessage(content=user_input)
        )

        # ------------------------------------------
        # STEP F: GENERATE AI RESPONSE
        # ------------------------------------------

        print("\n[2/3] Generating response...")
        print("\nAgent: ", end="", flush=True)

        response_text = ""

        for chunk in llm.stream(messages):

            response_text += chunk.content

            print(
                chunk.content,
                end="",
                flush=True
            )

        print("\n")

        # ------------------------------------------
        # STEP G: UPDATE CONVERSATION HISTORY
        # ------------------------------------------

        conversation_history.append(
            HumanMessage(content=user_input)
        )

        conversation_history.append(
            AIMessage(content=response_text)
        )

        print("[3/3] Response completed.\n")

    except Exception as error:

        print("\nSomething went wrong:")
        print(error)
        print("\nPlease check your Ollama connection and try again.\n")


# --------------------------------------------------
# 10. CLOSE DATABASE
# --------------------------------------------------

conn.close()

print("\nAI Agent stopped.")
print("Memory database closed.")
