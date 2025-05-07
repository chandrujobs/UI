# minimal_app.py - Simplified version to fix 400 error
import os
import json
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model_id = os.getenv("MODEL_ID")

print("Environment variables loaded:")
print(f"API Key exists: {bool(api_key)}")
print(f"Base URL: {base_url}")
print(f"Model ID: {model_id}")

# Initialize the OpenAI client
client = OpenAI(api_key=api_key, base_url=base_url)

app = Flask(__name__)

# Minimal HTML template with form
MINIMAL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Minimal CodePilot</title>
    <style>
        body { font-family: Arial; max-width: 800px; margin: 0 auto; padding: 20px; }
        textarea { width: 100%; height: 100px; margin-bottom: 10px; }
        button { background: blue; color: white; padding: 10px 15px; border: none; }
        pre { background: #f5f5f5; padding: 15px; overflow: auto; }
        .result { margin-top: 20px; display: none; }
    </style>
</head>
<body>
    <h1>Minimal CodePilot</h1>
    <form id="form">
        <textarea id="prompt" placeholder="Describe the UI you want..."></textarea>
        <button type="submit">Generate</button>
    </form>
    <div id="loading" style="display:none;">Loading...</div>
    <div id="result" class="result">
        <h2>Result:</h2>
        <pre id="output"></pre>
    </div>

    <script>
        document.getElementById('form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const prompt = document.getElementById('prompt').value;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt: prompt })
                });
                
                const text = await response.text();
                console.log("Raw response:", text);
                
                let data;
                try {
                    data = JSON.parse(text);
                } catch (e) {
                    document.getElementById('output').textContent = 
                        "Error parsing JSON response: " + e.message + "\n\nRaw response:\n" + text;
                    document.getElementById('result').style.display = 'block';
                    return;
                }
                
                document.getElementById('output').textContent = JSON.stringify(data, null, 2);
                document.getElementById('result').style.display = 'block';
            } catch (error) {
                document.getElementById('output').textContent = "Error: " + error.message;
                document.getElementById('result').style.display = 'block';
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(MINIMAL_HTML)

@app.route('/api/generate', methods=['POST'])
def generate():
    # Print request details
    print("\n--- REQUEST DETAILS ---")
    print(f"Content-Type: {request.content_type}")
    print(f"Raw data: {request.data}")
    
    # Check for JSON content type
    if not request.is_json:
        error_msg = f"Expected application/json Content-Type but got {request.content_type}"
        print(f"Error: {error_msg}")
        return jsonify({"error": error_msg}), 400
    
    # Parse JSON
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
            
        print(f"Prompt: {prompt}")
    except Exception as e:
        error_msg = f"Error parsing JSON: {str(e)}"
        print(f"Error: {error_msg}")
        return jsonify({"error": error_msg}), 400
    
    # Create a simple response without calling the API
    simple_response = {
        "message": "Received prompt: " + prompt,
        "sample_output": {
            "interactive_code": "<html><body><button>Click Me</button></body></html>",
            "html_code": "<button>Click Me</button>",
            "css_code": "button { padding: 10px; background-color: blue; color: white; }",
            "js_code": "document.querySelector('button').addEventListener('click', function() { alert('Button clicked!'); });",
            "explanation": "This is a simple button example."
        }
    }
    
    return jsonify(simple_response)

@app.route('/api/test-claude', methods=['POST'])
def test_claude():
    try:
        data = request.get_json()
        prompt = data.get('prompt', 'Hello')
        
        # Make a simple API call to test connectivity
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50
        )
        
        response_text = response.choices[0].message.content
        
        return jsonify({
            "status": "success",
            "api_response": response_text
        })
    except Exception as e:
        print(f"Claude API error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    # Note the different port to avoid conflicts
    app.run(debug=True, port=5002)
