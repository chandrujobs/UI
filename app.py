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

@app.route('/test-api', methods=['GET'])
def test_api():
    """Test endpoint to verify API connectivity"""
    try:
        # Print connection details for debugging
        print(f"Testing API connection to: {base_url}")
        print(f"Using model: {model_id}")
        
        # Try a simple API call
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": "Hello, this is a test message. Please respond with 'API test successful'."}
            ],
            max_tokens=20
        )
        
        # Get the response content
        response_text = response.choices[0].message.content
        
        return jsonify({
            'status': 'success',
            'message': 'API connection test successful',
            'api_response': response_text
        })
        
    except Exception as e:
        print(f"API test error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'API connection test failed: {str(e)}'
        }), 500

@app.route('/generate', methods=['POST'])
def generate_code():
    # Add detailed request logging
    print(f"Request received: {request.data}")
    
    # Check if request has JSON content
    if not request.is_json:
        print("Error: Request is not JSON format")
        return jsonify({'error': 'Request must be in JSON format'}), 400
        
    # Try to get the prompt from the request
    try:
        prompt = request.json.get('prompt', '')
        print(f"Prompt extracted: {prompt}")
    except Exception as e:
        print(f"Error extracting prompt: {str(e)}")
        return jsonify({'error': f'Invalid JSON format: {str(e)}'}), 400
    
    if not prompt:
        print("Error: Empty prompt received")
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

@app.route('/test-env', methods=['GET'])
def test_env():
    """Test endpoint to verify environment variables"""
    try:
        # Check environment variables
        env_status = {
            'api_key': bool(api_key),  # Don't return the actual key, just whether it exists
            'base_url': base_url,
            'model_id': model_id
        }
        
        # Check which variables are missing
        missing_vars = []
        if not api_key:
            missing_vars.append('OPENAI_API_KEY')
        if not base_url:
            missing_vars.append('OPENAI_BASE_URL')
        if not model_id:
            missing_vars.append('MODEL_ID')
        
        if missing_vars:
            return jsonify({
                'status': 'error',
                'message': f'Missing environment variables: {", ".join(missing_vars)}',
                'env_status': env_status
            }), 400
        else:
            return jsonify({
                'status': 'success',
                'message': 'All required environment variables are set',
                'env_status': env_status
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error checking environment variables: {str(e)}'
        }), 500

@app.route('/api-test', methods=['GET'])
def api_test_page():
    """Render the API test page"""
    return render_template('api-test.html')

if __name__ == '__main__':
    app.run(debug=True)
