#Importing necessary Libraries
import pandas as pd
import numpy as np
import pdfplumber
import re
from pathlib import Path
from pdf2image import convert_from_path
import logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import ollama
import json



#Function that lets me extract info from invoices to a text. That text is then processed with an LLM, via ollama, to get the info needed. The info is then stored to a matrix that is then appended to the excel file 

def info_ex(file_path):

    #Setting up a starting value for my answer
    ollama_food = ""

    #Opens the file as a pdf
    with pdfplumber.open(file_path) as pdf:

        #Loop that iterates through each page and decides if the page is an image or not 
        for i , page in enumerate(pdf.pages): 

            #extracts the text from the pdf as if it was an extractable pdf
            text = page.extract_text() or ""

            # Filtering the text to keep only Greek and English letters using a regular expression
            letters_only = re.sub(r'[^a-zA-Zα-ωΑ-ΩάέήίόύώΆΈΉΊΌΎΏϊϋΪΫ]', '', text)

            #If statement that checks if invoice is a pdf or a scanned image
            if text and len(letters_only) > 15:

                #Adds to the answers what the program read from this page
                ollama_food += text + "\n\n"

            #The pdf is an image so I have to use another method to scan info
            else:

                
                # Store PDF as image with convert_from_path function
                images = convert_from_path( file_path , 300 , first_page = i + 1 , last_page= i + 1 , poppler_path=r"C:\Program Files\poppler-26.09.0\Library\bin")

                #Reading image info
                page_text = pytesseract.image_to_string(images[0] , lang="ell")

                #Adding each pages content to my final result
                ollama_food += page_text + "\n\n"

    return(ollama_food)




#Defining a function that gets the text of the page as a txt file and returns the Invoice Number , Vendors Name , Date that the invoice was published, a brief description, the total amount, the VAT Amount and a confidence score that
#represents how confident the model is about the extracted information. This information is returned as a string with the json format.
def finalresult(ollama_food) : 

    #Defining the model that I will be using 
    model = 'llama3.1:8b'

    #Defining the prompt that will be given to the LLM
    prompt = """You are a precise data extraction assistant. Your task is to extract invoice details from the provided OCR text and output ONLY a valid JSON object. Do not include any markdown formatting, code blocks, or conversational text.

                RULES:
                1. Extract the specific fields listed below.
                2. STRICT RULE: You are FORBIDDEN from performing any mathematical calculations. If a value (like VAT_Amount) is not explicitly printed in the text as a standalone number, you MUST output "N/A". Never calculate it yourself.
                3. The 'Confidence_Score' must be an integer between 0 and 100 representing your certainty that the extracted data matches the true invoice values.
                4. Do NOT output any thinking process, reasoning, or explanations. Go directly to generating the JSON object.
                5. For the 'Description' field, provide a very brief summary (2 to 5 words maximum) of what the invoice is for, based on the items or services listed. If it is completely unclear, output "N/A".

                EXPECTED JSON FORMAT:
                {{
                    "Invoice_Number": "...",
                    "Vendor_Name": "...",
                    "Date": "...",
                    "Description" : "..."
                    "Total_Amount": "...",
                    "VAT_Amount": "...",
                    "Confidence_Score": ...
                }}

                OCR TEXT TO PROCESS:""" + "\n\n" + ollama_food

    #Function that sends the prompt tο the ollama model
    response = ollama.chat(
        model = model  ,

        messages = [
            {'role' : 'user' , 'content' : prompt}
            ] ,

        #Defining the format of the output
        format = 'json' , 

        options = {
            #Definning how creative the LLM is.
            #The value of the temperature is 0.0 because we want the LLM to be as objective as possible 
            'temperature': 0.0, 

            #Setting a variable that lets the answer fully develop
            'num_predict': 2000 

        }
                        )
                        

    return response['message']['content']


# Setting up the directory to iterate
invoices_dir = Path('data/raw')

#Make a list that gathers the data before they become a Dataframe
all_rows = []

# Iteration for each pdf file
for file_path in invoices_dir.rglob('*.pdf'):
    try:
       
        #Extracting text
        ollama_food = info_ex(file_path)
        
        #If the PDF file is empty/blank, the invoice is skipped so that the LLM doesn't get confused
        if not ollama_food.strip():
            print(f"Αγνοήθηκε (άδειο κείμενο): {file_path.name}")
            continue
            
        #Taking the string from ollama
        raw_response = finalresult(ollama_food)
        
        #Turning the string output to a JSON
        parsed_data = json.loads(raw_response)
        
        #Add the name of the file
        parsed_data['File_Name'] = file_path.name
        
        #Save the row as a list
        all_rows.append(parsed_data)
        
        print(f"Επιτυχία: {file_path.name}")
        
    except Exception as e:
        #If an error occurs, the program doesn't stop and it projects an error message.
        print(f"Σφάλμα στο αρχείο {file_path.name}: {e}")

#Transform the list into a DataFrame 
if all_rows:
    df = pd.DataFrame(all_rows)
    
    # Setting index = False so that the first column is not 1, 2, 3 etc 
    with pd.ExcelWriter('data/raw/output_1.xlsx') as writer:
        df.to_excel(writer, sheet_name='Sheet 1', index=False)
        
    print(f"\nΟλοκληρώθηκε! Αποθηκεύτηκαν {len(df)} τιμολόγια.")
else:
    print("\nΔεν βρέθηκαν δεδομένα για εξαγωγή.")

    