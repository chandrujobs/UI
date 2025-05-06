from flask import Flask, request, jsonify, render_template
import os
import json
import logging
from dotenv import load_dotenv
from flask_cors import CORS
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure static folder explicitly
app = Flask(__name__, 
            static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'),
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))
            
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for all routes

# Get environment variables - using your exact naming convention
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model_id = os.getenv("MODEL_ID", "gpt-4o-mini")  # Default to gpt-4o-mini if not specified

logger.info(f"Using API URL: {base_url}")
logger.info(f"Using Model ID: {model_id}")
logger.info(f"API Key configured: {'Yes' if api_key else 'No'}")

# Initialize OpenAI client
try:
    client = OpenAI(api_key=api_key, base_url=base_url)
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {str(e)}")

# Home page 
@app.route('/')
def index():
    return render_template('index.html')

# Test route to verify API connectivity
@app.route('/test-api', methods=['GET'])
def test_api():
    try:
        # Simple test to verify API key works
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=10
        )
        return jsonify({"status": "API connection successful"})
    except Exception as e:
        logger.error(f"API test failed: {str(e)}")
        return jsonify({"status": "API connection failed", "error": str(e)}), 500

# Simple test generation endpoint for debugging
@app.route('/test-generate', methods=['GET'])
def test_generate():
    """Test endpoint that returns hardcoded UI for debugging"""
    return jsonify({
        "html": """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial; margin: 0; padding: 20px; }
        h1 { color: #4338ca; }
    </style>
</head>
<body>
    <h1>Test UI</h1>
    <p>This is a test UI to verify the preview functionality.</p>
</body>
</html>""",
        "react": "function TestUI() { return <h1>Test UI</h1>; }",
        "vue": "<template><h1>Test UI</h1></template>",
        "angular": "<h1>Test UI</h1>"
    })

# Generate UI and code endpoint
@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Check if API key is properly set
        if not api_key:
            logger.error("API key not found")
            return jsonify({'error': 'API key not found. Please check your .env file.'}), 401
            
        data = request.json
        logger.debug(f"Received data: {data}")
        
        prompt = data.get('prompt', '')
        device = data.get('device', 'desktop')
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
            
        logger.info(f"Processing prompt for {device} view: {prompt[:50]}...")
            
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
        
        # Create prompt for OpenAI
        user_prompt = f"""
        Create a UI based on this description: {prompt}
        
        Optimize it for {device} view.
        """
        
        logger.info("Sending request to OpenAI API...")
        
        # Send request to OpenAI
        try:
            # Some API implementations might not support response_format
            # Try first with response_format
            try:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=4000
                )
            except Exception as format_error:
                logger.warning(f"Response format parameter failed, trying without it: {str(format_error)}")
                # If it fails, try without response_format
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=4000
                )
                
            logger.info("Received response from OpenAI API")
            
            # Extract the JSON content from the response
            try:
                content = response.choices[0].message.content
                logger.debug(f"Content sample: {content[:100]}...")
                
                # Sometimes the API might return content with markdown code blocks
                # Try to extract JSON from markdown if needed
                if content.strip().startswith("```json") or content.strip().startswith("```"):
                    import re
                    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if match:
                        content = match.group(1)
                        logger.info("Extracted JSON from markdown code block")
                
                # Parse the response
                try:
                    result = json.loads(content)
                    
                    # Ensure all required fields exist
                    required_fields = ["html", "react", "vue", "angular"]
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if missing_fields:
                        logger.warning(f"Missing fields in response: {missing_fields}")
                        # Add empty placeholders for missing fields
                        for field in missing_fields:
                            result[field] = f"// {field.capitalize()} code could not be generated"
                    
                    # Make sure HTML includes doctype if not present
                    if "html" in result and not result["html"].lower().startswith("<!doctype"):
                        result["html"] = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
{result["html"]}
</body>
</html>"""
                    
                    return jsonify(result)
                except json.JSONDecodeError as json_err:
                    logger.error(f"Failed to parse JSON: {json_err}")
                    # Attempt to fix common JSON syntax errors
                    fixed_content = content.replace("'", '"').replace('\n', '\\n')
                    try:
                        result = json.loads(fixed_content)
                        logger.info("Fixed JSON parsing issue")
                        return jsonify(result)
                    except:
                        # As a last resort, return a minimal working UI
                        logger.error("Could not fix JSON, returning minimal UI")
                        return jsonify({
                            "html": f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial; margin: 0; padding: 20px; }}
        h1 {{ color: #4338ca; }}
    </style>
</head>
<body>
    <h1>{prompt}</h1>
    <p>The UI could not be generated correctly. Please try again with different parameters.</p>
</body>
</html>""",
                            "react": "function UI() { return <h1>UI Generation Error</h1>; }",
                            "vue": "<template><h1>UI Generation Error</h1></template>",
                            "angular": "<h1>UI Generation Error</h1>"
                        })
            except Exception as e:
                logger.error(f"Error processing content: {str(e)}")
                return jsonify({'error': f'Content processing failed: {str(e)}'}), 500
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return jsonify({'error': f'API call failed: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Generate endpoint error: {str(e)}")
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
    
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    os.makedirs(static_dir, exist_ok=True)
    
    # Create index.html file in templates
    with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
        f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Codepilot AI</title>
    <!-- Redirect to static version -->
</head>
<body>
    <script>
        window.location.href = '/static/index.html';
    </script>
</body>
</html>""")

# Error handler for 500 errors
@app.errorhandler(500)
def handle_500(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == '__main__':
    try:
        setup_app()
        logger.info("Starting application on port 5000")
        app.run(debug=True, port=5000)
    except Exception as e:
        logger.critical(f"Failed to start application: {str(e)}")
