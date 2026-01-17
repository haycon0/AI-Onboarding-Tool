
import re
import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from .models import Client, Interaction

# Load environment variables from .env file
load_dotenv()


def gemini_prompt(prompt):

    client = Client.objects.first()
    # get the interaction history for this client
    interactions = Interaction.objects.filter(client=client)
    # get the first interaction
    first_interaction = interactions.first()
    history = first_interaction.conversation if first_interaction else []
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    chat = client.chats.create(
        model="gemini-2.0-flash",
        history=history,
    )
    response = chat.send_message(message="I have 2 dogs in my house.")
    print(response.text)
    response = chat.send_message(message="How many paws are in my house?")
    print(response.text)
    print("Full chat history:")
    print(chat.get_history())
    # Save the history to the interaction
    if not first_interaction:
        first_interaction = Interaction.objects.create(client=client, conversation=json.dumps(chat.get_history()))
    else:
        first_interaction.conversation = json.dumps(chat.get_history())
        first_interaction.save()
    return response.text