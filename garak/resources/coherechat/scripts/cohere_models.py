import os
import cohere

# Retrieve the API key from an environment variable
api_key = os.getenv("COHERE_API_KEY")

# Check if the API key is available
if api_key is None:
    print("API key not found. Please set the COHERE_API_KEY environment variable.")
    exit()

# Initialize the Cohere client with the retrieved API key
co = cohere.Client(api_key)

# Initialize an empty list to hold all models
all_models = []

# Initialize the next token variable
next_token = None

while True:
    # Fetch a page of models using the next token
    if next_token:
        response = co.models.list(next=next_token)
    else:
        response = co.models.list()

    # Add the current page of models to the list
    all_models.extend(response.models)

    # Check if there is a next token
    if not hasattr(response, 'next'):
        break

    # Move to the next token
    next_token = response.next

# Print all models
for model in all_models:
    print(model)
