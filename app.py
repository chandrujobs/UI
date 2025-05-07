# app.py - Fixed Streamlit version of CodePilot AI
import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import base64
from datetime import datetime

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
    initial_sidebar_state="expanded"
)

# Define frontend frameworks
FRAMEWORKS = {
    "HTML/CSS/JS": "Standard HTML, CSS, and JavaScript",
    "React": "React with functional components and hooks",
    "Vue.js": "Vue.js 3 with Composition API",
    "Angular": "Angular with TypeScript",
    "Svelte": "Svelte components"
}

# Define device types with numerical dimensions
DEVICES = {
    "Desktop": {"width": 1200, "height": 600},
    "Tablet": {"width": 768, "height": 600},
    "Mobile": {"width": 375, "height": 667}
}

# Prompt library organized by categories
PROMPT_LIBRARY = {
    "Form Components": [
        "Create a login form with email and password fields",
        "Create a sign-up form with name, email, password, and confirm password fields",
        "Create a contact form with name, email, subject, message, and submit button",
        "Create a checkout form with billing address, payment details, and order summary",
        "Create a search form with filters for categories, price range, and ratings"
    ],
    "Navigation Components": [
        "Create a responsive navbar with logo, links, and a hamburger menu for mobile",
        "Create a sidebar navigation with collapsible categories",
        "Create a bottom navigation bar for mobile with icons",
        "Create a mega menu with dropdown categories and featured items",
        "Create a breadcrumb navigation for a product page"
    ],
    "Interactive Elements": [
        "Create an image carousel/slider with navigation arrows",
        "Create a modal popup with form inside",
        "Create an accordion FAQ section",
        "Create a tabbed interface for product information",
        "Create a star rating component with interactive feedback"
    ],
    "Data Display": [
        "Create a responsive data table with sorting and filtering",
        "Create a pricing table with multiple tiers",
        "Create a dashboard with key metrics and charts",
        "Create a product grid with cards and quick view options",
        "Create a timeline component for displaying events"
    ],
    "Complete Layouts": [
        "Create a landing page with hero section, features, and call to action",
        "Create a product page with images, details, related items, and reviews",
        "Create a blog layout with featured post, recent posts, and sidebar",
        "Create a portfolio gallery with filtering options",
        "Create an admin dashboard layout with sidebar navigation and statistics"
    ]
}

# Initialize session state variables
if 'current_device' not in st.session_state:
    st.session_state.current_device = "Desktop"
if 'current_framework' not in st.session_state:
    st.session_state.current_framework = "HTML/CSS/JS"
if 'history' not in st.session_state:
    st.session_state.history = []
if 'selected_prompt_category' not in st.session_state:
    st.session_state.selected_prompt_category = None
if 'selected_prompt' not in st.session_state:
    st.session_state.selected_prompt = None
if 'show_result' not in st.session_state:
    st.session_state.show_result = False

# Function to generate code from Claude
def generate_code(prompt, framework, device):
    try:
        # System message for Claude
        system_message = f"""
        You are CodePilot AI, an expert UI developer. Generate:
        1. Complete, functional code for an interactive UI based on the user's prompt
        2. The code should be specifically optimized for {device} devices
        3. Use the {framework} framework/technology

        Your response MUST be a valid JSON object with EXACTLY these fields (all are required):
        - "interactive_code": A complete self-contained code that can be rendered directly
        - "separate_code": The code in separate files format
        - "explanation": Detailed explanation of how the code works and its features
        - "css_code": Just the CSS/styling component
        - "framework_specific_code": The main code specific to the chosen framework
        - "additional_files": Any additional files or components needed

        Important details:
        - For {device} optimization, ensure proper responsive design, appropriate font sizes, and interaction patterns
        - For {framework}, follow best practices and latest patterns
        - Ensure the design is modern, professional, and visually appealing
        - Include appropriate animations and transitions for a polished user experience
        - Make sure all code is complete, working, and properly formatted
        """
        
        # Default fallback response (simplified for space)
        fallback_response = {
            "interactive_code": "<html><body><p>Simple example</p><button>Click me</button></body></html>",
            "separate_code": {"html": "<button>Click me</button>", "css": "button { padding: 10px; }", "js": "// JS code"},
            "explanation": "This is a simple example.",
            "css_code": "button { padding: 10px; background-color: blue; color: white; }",
            "framework_specific_code": "// Framework code would go here",
            "additional_files": {}
        }
        
        # Call Claude API
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Create an interactive UI for: {prompt}. Make it professional, modern, and optimized for {device} with {framework}."}
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
            required_fields = ['interactive_code', 'separate_code', 'explanation', 'css_code', 'framework_specific_code', 'additional_files']
            missing_fields = [field for field in required_fields if field not in json_result]
            
            if missing_fields:
                st.warning(f"Response missing fields: {', '.join(missing_fields)}. Using fallback values for those fields.")
                
                # Add any missing fields with default values
                for field in missing_fields:
                    json_result[field] = fallback_response[field]
                
            # Add generation metadata
            json_result["metadata"] = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "prompt": prompt,
                "framework": framework,
                "device": device
            }
            
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

