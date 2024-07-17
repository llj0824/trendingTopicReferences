import requests
from openai import OpenAI
from config import LLM_CREDENTIALS


# Define a class to encapsulate API interactions
ANTHROPIC_API_KEY = LLM_CREDENTIALS["ANTHROPIC_API_KEY"]
OPENAI_API_KEY = LLM_CREDENTIALS["OPENAI_API_KEY"]
class LLM_API_Utils:
    def __init__(self, anthropic_api_key=ANTHROPIC_API_KEY, openai_api_key=OPENAI_API_KEY):
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_key = openai_api_key
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)

    def call_claude(self, system_role, prompt, model="claude-3-5-sonnet-20240620",  max_tokens=4000, temperature=0.5):
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        data = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_role,
            "messages": [{"role": "user", "content": prompt}]
        }

        # This is example of maintaing previous
        # data = {
        #     "model": model,
        #     "max_tokens": max_tokens,
        #     "temperature": temperature,
        #     "messages": [
        #         {"role": "system", "content": system_role},
        #         {"role": "user", "content": "Hello, AI"},
        #         {"role": "assistant", "content": "Hello! How can I assist you today?"},
        #         {"role": "user", "content": prompt}
        #     ]
        # }

        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        return response.json()

    def call_gpt4(self, prompt,model="gpt-4o", system_role="",max_tokens=4000, temperature=0.5):
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[{
                "role": "system",
                "content": system_role
            }, {
                "role": "user",
                "content": prompt
            }],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()

    def call_claudeOrGpt4_llm(self, model_name, system_role, prompt, max_tokens=4000, temperature=0.5):
        print(f"Api call to LLM: \n{prompt}\n")
        try:
            if model_name.startswith("claude"):
                response = self.call_claude(model=model_name, system_role=system_role, prompt=prompt, max_tokens=max_tokens, temperature=temperature)
                # Assuming the breakpoint was for debugging; remember to remove or comment it out in production code.
                output = response['content'][0]['text'].strip()  # Adjust based on Claude's actual response structure
            else:
                output = self.call_gpt4(model=model_name, system_role=system_role, prompt=prompt, max_tokens=max_tokens, temperature=temperature)
        except Exception as e:
            print(f"An error occurred: {e}")
            # Attempt to print the full response if it's available and can be parsed
            try:
                print("Full API response:", response)
            except NameError:
                print("Error occurred before a response was received.")
            output = "An error occurred while processing your request."
        print(f"api response: \n{output}\n")
        return output

# Example usage:
# llm_api_utils = LLM_API_Utils(anthropic_api_key='your_anthropic_api_key', openai_api_key='your_openai_api_key')
# claude_response = llm_api_utils.call_claude(model='claude-3-opus-20240229', prompt='Your prompt here')
# gpt4_response = llm_api_utils.call_gpt4(model='gpt-4-turbo-preview', prompt='Your prompt here')