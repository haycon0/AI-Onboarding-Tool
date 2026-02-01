from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Client, Interaction, Department
import json
from .gemini import gemini_prompt, gemini_prompt_department, create_interactions


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def clients(request):
    template = loader.get_template('assistant.html')
    return HttpResponse(template.render())

def departments(request):
    template = loader.get_template('departments.html')
    return HttpResponse(template.render())


def interactions_list(request):
    interactions = Interaction.objects.select_related('client', 'department').all()
    context = {
        "interactions": interactions,
    }
    return render(request, "interactions_list.html", context)


def _flatten_conversation(conversation):
    messages = []
    if not isinstance(conversation, list):
        return messages
    for entry in conversation:
        role = entry.get("role", "user") if isinstance(entry, dict) else "user"
        parts = entry.get("parts", []) if isinstance(entry, dict) else []
        texts = []
        for part in parts:
            text = part.get("text") if isinstance(part, dict) else None
            if text:
                texts.append(text)
        if texts:
            messages.append({
                "role": role,
                "text": "\n".join(texts),
            })
    return messages


def interaction_detail(request, interaction_id):
    interaction = get_object_or_404(
        Interaction.objects.select_related('client', 'department'),
        id=interaction_id,
    )
    context = {
        "interaction": interaction,
        "messages": _flatten_conversation(interaction.conversation),
    }
    return render(request, "interaction_detail.html", context)


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
        interaction_id = data.get('interaction_id')

        print(f"[Django] Interaction ID from chainlit: {interaction_id}", flush=True)
            # If the interaction_id is null then create a new interaction
        if not interaction_id:
            current_interaction = Interaction.objects.create(conversation=[])
            print(f"[Django] Created new interaction with ID {current_interaction.id}", flush=True)
        else:
            try:
                current_interaction = Interaction.objects.get(id=interaction_id)
            except Interaction.DoesNotExist:
                print(f"[Gemini] Interaction {interaction_id} not found, creating new one", flush=True)
                current_interaction = Interaction.objects.create(conversation=[])
        interaction_id = current_interaction.id
        if not prompt:
            return JsonResponse({
                'status': 'error',
                'message': 'No prompt provided'
            }, status=400)
        
        # Process the prompt using configured operations
        # Pass interaction_id to gemini_prompt
        gemini_response = gemini_prompt(prompt, interaction_id=interaction_id)
        
        # Log the original and processed prompt
        print(f"[Django] Received prompt: {prompt}", flush=True)
        print(f"[Django] Processed prompt: {gemini_response}", flush=True)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Message received',
            'original_prompt': prompt,
            'gemini_response': gemini_response,
            'interaction_id': interaction_id
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

@csrf_exempt
@require_http_methods(["POST"])   
def receive_message_department(request):
    """
    API endpoint to receive prompts/messages for the attorney/department.
    Processes the prompt and returns a "message received" confirmation.
    """
    print("[Django] Processing a message request for department", flush=True)
    try:
        print("[Django] Received a message request for department" + str(request.body), flush=True)
        data = json.loads(request.body)
        prompt = data.get('prompt') or data.get('message')
        
        if not prompt:
            return JsonResponse({
                'status': 'error',
                'message': 'No prompt provided'
            }, status=400)
        
        # Process the prompt using configured operations
        # Pass interaction_id to gemini_prompt
        gemini_response = gemini_prompt_department(prompt)
        
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
        print(f"[Django] Error receiving message for department: {e}", flush=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def create_interactions_endpoint(request):
    return JsonResponse({
            'status': 'error',
            'message': 'Creating interactions is currently disabled'
        }, status=500)
    """
    API endpoint to create a dummy interaction for testing.
    """
    try:
        for _ in range(10):
            create_interactions()
        return interactions_list(request)
    except Exception as e:
        print(f"[Django] Error creating interaction: {e}", flush=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)