from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Client, Interaction, Department
import json
from .gemini import gemini_prompt, gemini_prompt_department


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def clients(request):
    template = loader.get_template('assistant.html')
    return HttpResponse(template.render())

def departments(request):
    template = loader.get_template('departments.html')
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
        interaction_id = data.get('interaction_id')

        print(f"[Django] Interaction ID from chainlit: {interaction_id}", flush=True)
        
        # If the interaction_id is null then create a new interaction
        if not interaction_id:
            new_interaction = Interaction.objects.create(conversation=[])
            print(f"[Django] Created new interaction with ID {new_interaction.id}", flush=True)
            interaction_id = new_interaction.id
            original_prompt = prompt
            departments = ", ".join([dept.name for dept in Department.objects.all()])
            prompt = f"""
            This text is from the system to initialize a new interaction:
            This interaction is to onboard a client to a law firm. 
            The first step is to gather basic information about the client and their legal needs. 
            This begins with determining if they have used this AI onboarding tool before and if they are already in our system.
            To do this we need their name and password. Please request this if they have not provided it or it is unclear.
            We also need to determine what department can assist them with their legal needs.
            If they do not know which department can assist them, please ask clarifying questions about their legal needs to determine the appropriate department.
            Once you feel an appropriate amount of information has been gathered, thank the client, confirm their details, inform them that their information has been recorded, and end the interaction.
            The available departments are: {departments}.
            This text is the initial message from the client: {original_prompt}"""
        

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
            'gemini_response': gemini_response,
            'interaction_id': interaction_id
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