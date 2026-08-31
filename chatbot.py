import os

import re

import json

import requests

from openai import OpenAI

from dotenv import load_dotenv



try:

    base_dir = os.path.dirname(os.path.abspath(__file__))

    dotenv_path = os.path.join(base_dir, "..", ".env")

    load_dotenv(dotenv_path=dotenv_path, override=True)

except Exception:

    pass



def save_contact_info(name: str, phone: str, email: str, branch: str, pathway: str, interest_score: int = 3) -> str:

    clean_phone = re.sub(r"\D", "", phone)

    if len(clean_phone) != 10:

        return "Error: The phone number must contain exactly 10 digits."



    student_data = {

        "name": name,

        "email": email,

        "mobile": clean_phone,

        "mobile2": "",

        "mobile3": "",

        "mobile4": "",

        "branch": branch,

        "pathway": pathway,

        "mktmode": "WEB",

        "submktmode": "Chatbot",

        "course": "General Inquiry",

        "qualification": "N/A",

        "remarks": f"Interest Score: {interest_score}" 

    }



    try:

        headers = {'Content-Type': 'application/json'}

        api_url = "https://api.nchs.edu.lk/api/website/lead"

        response = requests.post(api_url, json=student_data, headers=headers, timeout=10)

        

        if response.status_code == 200 and response.json().get("success"):

            return "Contact information processed and delivered to counselors successfully."

        else:

            return "Contact information processed, but API delivery failed."

            

    except Exception as e:

        return f"Error sending to API: {str(e)}"



# The newly trained System Prompt based on your document workflows

SYSTEM_PROMPT = {

    "role": "system",

    "content": """You are a friendly campus assistant for Nawaloka College of Higher Education (NCHS). 

    Your goal is to guide students and collect their information naturally.



    CRITICAL RULES:

    - ASK ONE QUESTION AT A TIME. Wait for the user to answer before moving to the next step. Do not bombard them.

    - NEVER assume the user's name.

    - Treat every new conversation as a completely new student.



    CONVERSATIONAL FLOW:

    Step 1: Greet and politely ask for their Name, Age, and Contact Number.

    Step 2: Ask about their education status: Have they completed O/Ls, completed A/Ls, or are they waiting for A/L results?

    

    Step 3 (Branching based on Step 2):

      * IF COMPLETED A/L: 

        - Ask if it was Local or London, their stream, and their results (including General English).

        - Condition: If they got an 'S' pass or below for General English, inform them they need IELTS (Overall 5.5) or PTE (Overall 42) before commencing.

        - Ask which degree pathway they want (Business, IT, Science, Engineering).

      * IF O/L STUDENT: 

        - Ask for their exam year and results. 

        - Condition: If they have 4 or more 'A' passes, congratulate them on being eligible for an NCHS scholarship!

        - Ask for their English grade and preferred stream.

      * IF PENDING A/L: 

        - Ask for their A/L stream and O/L English result. 

        - Briefly explain that you offer Diploma/Foundation options and Australian pathways.

        

    Step 4: Ask which NCHS branch is easiest to visit (Colombo or Kandy).

    Step 5: Ask for their Email address to finalize their profile.

    Step 6: Ask if they would like to arrange a free counseling session (via Call or WhatsApp) and what time is convenient.

    

    Step 7 (Final Trigger): 

    If they agree to be contacted, politely acknowledge it and output this EXACT string to trigger the system form (do not alter this format):

    "Name: [Their Name], Email: [Their Email], Number: [Their Phone Number], Branch: [Branch], Pathway: [Pathway]"

    

    Once the form triggers and the save_contact_info tool is called, thank them and inform them a counselor will reach out at their preferred time."""

}



chat_history = [SYSTEM_PROMPT]



tools = [

    {

        "type": "function",

        "function": {

            "name": "save_contact_info",

            "description": "Saves a user's name, email, phone number, branch, pathway, and an evaluated interest score.",

            "parameters": {

                "type": "object",

                "properties": {

                    "name": {"type": "string", "description": "The user's name"},

                    "email": {"type": "string", "description": "The user's email address"},

                    "phone": {"type": "string", "description": "The user's phone number"},

                    "branch": {"type": "string", "description": "The chosen branch (CMB or KND)"},

                    "pathway": {"type": "string", "description": "The chosen pathway (SUT or USA or UK or FED or CAN)"},

                    "interest_score": {

                        "type": "string", 

                        "description": "An AI-evaluated score (e.g., '1', '3', '5') indicating how likely the user is to enroll."

                    }

                },

                "required": ["name", "email", "phone", "branch", "pathway", "interest_score"]

            }

        }

    }

]



def generate_response(user_message: str) -> str:

    global chat_history

    

    if len(chat_history) > 20:

        chat_history = [SYSTEM_PROMPT]



    api_key = os.environ.get("LLAMA_API_KEY") or os.environ.get("OPENAI_API_KEY")

    if not api_key:

        return "Error: LLAMA_API_KEY was not found in your environment variables."



    client = OpenAI(

        api_key=api_key,

        base_url="https://api.groq.com/openai/v1"

    )



    chat_history.append({"role": "user", "content": user_message})



    try:

        response = client.chat.completions.create(

            model="openai/gpt-oss-120b",

            messages=chat_history,

            tools=tools,

            temperature=0.4

        )

        

        response_message = response.choices[0].message



        if response_message.tool_calls:

            chat_history.append(response_message)

            submitted_name = ""

            

            for tool_call in response_message.tool_calls:

                if tool_call.function.name == "save_contact_info":

                    args = json.loads(tool_call.function.arguments)

                    submitted_name = args.get("name", "").strip()

                    

                    raw_score = str(args.get("interest_score", "3"))

                    match = re.search(r'\d', raw_score)

                    final_score = int(match.group()) if match else 3



                    function_result = save_contact_info(

                        name=args.get("name"), 

                        phone=args.get("phone"),

                        email=args.get("email", "N/A"),

                        branch=args.get("branch", "N/A"),

                        pathway=args.get("pathway", "N/A"),

                        interest_score=final_score

                    )

                    

                    chat_history.append({

                        "role": "tool",

                        "tool_call_id": tool_call.id,

                        "name": "save_contact_info",

                        "content": function_result

                    })

            

            final_response = client.chat.completions.create(

               model="openai/gpt-oss-120b",

               messages=chat_history,

               tools=tools 

            )

            final_text = final_response.choices[0].message.content

            

            if not final_text:

                if submitted_name:

                    first_name = submitted_name.split()[0]

                    final_text = f"Thank you, {first_name}! Your details have been successfully saved, and a counselor will reach out to you shortly."

                else:

                    final_text = "Thank you! Your details have been successfully saved, and a counselor will reach out to you shortly."

                

            chat_history.append({"role": "assistant", "content": final_text})

            return final_text

            

        else:

            final_text = response_message.content

            if not final_text:

                 final_text = "I'm sorry, I couldn't process that. Could you please rephrase?"

                 

            chat_history.append({"role": "assistant", "content": final_text})

            return final_text



    except Exception as e:

        return f"API Error: {str(e)}"
