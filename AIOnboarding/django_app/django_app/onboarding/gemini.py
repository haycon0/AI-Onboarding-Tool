import json
from google import genai
from google.genai import types
from .models import Client, Interaction
from .api import api_key

def gemini_prompt(prompt):

    client = Client.objects.first()
    # get the interaction history for this client
    interactions = Interaction.objects.filter(client=client)
    # get the first interaction
    first_interaction = interactions.first()
    history = first_interaction.conversation if first_interaction else []
    print(api_key(), flush=True)
    client = genai.Client(api_key=api_key())
    chat = client.chats.create(
        model="gemini-2.0-flash",
        history=history,
    )
    response = chat.send_message(message=prompt)
    print(chat.get_history())
    # Save the history to the interaction
    if not first_interaction:
        first_interaction = Interaction.objects.create(client=client, conversation=serialize_chat_history(chat.get_history()))
    else:
        first_interaction.conversation = serialize_chat_history(chat.get_history())
        first_interaction.save()
    return response.text

def serialize_chat_history(chat_history):
    serialized_data = []
    
    for message in chat_history:
        # Extract role (user or model)
        role = getattr(message, 'role', 'user') # Default to user if role is missing
        
        # specific handling for 'UserContent' vs 'Content' objects if needed, 
        # though usually they share the same structure regarding 'parts'
        
        parts_data = []
        if hasattr(message, 'parts'):
            for part in message.parts:
                # Check if it is text (standard) or other data (images/function calls)
                if hasattr(part, 'text'):
                    parts_data.append({"text": part.text})
                # Add handling for inline_data (images) here if necessary
        
        serialized_data.append({
            "role": role,
            "parts": parts_data
        })
        
    return serialized_data