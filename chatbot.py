import os
import re
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

# 1. Locate and load the .env file for local testing 
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(base_dir, "..", ".env")
    load_dotenv(dotenv_path=dotenv_path, override=True)
except Exception:
    pass

# 2. Save function: Direct API Delivery
def save_contact_info(name: str, phone: str, email: str, branch: str, pathway: str, interest_score: int = 3) -> str:
    """Sends a user's details directly to the NCHS Campus API."""
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

# 3. Dynamic Instructions Base
nchs_dataset = """
NCHS CAMPUS DATASET:
- Federation University Programmes (3 Years, Full-Time, Intakes: Feb/June/Oct):
  * Bachelor of Business (Management or Marketing)
  * Bachelor of IT (Software Development, Business Information Systems)
- Swinburne University Pathways:
  * Fields: Business, IT, Engineering, Health Science
  * Foundation Year: Pathway to 1st year Bachelor
  * UniLink Diploma in Health Science: 8-month pathway to 2nd year Bachelor.
  * Health Science Specializations: Applied Statistics, Biomedical Science, Nutrition, Psychology, etc.
- Partnerships: California State University, Monterey Bay (USA) & Ulster University (UK).
"""

def get_system_prompt(is_submitted: bool) -> str:
    """Generates a dynamic system prompt based on whether details have been captured."""
    base_prompt = f"You are a friendly campus assistant for Nawaloka College of Higher Education (NCHS). Keep answers concise.\nUse this dataset: {nchs_dataset}\n\nWORKFLOW RULES:\n"
    
    if is_submitted:
        # RULES FOR WHEN DETAILS ARE ALREADY SUBMITTED
        return base_prompt + """1. The user has ALREADY provided their contact details.
2. Simply answer their questions directly, accurately, and concisely.
3. DO NOT ask if they want to speak to a counselor.
4. DO NOT output the contact form template under any circumstances."""
    else:
        # RULES FOR WHEN DETAILS ARE NOT YET SUBMITTED
        return base_prompt + """1. SIMPLE GREETINGS: IF the user just says "Hi", "Hello", etc., YOU MUST USE THIS EXACT PHRASE word-for-word:
"Hello! 👋 How can I help you today? If you’d like more details about our programmes or pathways, just let me know. Would you like to speak with a counselor for further assistance?"

2. COUNSELOR AGREEMENT: IF the user agrees to speak with a counselor (e.g., "yes", "okay", "sure"):
- Respond with: "Please provide your details so you can speak with a consultant and learn more about a specific program or the application process."
- Append this EXACT template to trigger the form:
  "Name: [Your Name], Email: [Your Email], Number: [Your Phone Number], Branch: [Branch], Pathway: [Pathway]"
  
3. SPECIFIC QUESTIONS: IF the user asks a specific question about the campus or courses (skipping the greeting):
- Answer their question FIRST.
- Then, IMMEDIATELY append this exact text block below your answer to trigger the form:
  "Please provide your details so you can speak with a consultant and learn more about a specific program or the application process.
  Name: [Your Name], Email: [Your Email], Number: [Your Phone Number], Branch: [Branch], Pathway: [Pathway]"
  
4. SCORING & SAVING: When the user provides their details, call the save_contact_info tool."""

chat_history = [
    {"role": "system", "content": get_system_prompt(is_submitted=False)}
]

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
                    "phone": {"type": "string", "description": "The Your phone number"},
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

# 4. Main Response Generator
def generate_response(user_message: str) -> str:
    # 1. Check if the form was already successfully submitted in previous turns
    form_submitted = any(
        (isinstance(msg, dict) and msg.get("role") == "tool" and msg.get("name") == "save_contact_info")
        for msg in chat_history
    )
    
    # 2. Dynamically update the system instructions based on submission state
    if chat_history and chat_history[0].get("role") == "system":
        chat_history[0]["content"] = get_system_prompt(form_submitted)

    # 3. Intercept simple greetings ONLY if form is not submitted yet
    if not form_submitted:
        clean_msg = re.sub(r'[^a-zA-Z\s]', '', user_message).strip().lower()
        if clean_msg in ["hi", "hello", "hey", "hi there", "hello there", "greetings"]:
            exact_reply = "Hello! 👋 How can I help you today? If you’d like more details about our programmes or pathways, just let me know. Would you like to speak with a counselor for further assistance?"
            chat_history.append({"role": "user", "content": user_message})
            chat_history.append({"role": "assistant", "content": exact_reply})
            return exact_reply

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
            temperature=0.5
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
            
            # Immediately update the system prompt BEFORE it generates its confirmation response
            if chat_history and chat_history[0].get("role") == "system":
                chat_history[0]["content"] = get_system_prompt(True)
            
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
                 
            # 4. PYTHON-LEVEL FAILSAFE: Physically strip out the template if the AI ignores the new system prompt
            form_submitted_check = any((isinstance(msg, dict) and msg.get("role") == "tool" and msg.get("name") == "save_contact_info") for msg in chat_history)
            if form_submitted_check and "Name: [" in final_text:
                if "Please provide your details" in final_text:
                    final_text = final_text.split("Please provide your details")[0].strip()
                else:
                    final_text = final_text.split("Name: [")[0].strip()
                 
            chat_history.append({"role": "assistant", "content": final_text})
            return final_text

    except Exception as e:
        return f"API Error: {str(e)}"
