import json
from google import genai
from google.genai import types
from .models import Client, Interaction, Department
from .api import api_key
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from django.db import connection
from django.conf import settings
from sqlalchemy import create_engine
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional

class Information(BaseModel):
    name: Optional[str] = Field(description="This should be filled if the prompt contains the users name. Please be certain it is the users name and not a random name mentioned in the prompt.")
    password: Optional[str] = Field(description="This should be filled if the prompt contains the users password. It should be clear in the chat that the user wants to provide this password.")
    email: Optional[str] = Field(description="This should be filled if the prompt contains the users email. Please be certain it is the users email and not a random email mentioned in the prompt.")
    department: Optional[str] = Field(description=
                                      f"""This should be filled if the user indicates they want to be connected to a department in the current interaction. Previous interactions should not be considered for filling this field.
                                      The possible deparments are Corporate Law, Litigation, Intellectual Property, Real Estate, Employment Law, Tax Law, Environmental Law, Healthcare Law, Family Law, Bankruptcy & Restructuring, International Law, Administrative Law, Energy Law, Construction Law, Financial Services. 
                                      If it is clear the user wants to interact with one of these departments, fill this field with the exact name of the department.""")
    
class ChangeDepartment(BaseModel):
    department: Optional[str] = Field(description=f"""This should be filled if the user wants to interact with a different department in the current interaction than the current department.
                                      The possible deparments are Corporate Law, Litigation, Intellectual Property, Real Estate, Employment Law, Tax Law, Environmental Law, Healthcare Law, Family Law, Bankruptcy & Restructuring, International Law, Administrative Law, Energy Law, Construction Law, Financial Services. 
                                      If it is clear the user wants to interact with one of these departments, fill this field with the exact name of the department.""")

def gemini_prompt(prompt, interaction_id=None):

    # get the interaction history for this client
    if interaction_id:
        # Get specific interaction by ID
        try:
            current_interaction = Interaction.objects.get(id=interaction_id)
        except Interaction.DoesNotExist:
            print(f"[Gemini] Interaction {interaction_id} not found, creating new one", flush=True)
            current_interaction = None
    else:
        # Get the first interaction for this client
        interactions = Interaction.objects.filter(client=client)
        current_interaction = interactions.first()
    
        # Get the client based on the extracted name if name is present else create a new client
    if not current_interaction.client or not current_interaction.department:
        vars = extract_variables_gemini(prompt)

        name = vars.get("name")
        password = vars.get("password")
        email = vars.get("email")
        department = vars.get("department")
        print(f"[Gemini] Extracted variables: name={name}, password={password}, email={email}, department={department}", flush=True)

    # Assign client if not already assigned
    if not current_interaction.client:
        if not name or not password or not email:
            return "Please clearly provide name, password, and email to proceed."
        client = Client.objects.filter(email=email).first() if name else None
        if client and password != client.password:
            return f"Incorrect password for client {name}."
        if not client:
            client = Client.objects.create(name=name, password=password, email=email)
            print(f"[Gemini] Created new client {client.name}", flush=True)
        else:
            # Please add all interactions to the prompt
            interactions = Interaction.objects.filter(client=client)
            temp = ""
            for interaction in interactions:
                temp += f"\nPrevious interaction this client had with {interaction.department.name if interaction.department else 'The system'} - {interaction.conversation}"
            if interactions:
                print(f"[Gemini] Previous interactions: {temp}", flush=True)
                summary_prompt = f"Please provide a concise summary of these previous interactions in paragraph form retaining relevant legal facts: {temp}"
                cli = genai.Client(api_key=api_key())
                response = cli.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=summary_prompt
                )
                print(f"[Gemini] Summary of previous interactions: {response.text}", flush=True)
                prompt = f"""{prompt} Summary of all previous interactions this client had with the system (This is not necessarily relevant for the current interaction): {response.text}"""

        current_interaction.client = client
        current_interaction.save()
        prompt = f"""{prompt} Note from the system: The client has been added to the system."""
        print(f"[Gemini] Assigned client {client.name} to interaction {current_interaction.id}", flush=True)
    else:
        if not current_interaction.department and not department:
            prompt = f"""{prompt} New instructions from the system: Please determine the appropriate department for this client based on their legal needs and confirm that this is the appropriate department."""

    # Assign department if not already assigned
    if not current_interaction.department and department:
        department_obj = Department.objects.filter(name=department).first()
        current_interaction.department = department_obj
        current_interaction.save()
        print(f"[Gemini] Assigned department {department_obj.name} to interaction {current_interaction.id}", flush=True)
        prompt = f"""New instructions from the system: {department_obj.prompt} Input from the user: {prompt}"""
    
    # Check if the department needs to be changed
    if current_interaction.department:
        print(f"[Gemini] Checking if current department for interaction is correct", flush=True)
        new_department = change_department(prompt, current_interaction.department.name)
        print(f"[Gemini] New department suggested: {new_department}", flush=True)
        if new_department and new_department != current_interaction.department.name:
            # Save the current interaction before changing the department
            Interaction.objects.create(conversation=current_interaction.conversation, department=current_interaction.department, client=current_interaction.client)
            current_interaction.department = Department.objects.filter(name=new_department).first()
            current_interaction.save()
            prompt = f"""New instructions from the system: {current_interaction.department.prompt} Input from the user: {prompt}"""
            print(f"[Gemini] Changed department to {new_department} for interaction {current_interaction.id}", flush=True)


    history = current_interaction.conversation if current_interaction else []
    client = genai.Client(api_key=api_key())
    chat = client.chats.create(
        model="gemini-2.0-flash",
        history=history,
    )
    response = chat.send_message(message=prompt)
    #print("Chat History:")
    #print(chat.get_history())
    # Save the history to the interaction
    if not current_interaction:
        current_interaction = Interaction.objects.create(client=client, conversation=serialize_chat_history(chat.get_history()))
    else:
        current_interaction.conversation = serialize_chat_history(chat.get_history())
        current_interaction.save()
    return response.text

