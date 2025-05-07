// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const promptForm = document.getElementById('prompt-form');
    const promptInput = document.getElementById('prompt-input');
    const generateBtn = document.getElementById('generate-btn');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    const uiPreview = document.getElementById('ui-preview');
    const htmlCode = document.getElementById('html-code');
    const cssCode = document.getElementById('css-code');
    const jsCode = document.getElementById('js-code');
    const explanationContent = document.getElementById('explanation-content');

    // Tab functionality
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons and contents
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(`${tabId}-content`).classList.add('active');
        });
    });

    // Copy button functionality
    const copyBtns = document.querySelectorAll('.copy-btn');
    
    copyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const codeElement = document.getElementById(targetId);
            const textToCopy = codeElement.textContent;
            
            // Copy to clipboard
            navigator.clipboard.writeText(textToCopy).then(() => {
                btn.textContent = 'Copied!';
                btn.classList.add('copied');
                
                // Reset button after 2 seconds
                setTimeout(() => {
                    btn.textContent = 'Copy';
                    btn.classList.remove('copied');
                }, 2000);
            });
        });
    });

    // Form submission
    promptForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const prompt = promptInput.value.trim();
        if (!prompt) return;
        
        // Show loading, hide results
        loadingSection.style.display = 'block';
        resultsSection.style.display = 'none';
        generateBtn.disabled = true;
        
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt }),
            });
            
            if (!response.ok) {
                throw new Error('Failed to generate code');
            }
            
            const data = await response.json();
            const result = JSON.parse(data.result);
            
            // Update UI with generated code
            displayResults(result);
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while generating code. Please try again.');
        } finally {
            loadingSection.style.display = 'none';
            generateBtn.disabled = false;
        }
    });

    // Function to display results
    function displayResults(result) {
        // Set the HTML/CSS/JS code sections
        htmlCode.textContent = result.html_code;
        cssCode.textContent = result.css_code;
        jsCode.textContent = result.js_code;
        
        // Set the explanation
        explanationContent.innerHTML = result.explanation;
        
        // Set the UI preview
        uiPreview.innerHTML = result.interactive_code;
        
        // Execute any JavaScript in the preview
        const scriptTags = uiPreview.querySelectorAll('script');
        scriptTags.forEach(scriptTag => {
            const newScript = document.createElement('script');
            
            // Copy all attributes
            Array.from(scriptTag.attributes).forEach(attr => {
                newScript.setAttribute(attr.name, attr.value);
            });
            
            // Set the script content
            newScript.textContent = scriptTag.textContent;
            
            // Replace the old script tag with the new one
            scriptTag.parentNode.replaceChild(newScript, scriptTag);
        });
        
        // Apply syntax highlighting
        hljs.highlightAll();
        
        // Show results section
        resultsSection.style.display = 'block';
    }
});
