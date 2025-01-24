import numpy as np
import pandas as pd
import os

import google.generativeai as genai # type: ignore
import openai
import anthropic

import time
from threading import Lock

# Initialize a lock for thread-safe rate limiting
rate_limit_lock = Lock()
last_request_time = time.time()

# Constants for rate-limiting
REQUESTS_PER_MINUTE = 2  # Max 2 requests per minute
MIN_REQUEST_INTERVAL = 60 / REQUESTS_PER_MINUTE  # Minimum time between requests (seconds)

def enforce_rate_limit():
        """
        Ensures requests are spaced out to adhere to rate-limiting constraints.
        """
        global last_request_time

        with rate_limit_lock:  # Ensure thread safety
            current_time = time.time()
            elapsed_time = current_time - last_request_time

            # Check if we need to delay
            if elapsed_time < MIN_REQUEST_INTERVAL:
                delay = MIN_REQUEST_INTERVAL - elapsed_time
                print(f"Rate limiting: Sleeping for {delay:.2f} seconds...")
                time.sleep(delay)

            # Update the last request timestamp
            last_request_time = time.time()


gemini_api_key = os.getenv('GEMINI_API_KEY')
openai_api_key = os.getenv('OPENAI_API_KEY')
claude_api_key = os.getenv('CLAUDE_API_KEY')

class LLMScore:

    def initialiseModel():
        
        genai.configure(api_key=gemini_api_key)
        openai.api_key = openai_api_key

    async def query_api(model_name, jd, resume):

        prompt = f"""I'm picking top resume from the collection of resumes given the jd. Given this jd = [{jd}] and the resume = [{resume}], based on your score I'll order them. How well does the candidate's technical skills and other requirements match the job requirements? Give me a match score between this jd and the resume. The return element should just be a score between 0 and 1, no other text."""

        if model_name == "Gemini":

          #enforce_rate_limit()
          #print("Using Gemini-Model")

           model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

           try:
               
                response = await model.generate_content(prompt)
                return response.text
           
           except Exception as e:
                
                print(f"Error querying Gemini API: {e}")
                return None
        
        elif model_name == "OpenAI":

            try:
                response = await openai.ChatCompletion.acreate(
                    model="gpt-4", 
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10 
                )
               
                return response['choices'][0]['message']['content'].strip()
            
            except Exception as e:
                print(f"Error querying OpenAI API: {e}")
                return None
        
        elif model_name == "Claude":

            try:
                client = anthropic.Client(api_key=claude_api_key)
                response = await client.completions.create(
                    model="claude-2", 
                    prompt=f"{anthropic.HUMAN_PROMPT} {prompt}{anthropic.AI_PROMPT}",
                    max_tokens_to_sample=10  
                )
               
                return response['completion'].strip()
            
            except Exception as e:
                print(f"Error querying Claude API: {e}")
                return None 