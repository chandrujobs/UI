from flask import Flask, request, jsonify, render_template
import os
import json
import anthropic
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get environment variables
OPEN_API_KEY = os.getenv("OPEN_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL_ID = os.getenv("MODEL_ID")

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=OPEN_API_KEY, base_url=OPENAI_BASE_URL)

# Home page 
@app.route('/')
def index():
    return render_template('index.html')

# Generate UI and code endpoint
@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        device = data.get('device', 'desktop')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
            
        # Create system prompt based on device type
        system_prompt = f"""You are an expert UI/UX designer and front-end developer. 
        You will be given a prompt describing a UI that needs to be created.
        Your task is to generate:
        1. Clean, responsive HTML/CSS code for the requested UI optimized for {device} view
        2. Equivalent React code using functional components and hooks
        3. Equivalent Vue 3 code using the Composition API
        4. Equivalent Angular code
        
        For the HTML/CSS:
        - Use modern CSS practices
        - Ensure it's fully responsive
        - Include inline CSS in a <style> tag
        - Don't use any external libraries or CDNs
        - Make it visually appealing with good typography and spacing
        - For {device} view specifically, optimize the layout and sizes accordingly
        
        Return your response as a JSON object with the following structure:
        {{
            "html": "<complete HTML code with inline CSS>",
            "react": "<complete React component code>",
            "vue": "<complete Vue component code>",
            "angular": "<complete Angular component code>"
        }}
        
        Do not include any explanations, just the JSON response.
        """
        
        # Create prompt for Claude
        user_prompt = f"""
        Create a UI based on this description: {prompt}
        
        Optimize it for {device} view.
        """
        
        # Send request to Claude
        response = client.messages.create(
            model=MODEL_ID,
            system=system_prompt,
            max_tokens=4000,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Parse the response
        content = response.content[0].text
        
        # Extract JSON from response (handle potential explanatory text)
        try:
            # Try to parse the entire content as JSON
            result = json.loads(content)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the text
            import re
            json_match = re.search(r'```json\n([\s\S]*?)\n```', content)
            if json_match:
                try:
                    result = json.loads(json_match.group(1))
                except:
                    return jsonify({'error': 'Failed to parse JSON from response'}), 500
            else:
                # Last resort: look for { and } brackets
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    try:
                        result = json.loads(json_match.group(0))
                    except:
                        return jsonify({'error': 'Failed to parse JSON from response'}), 500
                else:
                    return jsonify({'error': 'Could not extract JSON from response'}), 500
        
        # Return the result
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Sample prompts endpoint
@app.route('/sample-prompts', methods=['GET'])
def sample_prompts():
    # Return a list of sample prompts
    prompts = [
        "E-commerce product page with product image, details, and add to cart button",
        "Task management dashboard with tasks organized by status",
        "Blog article layout with featured image, title, content and sidebar",
        "Contact form with name, email, subject and message fields",
        "User profile page with avatar, bio and activity feed",
        "Landing page for SaaS product with hero section, features and pricing"
    ]
    return jsonify(prompts)

# Create templates directory and save index.html
def setup_app():
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create index.html file from our HTML content in the UI artifact
    # In a real implementation, you would have this file already in your project
    # This is just for demonstration purposes
    with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codepilot AI</title>
    <!-- Insert the HTML from the UI artifact here -->
</head>
<body>
    <!-- Content will be loaded from the UI artifact -->
    <script>
        window.location.href = '/static/index.html';
    </script>
</body>
</html>""")

if __name__ == '__main__':
    setup_app()
    app.run(debug=True, port=5000)