# Sidebar for settings and history
with st.sidebar:
    st.title("CodePilot AI")
    
    # Framework selection
    st.subheader("Framework")
    selected_framework = st.selectbox("Select Framework", list(FRAMEWORKS.keys()), index=list(FRAMEWORKS.keys()).index(st.session_state.current_framework))
    if selected_framework != st.session_state.current_framework:
        st.session_state.current_framework = selected_framework
    
    # Prompt Library as a dropdown
    st.subheader("Prompt Library")
    
    # First dropdown for category selection
    categories = list(PROMPT_LIBRARY.keys())
    selected_category = st.selectbox("Select Category", categories)
    
    # Second dropdown for prompt selection within the category
    if selected_category:
        prompts = PROMPT_LIBRARY[selected_category]
        selected_prompt = st.selectbox("Select Prompt", prompts)
        
        # Button to use the selected prompt
        if st.button("Use This Prompt", use_container_width=True):
            st.session_state.selected_prompt = selected_prompt
            st.experimental_rerun()
    
    # History section (if exists)
    if st.session_state.history:
        st.subheader("History")
        for idx, item in enumerate(st.session_state.history):
            if st.button(f"{item['prompt'][:30]}...", key=f"history_{idx}", use_container_width=True):
                st.session_state.result = item['result']
                st.session_state.show_result = True
                st.session_state.current_framework = item['framework']
                st.rerun()

# Main content area
st.title("CodePilot AI")
st.markdown("Transform your ideas into professional, responsive UI with multiple framework options")

# Initialize prompt input
prompt_value = st.session_state.selected_prompt if st.session_state.selected_prompt else ""

# Input and generation section
with st.container():
    with st.form("generation_form"):
        prompt = st.text_area("Describe the UI you want to create:", 
                              value=prompt_value,
                              placeholder="E.g., Create a modern dashboard with sidebar navigation", 
                              height=100)
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Framework: {st.session_state.current_framework}")
        with col2:
            st.info(f"Device: {st.session_state.current_device}")
            
        # Generate button
        submitted = st.form_submit_button("Generate UI", type="primary", use_container_width=True)
        
        if submitted:
            if not prompt:
                st.warning("Please enter a prompt first.")
            else:
                with st.spinner("Generating your UI and code..."):
                    # Call Claude to generate code
                    result = generate_code(
                        prompt, 
                        st.session_state.current_framework, 
                        st.session_state.current_device
                    )
                    
                    # Add to history
                    history_item = {
                        'prompt': prompt,
                        'framework': st.session_state.current_framework,
                        'device': st.session_state.current_device,
                        'result': result
                    }
                    
                    # Add to history (limit to 10 items)
                    st.session_state.history.insert(0, history_item)
                    if len(st.session_state.history) > 10:
                        st.session_state.history = st.session_state.history[:10]
                    
                    # Store result in session state
                    st.session_state.result = result
                    st.session_state.show_result = True
                    st.session_state.selected_prompt = None  # Clear selected prompt
                    
                    # Reset the form
                    st.experimental_rerun()

