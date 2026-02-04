import openai

# Your OpenAI API key
openai.api_key = "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"

def chat_with_gpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-3.5-turbo" if needed
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

if _name_ == "_main_":
    prompt = input("Enter your prompt: ")
    answer = chat_with_gpt(prompt)
    print("\nChatGPT Response:\n")
    print(answer)