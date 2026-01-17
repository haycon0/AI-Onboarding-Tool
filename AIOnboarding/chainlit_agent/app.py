import chainlit as cl
import asyncio
import sys
import httpx


@cl.on_chat_start
async def on_chat_start():
    """
    Initialize chat session when page loads.
    """
    print("[D] Chat session started", flush=True)


@cl.on_message
async def main(message: cl.Message):
    """
    Main handler for all messages.
    Send to Django and display Django's response.
    """
    print(f"[D] Received message: {message.content}", flush=True)
    
    # Send message to Django API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://django:8000/api/message/",
                json={"message": message.content},
                timeout=5.0
            )
            print(f"[D] Django response status: {response.status_code}", flush=True)
            
            response_data = response.json()
            print (response_data, flush=True)
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
