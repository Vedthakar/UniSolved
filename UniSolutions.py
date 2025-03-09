import openai

openai.api_key = "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"
def chat_with_gpt(prompt):
    response = openai.ChatCompletion.create(model = "gpt-4o", 
                                            messages = [{"role":"user", "content":prompt}])
    

if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "fuck off"]:
            break
        response = chat_with_gpt(user_input)
        print("Unisolved: ", response)