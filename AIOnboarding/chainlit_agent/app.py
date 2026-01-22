import chainlit as cl
import asyncio
import sys
import httpx
from urllib.parse import urlparse, parse_qs
import os


# Global variable to store user type based on environment or default
USER_TYPE_DEFAULT = os.getenv("CHAINLIT_USER_TYPE", "Client")


@cl.on_chat_start
async def on_chat_start():
    """
    Initialize chat session when page loads.
    """
    print("[D] Chat session started", flush=True)
    
    # Check for user_type in environment variable (can be set by Docker/config)
    user_type = os.getenv("CHAINLIT_USER_TYPE", "Client")
    print(f"[D] User type from environment: {user_type}", flush=True)
    
    cl.user_session.set("user_type", user_type)
    
    # Store interaction_id in session (default to None, will be set by user/API)
    cl.user_session.set("interaction_id", None)
    
    # Start the session with appropriate message
    if user_type == "Attorney":
        await cl.Message(content="Hello Attorney! How can I assist you today?").send()
    else:
        await cl.Message(content="Hello! Please enter your email, password, and details of your legal issue. If you haven't used this AI onboarding tool before please provide your name as well, doing this will create a new account for you.").send()


@cl.on_message
async def main(message: cl.Message):
    """
    Main handler for all messages.
    Send to Django and display Django's response.
    """
    print(f"[D] Received message: {message.content}", flush=True)
    
    # Get interaction_id from session (if available)
    interaction_id = cl.user_session.get("interaction_id")
    user_type = cl.user_session.get("user_type")
    print(f"[D] User type from session: {user_type}", flush=True)
    print(f"[D] Interaction ID from session: {interaction_id}", flush=True)
    # Send message to Django API
    try:
        async with httpx.AsyncClient() as client:
            payload = {"message": message.content}
            if interaction_id:
                payload["interaction_id"] = interaction_id
            
            print(f"[D] Payload sent to Django: {payload}", flush=True)
            
            if user_type == "Client":
                response = await client.post(
                    "http://django:8000/api/message/",
                    json=payload,
                    timeout=60.0
                )
            elif user_type == "Attorney":
                response = await client.post(
                    "http://django:8000/api/attorney_message/",
                    json=payload,
                    timeout=60.0
                )
            else:
                print(f"[D] Unknown user type: {user_type}", flush=True)
            print(f"[D] Django response status: {response.status_code}", flush=True)
            
            response_data = response.json()
            print (response_data, flush=True)
            if(response_data.get('interaction_id')):
                cl.user_session.set("interaction_id", response_data['interaction_id'])
            django_response = response_data.get('response') or response_data.get('gemini_response') or "No response from Django."
            print(f"[D] Django said: {django_response}", flush=True)
    except Exception as e:
        print(f"[D] Error sending to Django: {e}", flush=True)
        django_response = f"Error: {str(e)}"
    
    # Send Django's response to user
    print("[D] Sending Django response to user...", flush=True)
    response_msg = cl.Message(content=django_response)
    await response_msg.send()
    print("[D] Response sent", flush=True)
