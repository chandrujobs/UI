# app.py - Flask backend for CodePilot AI
import os
import json
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

        Format your response as a JSON with these exact keys:
        - "interactive_code": Combined HTML/CSS/JS code ready to be rendered directly
        - "html_code": Just the HTML component
        - "css_code": Just the CSS component 
        - "js_code": Just the JavaScript component
        - "explanation": Brief explanation of how the code works
        
        Important formatting rules:
        - Make sure the JSON response is properly formatted and valid
        - The "interactive_code" must be a complete HTML document with inline CSS and JavaScript
        - Escape all special characters in the code values
        - Do not include any markdown code blocks or formatting in your response, just raw JSON
        - The final response must be valid JSON that can be parsed with JSON.parse()
        - Make sure all code is complete, working, and properly formatted
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
        
        # Validate that the result is valid JSON before sending it to the client
        try:
            # Try to parse it to validate, but send the original string to the client
            # so they can parse it themselves
            json_result = json.loads(result)
            
            # Check for required fields
            required_fields = ['interactive_code', 'html_code', 'css_code', 'js_code', 'explanation']
            missing_fields = [field for field in required_fields if field not in json_result]
            
            if missing_fields:
                return jsonify({
                    'error': f'Response missing required fields: {", ".join(missing_fields)}'
                }), 400
                
            # Return the parsed JSON object directly
            return jsonify({'result': json_result})
            
        except json.JSONDecodeError as e:
            return jsonify({
                'error': f'Invalid JSON response from AI: {str(e)}',
                'raw_response': result
            }), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
