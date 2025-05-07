# app.py - Flask backend for CodePilot AI
import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model_id = os.getenv("MODEL_ID")

# Initialize the OpenAI client
client = OpenAI(api_key=api_key, base_url=base_url)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_code():
    prompt = request.json.get('prompt', '')
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    try:
        # Create a prompt that instructs Claude to generate both HTML/CSS/JS and the separate code
        system_message = """
        You are CodePilot AI, an expert UI developer. Generate:
        1. Complete, functional HTML/CSS/JS code for an interactive UI based on the user's prompt
        2. Separate HTML, CSS, and JavaScript code that can be copied

        Format your response as a JSON with these keys:
        - "interactive_code": Combined HTML/CSS/JS code ready to be rendered directly
        - "html_code": Just the HTML component
        - "css_code": Just the CSS component 
        - "js_code": Just the JavaScript component
        - "explanation": Brief explanation of how the code works
        
        Make sure all code is complete, working, and properly formatted.
        """
        
        # Call Claude API
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Create an interactive UI for: {prompt}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=4000
        )
        
        # Extract and parse the response
        result = response.choices[0].message.content
        return jsonify({'result': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
