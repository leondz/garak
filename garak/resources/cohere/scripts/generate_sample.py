import os
import cohere

# Retrieve the API key from an environment variable
api_key = os.getenv("COHERE_API_KEY")

# Check if the API key is available
if api_key is None:
    print("API key not found. Please set the COHERE_API_KEY environment variable. - https://docs.cohere.com/reference/checkapikey")
    exit()

# Initialize the Cohere client with the retrieved API key
co = cohere.Client(api_key)

# Specify the model and generate text
response = co.generate(
    model='command',  # Replace 'model_name' with the desired model
    prompt='Once upon a time',
    max_tokens=50
)

# Print the full payload response
print(response)
