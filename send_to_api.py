import csv
import requests
import time
import os

# UPDATED: Pointing to the real NCHS Campus API
API_URL = "https://api.nchs.edu.lk/api/website/lead" 

def process_lead_queue():
    print("🤖 Automator started. Waiting for new leads to arrive...")
    
    while True:
        if os.path.exists("leads.csv"):
            print("\n📂 New leads detected! Processing queue...")
            
            try:
                with open("leads.csv", "r", encoding="utf-8") as file:
                    reader = csv.DictReader(file)
                    
                    for row in reader:
                        # UPDATED: Keys now perfectly match the NCHS database requirements
                        student_data = {
                            "name": row["Name"],
                            "email": row["Email"],
                            "mobile": row["Phone Number"],
                            "mobile2": "",
                            "mobile3": "",
                            "mobile4": "",
                            "branch": row["Branch"],
                            "pathway": row["Pathway"],
                            "mktmode": "WEB",
                            "submktmode": "Test",
                            "course": "Test",
                            "qualification": "Test",
                            "remarks": f"Interest Score: {row['Interest Score']}" # Appended score to remarks
                        }
                        
                        print(f"   -> Sending {row['Name']} to NCHS Database...")
                        
                        # Added a small timeout and headers for best practices
                        headers = {'Content-Type': 'application/json'}
                        response = requests.post(API_URL, json=student_data, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            # Parse the JSON response to print the exact Lead ID
                            response_data = response.json()
                            if response_data.get("success"):
                                print(f"      ✓ Delivered! Lead ID: {response_data.get('leadID')}")
                            else:
                                print(f"      X Server rejected. Message: {response_data.get('message')}")
                        else:
                            print(f"      X Failed. HTTP Code: {response_data.status_code}")
                
                os.remove("leads.csv")
                print("🧹 CSV file cleared. Queue is empty.")
                
            except Exception as e:
                print(f"Error processing file: {e}")
        
        time.sleep(60)

process_lead_queue()