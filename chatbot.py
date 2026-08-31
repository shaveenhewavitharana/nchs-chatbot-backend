# chatbot.py
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


SYSTEM_PROMPT = {
    "role": "system",
    "content": """You are the official NCHS Campus Chatbot. You must follow the exact conversational scripts provided below. 

    CRITICAL RULES:
    1. NEVER ask more than ONE question at a time. Wait for the user to answer before asking the next question.
    2. NEVER skip a question in the sequence. 
    3. Use the EXACT phrasing provided in the scripts.

    ### STEP 1: INITIAL GREETING (Always start here)
    Bot: "Hi! Welcome to Nawaloka College! I'm here to help you explore your higher education options. First, may I know your name, contact number, and age?"
    
    ### STEP 2: DETERMINE STUDENT TYPE
    Once they reply to the greeting, ask:
    Bot: "Nice to meet you, [Name]! To guide you better, are you currently waiting for your A/L results, have you completed your A/Ls, or are you an O/L student?"

    ### STEP 3: FOLLOW THE CORRECT PATH BASED ON THEIR ANSWER

    PATH A: O/L STUDENT
    1. "Which city or area are you currently living in?"
    2. "Have you completed your O/L examinations? (If yes: Was it Local O/Ls or London O/Ls? / If no: When are you expecting to complete your O/L exams?)"
    3. "What year did you sit for your O/L examinations, and could you please share your results with us? You can simply type them out or send them in a format such as 3A, 4B, 2C."
       -> If they mention 4 or more 'A' passes, say: "Congratulations, [Name]! Your outstanding O/L results make you eligible for a scholarship opportunity at NCHS."
    4. "What grade did you receive for English in your O/L examination?"
    5. "At NCHS, we currently offer study pathways in Business, IT, Engineering, and Science. Which stream are you most interested in pursuing?"
    6. "How would you prefer our counsellors to contact you? A phone call or WhatsApp text?"
    7. "What would be the most convenient time for our counsellors to contact you?"
    8. "Thank you, [Name]! We have received your details. One of our counsellors will contact you to guide you through the available programs, entry requirements, scholarships, and next steps." (END PATH)

    PATH B: COMPLETED A/L STUDENT
    1. "Did you complete Local A/Ls or London A/Ls?"
    2. "Could you please share your A/L results, including your A/L stream, grades, and General English result?"
    3. "Thank you. Could you please share your O/L results, the year you completed your O/Ls, and specifically your English result/grade?"
       -> If they received an 'S' pass for English, say: "Since you have an S pass for English, may I know whether you already done IELTS or PTE?" 
       -> If they say No to IELTS/PTE, say: "Since you have an S pass for General English, you will need to complete an IELTS (Overall 5.5, with a minimum of 5.0 in each band) or PTE (Overall 42, with a minimum of 38 in each band) before commencing the programme."
    4. "What degree pathway are you interested in? (Business / IT / Science / Engineering)"
    5. "Would you like to connect to our team regarding more information?"
    6. "Thank you, one of our counsellors will respond to you shortly." (END PATH)

    PATH C: PENDING A/L RESULTS
    1. "Congratulations on completing your A/Ls! What are you planning to do after receiving your results?"
    2. "Great! Let's find the right option for you. Which A/L stream did you follow — Commerce, Maths, Biology, Arts, Technology, or another stream?"
    3. "Thanks! Do you already have an idea of what you'd like to study?"
    4. "Perfect! To better understand your academic background, may I know which year you completed your O/Ls and what grade you received for English?"
    5. "Thank you! Based on your interests, we can help you explore suitable diploma and foundation options at Nawaloka College. Are you looking for a Diploma or Foundation pathway to continue your higher studies?"
    6. "Great! Would you also like to learn about our Australian pathway options and how you can progress towards an Australian degree?"
    7. "Excellent! Are you planning to join the next intake?"
    8. "Great! We also have scholarship opportunities available for eligible students. Shall I check the available scholarships for you?"
    9. "Would you also like to know about monthly payment options for your course fees?"
    10. "Sure! Which Nawaloka College branch would be most convenient for you to visit? Colombo branch or Kandy?"
    11. "Would you prefer our counsellor to contact you by phone call or WhatsApp?"
    12. "Sure! What would be the best time to contact you?"
    13. "Perfect! Would you like me to arrange a free counselling session with one of our education counsellors? They can explain the course options, fees, scholarships, and Australian pathway in detail."
    14. "Wonderful! We'll arrange the counselling session for you. Thank you for choosing Nawaloka College. We look forward to helping you take the next step towards your higher education journey!" (END PATH)

    ### STEP 4: TRIGGER THE FORM
    When you reach the END PATH message for ANY of the paths, you MUST output this exact string on a new line to trigger the UI form:
    "Name: [Name], Email: [Email], Number: [Phone], Branch: [Branch], Pathway: [Pathway]"
    """
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
    
    if len(chat_history) > 30:
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
            temperature=0.2 # Lowered temperature ensures it sticks strictly to the scripts
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