def gemini_prompt_department(prompt):
    response_from_sql = gemini_sql_query(prompt)
    prompt = f"{prompt}\n\nResponse from SQL query: {response_from_sql}"
    client = genai.Client(api_key=api_key())
    chat = client.chats.create(
        model="gemini-2.0-flash",
        history=[],
    )
    response = chat.send_message(message=prompt)
    return response.text

def change_department(prompt, current_department: str):
    prompt = f"""
    Analyze the following text and determine if the user wants to change their department.
    Current department: {current_department}
    Text: {prompt}
    """
    client = genai.Client(api_key=api_key())
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": ChangeDepartment.model_json_schema(),
        },
    )
    print(f"[Gemini] Change department response: {response.text}", flush=True)
    return json.loads(response.text).get("department")

def extract_variables_gemini(prompt):
    prompt = f"""
    Analyze the following text and extract user details.
    If a detail is missing or not mentioned, set the value to null (None).
    
    Text: {prompt}
    """
    client = genai.Client(api_key=api_key())
    response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_json_schema": Information.model_json_schema(),
    },
    )
    
    # Gemini returns a JSON string, which we parse into a Dictionary
    return json.loads(response.text)
        
def gemini_sql_query(prompt):
    """
    Use Gemini with LangChain SQL agent to query the database.
    """
    try:
        # Initialize Gemini LLM
        # "gemini-2.0-flash" for fast responses with tool calling
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            google_api_key=api_key()
        )

        # Get Django database configuration
        db_config = settings.DATABASES['default']
        db_engine = db_config['ENGINE']
        
        # Build SQLAlchemy connection string based on database type
        if 'sqlite' in db_engine:
            # SQLite
            db_url = f"sqlite:///{db_config['NAME']}"
        elif 'postgresql' in db_engine:
            # PostgreSQL
            db_url = f"postgresql://{db_config['USER']}:{db_config['PASSWORD']}@{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
        elif 'mysql' in db_engine:
            # MySQL
            db_url = f"mysql+pymysql://{db_config['USER']}:{db_config['PASSWORD']}@{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
        else:
            raise ValueError(f"Unsupported database engine: {db_engine}")

        # Create SQLAlchemy engine and SQLDatabase
        engine = create_engine(db_url)
        db = SQLDatabase(engine=engine)

        # Create the SQL agent
        agent_executor = create_sql_agent(
            llm=llm,
            db=db,
            agent_type="openai-tools",  # This agent type works well with Gemini's tool calling
            verbose=True
        )

        # Execute the query
        response = agent_executor.invoke(
            {"input": prompt}
        )

        output = response.get("output", "No response")
        print(f"SQL Query Response: {output}", flush=True)
        return output

    except Exception as e:
        print(f"Error in gemini_sql_query: {e}", flush=True)
        return f"Error executing SQL query: {str(e)}"

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