
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage


# 1. Connect to Ollama
llm = ChatOllama(
    model="qwen2.5:3b",
    base_url="http://host.docker.internal:11434"
)


# 2. Create conversation history
messages = [
    SystemMessage(
        content="You are a helpful AI assistant. "
                "Remember the conversation history."
                "you can answer in 2-3 sentences."
    )
]


# 3. Start conversation
print("AI Assistant Started!")
print("Type 'exit' to stop.\n")


while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        print("Goodbye!")
        break

    # Add user message
    messages.append(
        HumanMessage(content=user_input)
    )

    # Send conversation to LLM
    response = llm.invoke(messages)

    # Save AI response
    messages.append(response)

    # Display response
    print("\nAgent:", response.content)
    print()
