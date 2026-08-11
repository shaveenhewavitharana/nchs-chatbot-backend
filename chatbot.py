import os
import re
import json
import requests # Added to send data directly to the API
from openai import OpenAI
from dotenv import load_dotenv

# Locate and load the .env file for local testing 
# (Vercel will ignore this and use your Dashboard Environment Variables)
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(base_dir, "..", ".env")
    load_dotenv(dotenv_path=dotenv_path, override=True)
except Exception:
    pass

# Safely get the API key
api_key = os.environ.get("LLAMA_API_KEY")

# 1. Initialize the Llama Client
client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

# 2. Save function (UPDATED for Vercel: Direct API Delivery)
def save_contact_info(name: str, phone: str, email: str, branch: str, pathway: str, interest_score: int = 3) -> str:
    """Sends a user's details directly to the NCHS Campus API."""
    
    clean_phone = re.sub(r"\D", "", phone)
    if len(clean_phone) != 10:
        return "Error: The phone number must contain exactly 10 digits."

    # Prepare the payload exactly as the NCHS API expects it
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
        # Send instantly to the live NCHS database
        headers = {'Content-Type': 'application/json'}
        api_url = "https://api.nchs.edu.lk/api/website/lead"
        response = requests.post(api_url, json=student_data, headers=headers, timeout=10)
        
        if response.status_code == 200 and response.json().get("success"):
            return "Contact information processed and delivered to counselors successfully."
        else:
            return "Contact information processed, but API delivery failed."
            
    except Exception as e:
        return f"Error sending to API: {str(e)}"

# 3. Define the Tool and Instructions for Llama
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

chat_history = [
    {
        "role": "system",
        "content": f"""You are a friendly campus assistant for Nawaloka College of Higher Education (NCHS). Keep answers concise.
        Use this dataset: {nchs_dataset}

        WORKFLOW:
        1. Answer the user's questions regarding courses or general inquiries.
        2. Politely ask if they would like to speak with an NCHS counselor for further details.
        3. WAIT for the user to respond. DO NOT send the contact form template yet.
        4. IF the user agrees to be contacted, reply with a brief friendly acknowledgment and append this EXACT template to trigger the form:
           "Name: [Your Name], Email: [Your Email], Number: [Your Phone Number], Branch: [Branch], Pathway: [Pathway]"
        5. When the user provides their details, call the save_contact_info tool. 
           CRITICAL SCORING RULE: You must independently evaluate the user's interest level from 1 to 5 based on their chat history.
           - 1 or 2 = Low interest (casual browsing, short or vague questions).
           - 3 = Medium interest (asking about general course options).
           - 4 or 5 = High interest (asking specific questions about applying, tuition fees, deadlines, or entry requirements).
        6. Once successfully saved, thank them and inform them a representative will reach out."""
    }
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
    if not api_key:
        return "Error: LLAMA_API_KEY was not found."

    chat_history.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=chat_history,
            tools=tools,
            temperature=0.5
        )
        
        response_message = response.choices[0].message

        if response_message.tool_calls:
            chat_history.append(response_message)
            
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "save_contact_info":
                    args = json.loads(tool_call.function.arguments)
                    
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
                model="llama-3.3-70b-versatile",
                messages=chat_history
            )
            final_text = final_response.choices[0].message.content
            chat_history.append({"role": "assistant", "content": final_text})
            return final_text
            
        else:
            final_text = response_message.content
            chat_history.append({"role": "assistant", "content": final_text})
            return final_text

    except Exception as e:
        return f"API Error: {str(e)}"
