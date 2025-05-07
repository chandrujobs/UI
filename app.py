# app.py - Enhanced Streamlit version of CodePilot AI
import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import base64
import uuid
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

# Define device types
DEVICES = {
    "Desktop": {"width": "100%", "height": "600px"},
    "Tablet": {"width": "768px", "height": "600px"},
    "Mobile": {"width": "375px", "height": "667px"}
}

# Prompt library
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
if 'prompt_library_category' not in st.session_state:
    st.session_state.prompt_library_category = None
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False

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
                "device": device,
                "id": str(uuid.uuid4())[:8]
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

# Sidebar with settings and history
with st.sidebar:
    st.title("CodePilot AI")
    
    # Device selection
    st.subheader("Device Preview")
    device_cols = st.columns(3)
    
    for i, device in enumerate(DEVICES.keys()):
        if device_cols[i].button(device, key=f"btn_{device}", use_container_width=True):
            st.session_state.current_device = device
    
    # Framework selection
    st.subheader("Framework")
    selected_framework = st.selectbox("Select Framework", list(FRAMEWORKS.keys()), index=list(FRAMEWORKS.keys()).index(st.session_state.current_framework))
    if selected_framework != st.session_state.current_framework:
        st.session_state.current_framework = selected_framework
        if 'show_result' in st.session_state and st.session_state.show_result:
            st.warning("Please regenerate your UI with the new framework.")
    
    # Prompt Library
    st.subheader("Prompt Library")
    categories = st.radio("Categories", list(PROMPT_LIBRARY.keys()))
    
    if categories != st.session_state.prompt_library_category:
        st.session_state.prompt_library_category = categories
    
    # Show prompts for selected category
    if st.session_state.prompt_library_category:
        st.write("Sample Prompts:")
        for prompt in PROMPT_LIBRARY[st.session_state.prompt_library_category]:
            if st.button(prompt, key=f"prompt_{prompt}", use_container_width=True):
                # Set this prompt in the main text area
                st.session_state.selected_prompt = prompt
                st.session_state.form_submitted = False
    
    # History section
    if st.session_state.history:
        st.subheader("History")
        for idx, item in enumerate(st.session_state.history):
            if st.button(f"{item['prompt'][:30]}... ({item['framework']})", key=f"history_{idx}", use_container_width=True):
                st.session_state.result = item['result']
                st.session_state.show_result = True
                st.session_state.current_device = item['device']
                st.session_state.current_framework = item['framework']
                st.rerun()

# Main content area
st.title("CodePilot AI Studio")
st.markdown("Transform your ideas into professional, responsive UI with multiple framework options")

# Initialize prompt input
if 'selected_prompt' in st.session_state:
    prompt_value = st.session_state.selected_prompt
    # Clear it after using once
    del st.session_state.selected_prompt
else:
    prompt_value = ""

# Prompt input area
with st.container():
    with st.form("generation_form"):
        prompt = st.text_area("Describe the UI you want to create:", 
                              value=prompt_value,
                              placeholder="E.g., Create a modern dashboard with sidebar navigation, analytics charts, and a data table", 
                              height=100)
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Device: {st.session_state.current_device}")
        with col2:
            st.info(f"Framework: {st.session_state.current_framework}")
            
        # Generate button
        submitted = st.form_submit_button("Generate UI", type="primary", use_container_width=True)
        
        if submitted:
            st.session_state.form_submitted = True

# Handle generation
if st.session_state.form_submitted:
    if not prompt:
        st.warning("Please enter a prompt first.")
        st.session_state.form_submitted = False
    else:
        with st.spinner("Generating your professional UI and code..."):
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
                'result': result,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Add to history (limit to 10 items)
            st.session_state.history.insert(0, history_item)
            if len(st.session_state.history) > 10:
                st.session_state.history = st.session_state.history[:10]
            
            # Store result in session state
            st.session_state.result = result
            st.session_state.show_result = True
            st.session_state.form_submitted = False
            
            # Force a rerun to update the UI
            st.rerun()