# Display results if available
if 'show_result' in st.session_state and st.session_state.show_result and 'result' in st.session_state:
    result = st.session_state.result
    
    # Create tabs for different sections
    preview_tab, code_tab, explanation_tab = st.tabs(["UI Preview", "Code", "Explanation"])
    
    with preview_tab:
        # Device selection buttons in a row
        st.subheader("Device Preview")
        device_cols = st.columns(3)
        
        for i, device in enumerate(DEVICES.keys()):
            if device_cols[i].button(device, key=f"device_{device}", use_container_width=True):
                st.session_state.current_device = device
                # Only regenerate if the device changes and there's a prompt
                if 'result' in st.session_state and st.session_state.result:
                    prompt = st.session_state.result["metadata"]["prompt"]
                    framework = st.session_state.current_framework
                    with st.spinner(f"Optimizing for {device}..."):
                        result = generate_code(prompt, framework, device)
                        st.session_state.result = result
                        # Update history
                        if st.session_state.history:
                            st.session_state.history[0]['result'] = result
                            st.session_state.history[0]['device'] = device
                st.experimental_rerun()
        
        # Create a container with the specified device dimensions
        device_dims = DEVICES[st.session_state.current_device]
        
        # Create a centered container for the preview
        col1, preview_col, col2 = st.columns([1, 10, 1])
        
        with preview_col:
            # Add device frame styling
            if st.session_state.current_device == "Mobile":
                st.markdown("""
                <div style="margin: 0 auto; max-width: 375px; border: 12px solid #222; border-radius: 25px; overflow: hidden;">
                """, unsafe_allow_html=True)
            elif st.session_state.current_device == "Tablet":
                st.markdown("""
                <div style="margin: 0 auto; max-width: 768px; border: 16px solid #222; border-radius: 25px; overflow: hidden;">
                """, unsafe_allow_html=True)
            
            # Display the iframe
            st.components.v1.iframe(
                get_html_display(result["interactive_code"]), 
                height=device_dims["height"],
                width=f"{device_dims['width']}px" if st.session_state.current_device != "Desktop" else "100%",
                scrolling=True
            )
            
            # Close the device frame div
            if st.session_state.current_device in ["Mobile", "Tablet"]:
                st.markdown("</div>", unsafe_allow_html=True)
    
    with code_tab:
        framework = st.session_state.current_framework
        
        # Create framework-specific code tabs
        if framework == "HTML/CSS/JS":
            html_tab, css_tab, js_tab = st.tabs(["HTML", "CSS", "JavaScript"])
            
            with html_tab:
                st.code(result["separate_code"].get("html", ""), language="html")
                st.download_button("Download HTML", result["separate_code"].get("html", ""), "index.html", "text/html")
            
            with css_tab:
                st.code(result["css_code"], language="css")
                st.download_button("Download CSS", result["css_code"], "styles.css", "text/css")
            
            with js_tab:
                st.code(result["separate_code"].get("js", ""), language="javascript")
                st.download_button("Download JavaScript", result["separate_code"].get("js", ""), "script.js", "text/javascript")
        
        elif framework == "React":
            component_tab, css_tab, other_tab = st.tabs(["React Component", "CSS/Styling", "Additional Files"])
            
            with component_tab:
                st.code(result["framework_specific_code"], language="jsx")
                st.download_button("Download Component", result["framework_specific_code"], "Component.jsx", "text/plain")
            
            with css_tab:
                st.code(result["css_code"], language="css")
                st.download_button("Download CSS", result["css_code"], "styles.css", "text/css")
            
            with other_tab:
                if result["additional_files"]:
                    for filename, content in result["additional_files"].items():
                        st.subheader(filename)
                        lang = "jsx" if filename.endswith((".jsx", ".tsx")) else "javascript"
                        st.code(content, language=lang)
                        st.download_button(f"Download {filename}", content, filename, "text/plain")
                else:
                    st.info("No additional files for this component")
        
        elif framework == "Vue.js":
            component_tab, css_tab, other_tab = st.tabs(["Vue Component", "CSS/Styling", "Additional Files"])
            
            with component_tab:
                st.code(result["framework_specific_code"], language="html")
                st.download_button("Download Component", result["framework_specific_code"], "Component.vue", "text/plain")
            
            with css_tab:
                st.code(result["css_code"], language="css")
                st.download_button("Download CSS", result["css_code"], "styles.css", "text/css")
            
            with other_tab:
                if result["additional_files"]:
                    for filename, content in result["additional_files"].items():
                        st.subheader(filename)
                        lang = "javascript" if filename.endswith(".js") else "html"
                        st.code(content, language=lang)
                        st.download_button(f"Download {filename}", content, filename, "text/plain")
                else:
                    st.info("No additional files for this component")
        
        elif framework == "Angular":
            component_tab, template_tab, css_tab, other_tab = st.tabs(["Component", "Template", "CSS/Styling", "Additional Files"])
            
            with component_tab:
                st.code(result["framework_specific_code"], language="typescript")
                st.download_button("Download Component", result["framework_specific_code"], "component.ts", "text/plain")
            
            with template_tab:
                template_code = result["separate_code"].get("html", "")
                st.code(template_code, language="html")
                st.download_button("Download Template", template_code, "component.html", "text/html")
            
            with css_tab:
                st.code(result["css_code"], language="css")
                st.download_button("Download CSS", result["css_code"], "component.css", "text/css")
            
            with other_tab:
                if result["additional_files"]:
                    for filename, content in result["additional_files"].items():
                        st.subheader(filename)
                        lang = "typescript" if filename.endswith(".ts") else "html"
                        st.code(content, language=lang)
                        st.download_button(f"Download {filename}", content, filename, "text/plain")
                else:
                    st.info("No additional files for this component")
        
        elif framework == "Svelte":
            component_tab, other_tab = st.tabs(["Svelte Component", "Additional Files"])
            
            with component_tab:
                st.code(result["framework_specific_code"], language="html")
                st.download_button("Download Component", result["framework_specific_code"], "Component.svelte", "text/plain")
            
            with other_tab:
                if result["additional_files"]:
                    for filename, content in result["additional_files"].items():
                        st.subheader(filename)
                        lang = "javascript" if filename.endswith(".js") else "html"
                        st.code(content, language=lang)
                        st.download_button(f"Download {filename}", content, filename, "text/plain")
                else:
                    st.info("No additional files for this component")
        
        # Download complete code package
        st.subheader("Download Complete Code")
        st.download_button(
            label=f"Download {framework} Package",
            data=json.dumps({
                "metadata": result["metadata"],
                "files": result["separate_code"],
                "css_code": result["css_code"],
                "framework_specific_code": result["framework_specific_code"],
                "additional_files": result["additional_files"]
            }, indent=2),
            file_name=f"codepilot_{framework.lower().replace('/', '_').replace('.', '')}_package.json",
            mime="application/json",
        )
    
    with explanation_tab:
        st.subheader("Code Explanation")
        st.write(result["explanation"])
        
        # Framework-specific notes
        st.subheader(f"{framework} Implementation Details")
        if framework == "HTML/CSS/JS":
            st.info("This implementation uses standard HTML5, CSS3, and JavaScript ES6+.")
        elif framework == "React":
            st.info("This React implementation uses functional components with hooks.")
        elif framework == "Vue.js":
            st.info("This Vue.js implementation uses Vue 3 with the Composition API.")
        elif framework == "Angular":
            st.info("This Angular implementation uses TypeScript and Angular's component architecture.")
        elif framework == "Svelte":
            st.info("This Svelte implementation uses Svelte's reactive programming model.")

# Add footer
st.markdown("---")
st.markdown("""
<footer>
    <p style="text-align: center; color: #888; font-size: 0.8em;">© 2025 CodePilot AI - Powered by Claude 3.7 Sonnet</p>
</footer>
""", unsafe_allow_html=True)

# Custom CSS for cleaner UI
st.markdown("""
<style>
    /* Clean, modern UI styling */
    .main .block-container {
        padding-top: 1rem;
    }
    
    .stButton button {
        border-radius: 4px;
        font-weight: 500;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 16px;
    }
    
    [data-testid="stCodeBlock"] {
        max-height: 500px;
    }
    
    iframe {
        border: none;
        background-color: white;
    }
    
    /* Hide fullscreen button on iframe */
    iframe[title] ~ button {
        display: none;
    }
    
    /* Better form styling */
    [data-testid="stForm"] {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)
