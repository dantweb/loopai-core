import requests


def test_deepseek_api():
    # Replace with your actual API endpoint and key
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    API_KEY = "sk-15d75dc3b55148e7b98cdaf755b989bb"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    data = {
        "model": "deepseek-chat",  # Verify correct model name
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()  # Raises exception for 4xx/5xx errors

        print("API connection successful!")
        print("Response:", response.json())

        print(type(response))
        print(type(response.json()))
        exit
        # Extract and display the response content
        if 'choices' in response.json():
            reply = response.json()['choices'][0]['message']['content']
            print("\nAssistant reply:", reply)

        return True

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Connection Error: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Request Exception: {err}")

    return False


if __name__ == "__main__":
    test_deepseek_api()