# Display results if available
if 'show_result' in st.session_state and st.session_state.show_result:
    result = st.session_state.result
    
    # Create tabs for different sections
    preview_tab, code_tab, explanation_tab = st.tabs(["UI Preview", "Code", "Explanation"])
    
    with preview_tab:
        st.subheader(f"{st.session_state.current_device} Preview")
        
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
                height=int(device_dims["height"].replace("px", "")), 
                width=device_dims["width"],
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
                for filename, content in result["additional_files"].items():
                    st.subheader(filename)
                    lang = "jsx" if filename.endswith((".jsx", ".tsx")) else "javascript"
                    st.code(content, language=lang)
                    st.download_button(f"Download {filename}", content, filename, "text/plain")
        
        elif framework == "Vue.js":
            component_tab, css_tab, other_tab = st.tabs(["Vue Component", "CSS/Styling", "Additional Files"])
            
            with component_tab:
                st.code(result["framework_specific_code"], language="html")
                st.download_button("Download Component", result["framework_specific_code"], "Component.vue", "text/plain")
            
            with css_tab:
                st.code(result["css_code"], language="css")
                st.download_button("Download CSS", result["css_code"], "styles.css", "text/css")
            
            with other_tab:
                for filename, content in result["additional_files"].items():
                    st.subheader(filename)
                    lang = "javascript" if filename.endswith(".js") else "html"
                    st.code(content, language=lang)
                    st.download_button(f"Download {filename}", content, filename, "text/plain")
        
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
                for filename, content in result["additional_files"].items():
                    st.subheader(filename)
                    lang = "typescript" if filename.endswith(".ts") else "html"
                    st.code(content, language=lang)
                    st.download_button(f"Download {filename}", content, filename, "text/plain")
        
        elif framework == "Svelte":
            component_tab, other_tab = st.tabs(["Svelte Component", "Additional Files"])
            
            with component_tab:
                st.code(result["framework_specific_code"], language="html")
                st.download_button("Download Component", result["framework_specific_code"], "Component.svelte", "text/plain")
            
            with other_tab:
                for filename, content in result["additional_files"].items():
                    st.subheader(filename)
                    lang = "javascript" if filename.endswith(".js") else "html"
                    st.code(content, language=lang)
                    st.download_button(f"Download {filename}", content, filename, "text/plain")
        
        # Download complete code package
        st.subheader("Download Complete Code")
        
        # Create a JSON representation of all files
        download_package = {
            "metadata": result["metadata"],
            "files": result["separate_code"],
            "css_code": result["css_code"],
            "framework_specific_code": result["framework_specific_code"],
            "additional_files": result["additional_files"]
        }
        
        st.download_button(
            label=f"Download Complete {framework} Package",
            data=json.dumps(download_package, indent=2),
            file_name=f"codepilot_{framework.lower().replace('/', '_').replace('.', '')}_package.json",
            mime="application/json",
        )
    
    with explanation_tab:
        st.subheader("Code Explanation")
        st.write(result["explanation"])
        
        # Framework-specific notes
        st.subheader(f"{framework} Implementation Notes")
        
        if framework == "HTML/CSS/JS":
            st.write("""
            This implementation uses standard HTML5, CSS3, and JavaScript ES6+. The code can be deployed by simply including
            all three files in a directory and opening the HTML file in a browser. For production, consider minifying the
            CSS and JavaScript files for better performance.
            """)
        elif framework == "React":
            st.write("""
            This React implementation uses functional components with hooks. To use this code:
            1. Create a new React project (using Create React App or a similar tool)
            2. Create a new component file and paste the component code
            3. Import and use the component in your application
            4. Include the CSS by creating a separate CSS file or using CSS-in-JS
            """)
        elif framework == "Vue.js":
            st.write("""
            This Vue.js implementation uses Vue 3 with the Composition API. To use this code:
            1. Create a new Vue project (using Vue CLI or Vite)
            2. Create a new .vue file and paste the component code
            3. Import and register the component in your application
            4. The component includes all necessary CSS in its <style> section
            """)
        elif framework == "Angular":
            st.write("""
            This Angular implementation uses TypeScript and Angular's component architecture. To use this code:
            1. Create a new Angular project (using Angular CLI)
            2. Create a new component using ng generate component
            3. Replace the generated files with the provided code
            4. Import the component in your module and use it in your application
            """)
        elif framework == "Svelte":
            st.write("""
            This Svelte implementation uses Svelte's reactive programming model. To use this code:
            1. Create a new Svelte project (using degit or Vite)
            2. Create a new .svelte file and paste the component code
            3. Import and use the component in your application
            4. The component includes all necessary CSS in its <style> section
            """)
            
        # Device optimization notes
        st.subheader(f"{st.session_state.current_device} Optimization")
        
        if st.session_state.current_device == "Desktop":
            st.write("""
            This implementation is optimized for desktop devices with:
            - Wider layouts and more complex UI elements
            - Hover effects for interactive elements
            - Keyboard navigation support
            - Higher resolution images and more detailed content
            """)
        elif st.session_state.current_device == "Tablet":
            st.write("""
            This implementation is optimized for tablet devices with:
            - Touch-friendly UI elements with appropriate sizing
            - Responsive layouts that adapt to portrait and landscape orientations
            - Simplified navigation for touch interfaces
            - Optimized for medium-sized screens (768px width)
            """)
        elif st.session_state.current_device == "Mobile":
            st.write("""
            This implementation is optimized for mobile devices with:
            - Touch-first interface with larger interactive elements
            - Simplified single-column layouts
            - Collapsible/expandable sections to save vertical space
            - Optimized for narrow screens (375px width)
            - Performance optimizations for mobile browsers
            """)

# Add footer
st.markdown("---")
st.markdown("""
<footer>
    <p style="text-align: center; color: #888; font-size: 0.8em;">© 2025 CodePilot AI - Powered by Claude 3.7 Sonnet</p>
</footer>
""", unsafe_allow_html=True)

# Custom CSS for better styling
st.markdown("""
<style>
    /* General styling */
    .main .block-container {
        padding-top: 2rem;
    }
    
    /* Buttons */
    .stButton button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding: 10px 16px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4a6cf7;
        color: white;
    }
    
    /* Form styling */
    [data-testid="stForm"] {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    .stTextArea textarea {
        border-radius: 6px;
    }
    
    /* Device preview styling */
    iframe {
        border: none;
        background-color: white;
        transition: all 0.3s ease;
    }
    
    /* Code block styling */
    [data-testid="stCodeBlock"] {
        border-radius: 6px;
        max-height: 600px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #333;
    }
    
    h1 {
        font-weight: 800;
        color: #4a6cf7;
    }
    
    h2 {
        font-weight: 700;
    }
    
    h3 {
        font-weight: 600;
    }
    
    /* Info box */
    .stAlert {
        border-radius: 6px;
        padding: 2px 16px;
    }
</style>
""", unsafe_allow_html=True)
