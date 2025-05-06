from flask import Flask, request, jsonify, render_template, send_file
import os
import json
import logging
import base64
import tempfile
import fitz  # PyMuPDF for PDF processing
from io import BytesIO
from werkzeug.utils import secure_filename
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

# Model configuration - specify both shared service model and base model with fallbacks
shared_service_model = os.getenv("SHARED_SERVICE_MODEL", "vertex.ai.anthropic.claude-3.7-sonnet")
base_model = os.getenv("BASE_MODEL", "anthropic.claude-3-7-sonnet")

# Use the shared service model as the primary model ID
model_id = shared_service_model

# Prompt library (matching your Streamlit app)
prompt_library = {
    "Login Form": "A modern login screen with logo, email/password fields, and login button. Centered on a soft background.",
    "Product Cards": "Three product cards in a row, each with image, name, price, and Add to Cart button.",
    "Dashboard Layout": "A two-column dashboard with sidebar navigation and main content area containing charts or widgets.",
    "Registration Page": "A user registration form with full name, email, password, and confirm password fields. Minimal styling.",
    "Newsletter Signup": "Centered signup form with a heading, email input, and subscribe button on a soft gradient background."
}

logger.info(f"Using API URL: {base_url}")
logger.info(f"Using Shared Service Model: {shared_service_model}")
logger.info(f"Base Model: {base_model}")
logger.info(f"API Key configured: {'Yes' if api_key else 'No'}")

# Initialize OpenAI client
try:
    client = OpenAI(api_key=api_key, base_url=base_url)
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {str(e)}")

# Helpers for processing files
def extract_text_per_page(pdf_file, limit=3):
    """Extract text from each page of a PDF file"""
    page_texts = []
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc[:limit]:
            text = page.get_text().strip()
            if not text:
                text = "This page contains a UI screen. Generate a corresponding UX design."
            page_texts.append(text)
    return page_texts

def convert_image_to_description(image_file):
    """Convert image to a description for the AI"""
    return "This is a screenshot of a user interface. Replicate the layout using clean HTML and CSS."

# Home page 
@app.route('/')
def index():
    return render_template('index.html')

# Get prompt library
@app.route('/prompt-library', methods=['GET'])
def get_prompt_library():
    return jsonify(prompt_library)

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

