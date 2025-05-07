# app.py - Streamlit version of CodePilot AI
import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import base64

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model_id = os.getenv("MODEL_ID")

# Initialize the OpenAI client
client = OpenAI(api_key=api_key, base_url=base_url)

# Page config
st.set_page_config(
    page_title="CodePilot AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# App title and description
st.title("CodePilot AI")
st.markdown("Transform your ideas into interactive UI with code")

# Function to generate code from Claude
def generate_code(prompt):
    try:
        # System message for Claude
        system_message = """
        You are CodePilot AI, an expert UI developer. Generate:
        1. Complete, functional HTML/CSS/JS code for an interactive UI based on the user's prompt
        2. Separate HTML, CSS, and JavaScript code that can be copied

        Your response MUST be a valid JSON object with EXACTLY these fields (all are required):
        - "interactive_code": A complete self-contained HTML document with inline CSS and JavaScript
        - "html_code": Just the HTML component (without CSS and JS)
        - "css_code": Just the CSS component
        - "js_code": Just the JavaScript component
        - "explanation": Brief explanation of how the code works

        This is CRITICAL: All fields must be present in your response. 
        The "interactive_code" field must contain a complete HTML document that includes CSS in a <style> tag and JavaScript in a <script> tag.
        """
        
        # Default fallback response
        fallback_response = {
            "interactive_code": "<html><body><p>Simple button example</p><button>Click me</button></body></html>",
            "html_code": "<button>Click me</button>",
            "css_code": "button { padding: 10px; background-color: blue; color: white; }",
            "js_code": "document.querySelector('button').addEventListener('click', function() { alert('Button clicked!'); });",
            "explanation": "This is a simple button example."
        }
        
        # Call Claude API
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Create an interactive UI for: {prompt}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=4000,
            temperature=0.7
        )
        
        # Parse the response
        result = response.choices[0].message.content
        
        try:
            json_result = json.loads(result)
            
            # Check for required fields
            required_fields = ['interactive_code', 'html_code', 'css_code', 'js_code', 'explanation']
            missing_fields = [field for field in required_fields if field not in json_result]
            
            if missing_fields:
                st.warning(f"Response missing fields: {', '.join(missing_fields)}. Using fallback values for those fields.")
                
                # Add any missing fields with default values
                for field in missing_fields:
                    json_result[field] = fallback_response[field]
                
            return json_result
            
        except json.JSONDecodeError as e:
            st.error(f"Error parsing JSON response: {str(e)}")
            return fallback_response
            
    except Exception as e:
        st.error(f"Error generating code: {str(e)}")
        return fallback_response

# Function to create an HTML display for the interactive code
def get_html_display(html_code):
    # Encode the HTML to display in an iframe
    encoded = base64.b64encode(html_code.encode()).decode()
    return f'data:text/html;base64,{encoded}'

# Main app layout
with st.container():
    # Prompt input area
    prompt = st.text_area("Describe the UI you want to create:", 
                          placeholder="E.g., Create a contact form with name, email, message fields and a submit button", 
                          height=150)
    
    # Generate button
    if st.button("Generate UI", type="primary", use_container_width=True):
        if not prompt:
            st.warning("Please enter a prompt first.")
        else:
            with st.spinner("Generating your UI and code..."):
                # Call Claude to generate code
                result = generate_code(prompt)
                
                # Store result in session state to persist it
                st.session_state.result = result
                st.session_state.show_result = True

# Display results if available
if 'show_result' in st.session_state and st.session_state.show_result:
    result = st.session_state.result
    
    # Create tabs for different sections
    tab1, tab2 = st.tabs(["UI Preview", "Code"])
    
    with tab1:
        st.header("Generated UI Preview")
        # Display the interactive UI in an iframe
        iframe_height = 500
        st.components.v1.iframe(get_html_display(result["interactive_code"]), height=iframe_height, scrolling=True)
        
        st.subheader("How it works")
        st.write(result["explanation"])
    
    with tab2:
        # Create code tabs
        code_tab1, code_tab2, code_tab3 = st.tabs(["HTML", "CSS", "JavaScript"])
        
        with code_tab1:
            st.code(result["html_code"], language="html")
            if st.button("Copy HTML", key="copy_html"):
                st.session_state.clipboard = result["html_code"]
                st.success("HTML code copied to clipboard!")
        
        with code_tab2:
            st.code(result["css_code"], language="css")
            if st.button("Copy CSS", key="copy_css"):
                st.session_state.clipboard = result["css_code"]
                st.success("CSS code copied to clipboard!")
        
        with code_tab3:
            st.code(result["js_code"], language="javascript")
            if st.button("Copy JavaScript", key="copy_js"):
                st.session_state.clipboard = result["js_code"]
                st.success("JavaScript code copied to clipboard!")
        
        # Download full code option
        full_code = result["interactive_code"]
        st.download_button(
            label="Download Full Code",
            data=full_code,
            file_name="generated_ui.html",
            mime="text/html",
        )

# Add footer
st.markdown("---")
st.markdown("© 2025 CodePilot AI - Powered by Claude 3.7 Sonnet")

# Custom CSS for better styling
st.markdown("""
<style>
    .stButton button {
        background-color: #4a6cf7;
        color: white;
        font-weight: bold;
    }
    .stTextArea textarea {
        border-radius: 10px;
    }
    h1, h2, h3 {
        color: #4a6cf7;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4a6cf7;
        color: white;
    }
    iframe {
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: white;
    }
    footer {
        text-align: center;
        color: #888;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)
