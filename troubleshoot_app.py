# troubleshoot_app.py - Simple diagnostic app
import os
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model_id = os.getenv("MODEL_ID")

print("Environment variables:")
print(f"API Key exists: {bool(api_key)}")
print(f"Base URL: {base_url}")
print(f"Model ID: {model_id}")

# Initialize the OpenAI client
client = OpenAI(api_key=api_key, base_url=base_url)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('troubleshoot.html')

@app.route('/simple-test', methods=['POST'])
def simple_test():
    """Simple test endpoint that just echoes back the received JSON"""
    try:
        # Log raw request data
        print(f"Raw request data: {request.data}")
        
        # Check if Content-Type is application/json
        content_type = request.headers.get('Content-Type', '')
        print(f"Content-Type: {content_type}")
        
        if not content_type.startswith('application/json'):
            return jsonify({
                'error': f'Expected Content-Type application/json but got {content_type}'
            }), 400
        
        # Try to parse JSON
        try:
            data = request.get_json()
            print(f"Parsed JSON data: {data}")
            
            # Simply echo back the received data
            return jsonify({
                'status': 'success',
                'message': 'Request received successfully',
                'received_data': data
            })
            
        except Exception as e:
            print(f"JSON parsing error: {str(e)}")
            return jsonify({
                'error': f'Failed to parse JSON: {str(e)}'
            }), 400
            
    except Exception as e:
        print(f"Error in simple-test: {str(e)}")
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api-test', methods=['POST'])
def api_test():
    """Test endpoint for API connectivity"""
    try:
        # Get prompt from request
        data = request.get_json()
        prompt = data.get('prompt', 'Hello, this is a test message.')
        
        print(f"Testing API with prompt: {prompt}")
        
        # Make a simple API call
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        
        response_text = response.choices[0].message.content
        
        return jsonify({
            'status': 'success',
            'message': 'API test successful',
            'response': response_text
        })
        
    except Exception as e:
        print(f"API test error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'API test failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Using a different port to avoid conflicts
