
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


# STEP 1: Connect to Ollama
llm = ChatOllama(
    model="qwen2.5:3b",
    base_url="http://host.docker.internal:11434"
)


# STEP 2: Initialize conversation state
messages = [
    SystemMessage(
        content="You are a helpful AI assistant. "
                "Remember the conversation history "
                "provided to you."
    )
]


# STEP 3: Start conversation
print("AI Assistant started!")
print("Type 'exit' to stop.\n")


while True:

    # Get user input
    user_input = input("You: ")

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    # Add user message to history
    messages.append(
        HumanMessage(content=user_input)
    )

    # Send conversation history to LLM
    response = llm.invoke(messages)

    # Save AI response to history
    messages.append(
        AIMessage(content=response.content)
    )

    # Display response
    print("\nAgent:", response.content)
    print()
