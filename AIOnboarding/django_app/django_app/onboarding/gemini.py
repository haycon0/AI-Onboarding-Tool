
import re
from google import genai
from google.genai import types
from .models import Client, Interaction

def get_user_and_interaction(client_id=None, interaction_id=None):
    """
    Get a user (Client) and try to find an interaction.
    
    Args:
        client_id: The ID of the client to retrieve
        interaction_id: The ID of the interaction to retrieve (optional)
    
    Returns:
        A tuple of (client, interaction) or (client, None) if no interaction found
    """
    try:
        # Get the client
        if client_id is None:
            # If no client_id provided, get the first client
            client = Client.objects.first()
            if not client:
                print("No clients found in the database")
                return None, None
        else:
            client = Client.objects.get(id=client_id)
        
        print(f"Found client: {client.name} (ID: {client.id})")
        
        # Try to find an interaction
        if interaction_id is not None:
            # Get specific interaction by ID
            interaction = Interaction.objects.get(id=interaction_id, client=client)
            print(f"Found interaction: {interaction.title} (ID: {interaction.id})")
        else:
            # Get the first interaction for this client
            interaction = client.interactions.first()
            if interaction:
                print(f"Found interaction: {interaction.title} (ID: {interaction.id})")
            else:
                print(f"No interactions found for client: {client.name}")
                interaction = None
        
        return client, interaction
    
    except Client.DoesNotExist:
        print(f"Client with ID {client_id} not found")
        return None, None
    except Interaction.DoesNotExist:
        print(f"Interaction with ID {interaction_id} not found for this client")
        return client, None

def gemini_prompt(prompt):

    client = genai.Client(api_key="AIzaSyD_TZWn6Dl70AGqZ-Lrx8T_8BpwBVTbRI0")

    chat = client.chats.create(
        model="gemini-2.0-flash",
        history=[
            types.Content(role="user", parts=[types.Part(text="Hello")]),
            types.Content(
                role="model",
                parts=[
                    types.Part(
                        text="Great to meet you. What would you like to know?"
                    )
                ],
            ),
        ],
    )
    response = chat.send_message(message="I have 2 dogs in my house.")
    print(response.text)
    response = chat.send_message(message="How many paws are in my house?")
    print(response.text)
    print(chat.get_history())
    return response.text