# Generate UI and code endpoint
@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Check if API key is properly set
        if not api_key:
            logger.error("API key not found")
            return jsonify({'error': 'API key not found. Please check your .env file.'}), 401
        
        # Get form/JSON data    
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Form data with possible file
            prompt = request.form.get('prompt', '')
            device = request.form.get('device', 'desktop')
            file = request.files.get('file')
            max_pages = int(request.form.get('max_pages', 3))
            use_batching = request.form.get('use_batching', 'true').lower() == 'true'
        else:
            # JSON data
            data = request.json
            logger.debug(f"Received data: {data}")
            prompt = data.get('prompt', '')
            device = data.get('device', 'desktop')
            file = None
            max_pages = data.get('max_pages', 3)
            use_batching = data.get('use_batching', True)
        
        # If neither prompt nor file, require one
        if not prompt and not file:
            return jsonify({'error': 'Prompt or file is required'}), 400
            
        logger.info(f"Processing prompt/file for {device} view...")
            
        # Process pages from file or prompt
        pages = []
        
        if file:
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext == '.pdf':
                pages = extract_text_per_page(file, max_pages)
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                pages = [convert_image_to_description(file)]
            else:
                return jsonify({'error': 'Unsupported file type'}), 400
        
        if prompt:
            pages.append(prompt)
            
        if not pages:
            return jsonify({'error': 'No content to process'}), 400
            
        # Create system prompt based on device type
        system_prompt = f"""You are a UI/UX assistant that generates front-end HTML and CSS based on visual layouts or text descriptions. 
        Return clean, complete HTML that visually replicates the described layout. 
        Use inline <style> or <style> tags. 
        Do NOT return markdown, explanations, or code blocks. 
        Only output raw HTML for rendering. 
        Optimize for {device} view.
        """
        
        logger.info("Sending request to OpenAI API...")
        
        # Generate UX designs
        generated_html_list = []
        
        try:
            if use_batching and len(pages) > 1:
                # Batch mode - generate all screens at once
                combined_prompt = "\n\n---\n\n".join(pages)
                
                try:
                    # Try with response_format first
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Generate separate UX designs for the following screens:\n{combined_prompt}"}
                        ],
                        temperature=0.3,
                        max_tokens=4096
                    )
                except Exception as format_error:
                    logger.warning(f"Response format parameter failed, trying without it: {str(format_error)}")
                    # Try without response_format
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Generate separate UX designs for the following screens:\n{combined_prompt}"}
                        ],
                        temperature=0.3,
                        max_tokens=4096
                    )
                
                full_output = response.choices[0].message.content.strip()
                
                # Extract HTML blocks - similar to Streamlit logic
                chunks = full_output.split("<html")
                for chunk in chunks[1:]:  # Skip anything before first <html>
                    html_code = "<html" + chunk.strip()
                    if html_code.endswith("```"):
                        html_code = html_code.strip("```")
                    generated_html_list.append(html_code)
            else:
                # Individual mode - generate each screen separately
                for page_prompt in pages:
                    try:
                        response = client.chat.completions.create(
                            model=model_id,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": page_prompt}
                            ],
                            temperature=0.3,
                            max_tokens=2048
                        )
                    except Exception as e:
                        logger.error(f"Error generating individual screen: {str(e)}")
                        continue
                        
                    html_code = response.choices[0].message.content.strip()
                    if html_code.startswith("```") and html_code.endswith("```"):
                        html_code = html_code.strip("```")
                    generated_html_list.append(html_code)
                
            # Generate equivalent framework code for the first HTML
            if generated_html_list:
                first_html = generated_html_list[0]
                
                # Now generate React, Vue, and Angular versions
                framework_prompt = f"""
                Convert the following HTML/CSS code to equivalent {{'react': 'React', 'vue': 'Vue', 'angular': 'Angular'}} component code.
                
                HTML Code:
                {first_html}
                
                Return your response as a JSON object with the following structure:
                {{
                    "react": "<complete React component code>",
                    "vue": "<complete Vue component code>",
                    "angular": "<complete Angular component code>"
                }}
                
                Do not include any explanations, just the JSON response.
                """
                
                try:
                    framework_response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": "You are an expert front-end developer."},
                            {"role": "user", "content": framework_prompt}
                        ],
                        response_format={"type": "json_object"},
                        max_tokens=4000
                    )
                except Exception as format_error:
                    logger.warning(f"Response format parameter failed for frameworks, trying without it: {str(format_error)}")
                    framework_response = client.chat.completions.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": "You are an expert front-end developer."},
                            {"role": "user", "content": framework_prompt}
                        ],
                        max_tokens=4000
                    )
                
                content = framework_response.choices[0].message.content.strip()
                
                # Try to extract JSON from markdown if needed
                if content.strip().startswith("```json") or content.strip().startswith("```"):
                    import re
                    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if match:
                        content = match.group(1)
                
                try:
                    framework_code = json.loads(content)
                except json.JSONDecodeError:
                    # If JSON parsing fails, provide placeholders
                    framework_code = {
                        "react": "// React code could not be generated",
                        "vue": "// Vue code could not be generated",
                        "angular": "// Angular code could not be generated"
                    }
                
                # Create complete result
                result = {
                    "html": first_html,
                    "react": framework_code.get("react", "// React code unavailable"),
                    "vue": framework_code.get("vue", "// Vue code unavailable"),
                    "angular": framework_code.get("angular", "// Angular code unavailable"),
                    "multi_screen_html": generated_html_list
                }
                
                return jsonify(result)
            else:
                return jsonify({'error': 'Failed to generate UI'}), 500
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return jsonify({'error': f'API call failed: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Generate endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Error handler for 500 errors
@app.errorhandler(500)
def handle_500(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({"error": "Internal server error", "details": str(e)}), 500

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

if __name__ == '__main__':
    try:
        setup_app()
        logger.info("Starting application on port 5000")
        app.run(debug=True, port=5000)
    except Exception as e:
        logger.critical(f"Failed to start application: {str(e)}")
