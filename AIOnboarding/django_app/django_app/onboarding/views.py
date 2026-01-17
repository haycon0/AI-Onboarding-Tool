from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .gemini import gemini_prompt


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def members(request):
    template = loader.get_template('assistant.html')
    return HttpResponse(template.render())


@csrf_exempt
@require_http_methods(["POST"])
def receive_message(request):
    """
    API endpoint to receive prompts/messages.
    Processes the prompt and returns a "message received" confirmation.
    """
    try:
        print("[Django] Received a message request" + str(request.body), flush=True)
        data = json.loads(request.body)
        prompt = data.get('prompt') or data.get('message')
        
        if not prompt:
            return JsonResponse({
                'status': 'error',
                'message': 'No prompt provided'
            }, status=400)
        
        # Process the prompt using configured operations
        # Customize the operations list as needed
        gemini_response = gemini_prompt(prompt)
        
        # Log the original and processed prompt
        print(f"[Django] Received prompt: {prompt}", flush=True)
        print(f"[Django] Processed prompt: {gemini_response}", flush=True)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Message received',
            'original_prompt': prompt,
            'gemini_response': gemini_response
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        print(f"[Django] Error receiving message: {e}", flush=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)