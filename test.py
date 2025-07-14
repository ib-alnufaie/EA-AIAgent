import streamlit as st
import pandas as pd
from PIL import Image
import os
import json
from datetime import datetime           
from pyvis.network import Network
import time
import base64
from io import BytesIO

# --- Performance Optimization ---
# Use session state for caching to reduce recomputation
@st.cache_data(ttl=3600)  
def load_excel_data(file):
    return pd.read_excel(file)


@st.cache_data(ttl=3600)
def process_image_ocr(image):
    return pytesseract.image_to_string(image)


@st.cache_data(ttl=3600)
def create_network_graph(data):
    G = nx.DiGraph()
    for app in data:
        app_name = app.get("application_name")
        dependencies = app.get("depends_on", [])
        G.add_node(app_name)
        for dep in dependencies:
            if dep:  # Skip empty dependencies
                G.add_edge(app_name, dep)
    return G


# Function to get base64 encoded image for smooth loading
def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# --- Config ---
st.set_page_config(
    page_title="Agent-AI² Assistant",
    layout="wide",
    initial_sidebar_state="collapsed",  # Collapse sidebar for more space
)

# --- State ---
if "current_product" not in st.session_state:
    st.session_state.current_product = None

if "interview_index" not in st.session_state:
    st.session_state.interview_index = 0
if "interview_answers" not in st.session_state:
    st.session_state.interview_answers = {}
if "interview_active" not in st.session_state:
    st.session_state.interview_active = False
if "interview_complete" not in st.session_state:
    st.session_state.interview_complete = False

# For OCR product
if "ocr_text" not in st.session_state:
    st.session_state.ocr_text = ""

# For Excel import product
if "excel_df" not in st.session_state:
    st.session_state.excel_df = None

# For governance & mapping & roadmap data - simple dictionary holders
if "governance_scores" not in st.session_state:
    st.session_state.governance_scores = {}
if "mapping_result" not in st.session_state:
    st.session_state.mapping_result = {}
if "roadmap_result" not in st.session_state:
    st.session_state.roadmap_result = {}

# For file uploads in all products
if "screenshot_uploads" not in st.session_state:
    st.session_state.screenshot_uploads = {}
if "excel_uploads" not in st.session_state:
    st.session_state.excel_uploads = {}

# For smooth transitions
if "page_load_time" not in st.session_state:
    st.session_state.page_load_time = time.time()

# --- CSS styles with smooth animations ---
st.markdown(
    """
<style>
/* Base styles */
body {
    background-color: #f9f9f9;
    font-family: 'Segoe UI', sans-serif;
    transition: all 0.3s ease;
}

/* Smooth loading animation */
.stApp {
    opacity: 0;
    animation: fadeIn 0.5s ease-in-out forwards;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* Title styling with gradient animation */
.title-red {
    background: linear-gradient(to right, #d00000, #9b0000);
    background-size: 200% 200%;
    animation: gradientShift 8s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    font-weight: 900;
    text-align: center;
    margin-top: 0.2em;
    margin-bottom: 0.5em;
    font-family: 'Segoe UI', sans-serif;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}


/* Navbar with subtle shadow animation */
.navbar {
    background-color: #e0e0e0;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #ccc;
    margin-bottom: 2rem;
    font-family: 'Segoe UI', sans-serif;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: box-shadow 0.3s ease;
}

.navbar:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.nav-links {
    display: flex;
    gap: 1.5rem;
}

.nav-links a {
    font-weight: 600;
    color: #333;
    text-decoration: none;
    font-size: 1.1rem;
    position: relative;
    transition: color 0.3s ease;
}

.nav-links a:after {
    content: '';
    position: absolute;
    width: 0;
    height: 2px;
    bottom: -4px;
    left: 0;
    background-color: #d00000;
    transition: width 0.3s ease;
}

.nav-links a:hover {
    color: #d00000;
}

.nav-links a:hover:after {
    width: 100%;
}

/* Products container with smooth layout */
.products-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    opacity: 0;
    transform: translateY(20px);
    animation: slideUp 0.5s ease forwards;
    animation-delay: 0.2s;
}

@keyframes slideUp {
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.products-row {
    display: flex;
    flex-wrap: nowrap;
    justify-content: space-between;
    margin-bottom: 20px;
    gap: 20px;
}

/* Product cards with smooth hover effects */
.product-card {
    background: white;
    border-radius: 12px;
    width: calc(25% - 15px);
    padding: 20px;
    box-shadow: 0 3px 8px rgba(0,0,0,0.08);
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;
    min-height: 200px;
    position: relative;
    overflow: hidden;
}

.product-card:before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 0;
    background: linear-gradient(to bottom, rgba(208,0,0,0.05), transparent);
    transition: height 0.3s ease;
}

.product-card:hover {
    box-shadow: 0 10px 20px rgba(208,0,0,0.2);
    transform: translateY(-5px);
}

.product-card:hover:before {
    height: 100%;
}

.product-title {
    color: #d00000;
    font-weight: 700;
    font-size: 1.3rem;
    margin-bottom: 10px;
    position: relative;
    transition: transform 0.3s ease;
}

.product-card:hover .product-title {
    transform: translateY(-2px);
}

.product-desc {
    font-size: 1rem;
    color: #555;
    height: 80px;
    overflow: hidden;
    position: relative;
    transition: color 0.3s ease;
}

.product-card:hover .product-desc {
    color: #333;
}

/* Button styling with smooth transitions */
.button-row {
    margin-top: 20px;
    display: flex;
    justify-content: space-between;
}

.button-primary {
    background-color: #d00000;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.button-primary:after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 5px;
    height: 5px;
    background: rgba(255, 255, 255, 0.5);
    opacity: 0;
    border-radius: 100%;
    transform: scale(1, 1) translate(-50%);
    transform-origin: 50% 50%;
}

.button-primary:hover {
    background-color: #9b0000;
    transform: scale(1.02);
}

.button-primary:focus:not(:active)::after {
    animation: ripple 1s ease-out;
}

@keyframes ripple {
    0% {
        transform: scale(0, 0);
        opacity: 0.5;
    }
    100% {
        transform: scale(20, 20);
        opacity: 0;
    }
}

.button-secondary {
    background-color: #f0f0f0;
    color: #333;
    border: 1px solid #ccc;
    padding: 10px 15px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s ease;
}

.button-secondary:hover {
    background-color: #e0e0e0;
    transform: scale(1.02);
}

/* Step box with subtle animation */
.step-box {
    border-left: 4px solid #d00000;
    background-color: #fff4f4;
    padding: 15px 20px;
    margin-bottom: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    transition: all 0.3s ease;
    animation: fadeInLeft 0.5s ease;
}

.step-box:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    transform: translateX(3px);
}

@keyframes fadeInLeft {
    from {
        opacity: 0;
        transform: translateX(-10px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Upload section with smooth transitions */
.upload-section {
    background-color: #f5f5f5;
    border-radius: 8px;
    padding: 15px;
    margin: 20px 0;
    border: 1px solid #e0e0e0;
    transition: all 0.3s ease;
    animation: fadeIn 0.5s ease;
}

.upload-section:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    border-color: #ccc;
}

.upload-title {
    font-weight: 600;
    color: #333;
    margin-bottom: 10px;
    position: relative;
    padding-left: 15px;
}

.upload-title:before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 8px;
    height: 8px;
    background-color: #d00000;
    border-radius: 50%;
}

.file-preview {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 10px;
    margin-top: 10px;
    transition: all 0.3s ease;
}

.file-preview:hover {
    border-color: #d00000;
    box-shadow: 0 2px 5px rgba(208,0,0,0.1);
}

/* Big start interview button styling with pulse animation */
.big-button {
    background-color: #d00000;
    color: white;
    font-size: 1.8rem;
    font-weight: 700;
    padding: 20px 0;
    border-radius: 12px;
    width: 300px;
    margin: 20px auto;
    display: block;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: center;
    position: relative;
    overflow: hidden;
    animation: pulse 2s infinite;
}

.big-button:hover {
    background-color: #9b0000;
    transform: scale(1.03);
    animation: none;
    box-shadow: 0 6px 12px rgba(208,0,0,0.3);
}

@keyframes pulse {
    0% {
        box-shadow: 0 0 0 0 rgba(208, 0, 0, 0.4);
    }
    70% {
        box-shadow: 0 0 0 10px rgba(208, 0, 0, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(208, 0, 0, 0);
    }
}

/* Smooth loading spinner */
.loading-spinner {
    display: inline-block;
    width: 50px;
    height: 50px;
    border: 3px solid rgba(208,0,0,0.3);
    border-radius: 50%;
    border-top-color: #d00000;
    animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Responsive adjustments with smooth transitions */
@media (max-width: 1200px) {
    .products-row {
        flex-wrap: wrap;
    }
    .product-card {
        width: calc(50% - 10px);
        margin-bottom: 20px;
        transition: width 0.3s ease, margin 0.3s ease;
    }
}

@media (max-width: 600px) {
    .product-card {
        width: 100%;
        transition: width 0.3s ease;
    }
    .title-red {
        font-size: 2.5rem;
    }
}

/* Streamlit element customizations */
.stButton > button {
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: scale(1.02) !important;
}

/* Custom scrollbar for smoother scrolling */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: #d00000;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #9b0000;
}

/* Animation keyframes for dynamic elements */
@keyframes growWidth {
    from { width: 0%; }
    to { width: 100%; }
}

@keyframes slideToPosition {
    from { left: 0%; }
    to { left: 100%; }
}
</style>

<script>
// Smooth page transitions
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // Smooth loading of elements
    const animateElements = () => {
        const elements = document.querySelectorAll('.product-card, .step-box, .upload-section');
        elements.forEach((element, index) => {
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, 100 * index);
        });
    };
    
    // Call animation function
    setTimeout(animateElements, 300);
});
</script>
""",
    unsafe_allow_html=True,
)

# --- Navbar with smooth animation ---
st.markdown(
    """
<div class="navbar">
    <div class="title-red"Agent-AI²</div>
    <div class="nav-links">
        <a href="#home">Home</a>
        <a href="#products">Products</a>
        <a href="#about">About</a>
        <a href="#contact">Contact</a>
        <a href="#support">Support</a>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# --- Title with animation ---
st.markdown(
    "<h1 class='title-red' id='home'>agent-AI² – Enterprise Architecture Assistant</h1>",
    unsafe_allow_html=True,
)

# --- Product data ---
products_info = {
    "Interview Capture": "Conduct structured interviews to capture precise application and architecture data.",
    "Diagram Intelligence": "Extract data automatically from uploaded architecture diagrams using OCR.",
    "Excel Data Import": "Import and profile application data from existing Excel sheets.",
    "Risk & Health Evaluation": "Evaluate risk levels, operational status, and generate recommendations.",
    "Governance & Compliance Dashboard": "Visualize completeness and compliance with governance frameworks.",
    "Auto-Mapping": "Map applications to TOGAF/NORA layers automatically.",
    "Modernization Roadmap Generator": "Generate tailored modernization roadmaps from data.",
    "Dependency Visualization": "Visualize application dependencies via interactive graphs.",
}

# Universal file upload component with smooth animations
def file_upload_section(product_name):
    st.markdown(f"<div class='upload-section'>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='upload-title'>File Uploads for {product_name}</div>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### Screenshot Upload")
        screenshot = st.file_uploader(
            f"Upload Screenshot for {product_name}",
            type=["png", "jpg", "jpeg"],
            key=f"screenshot_{product_name}",
        )
        if screenshot:
            # Show loading spinner while processing
            with st.spinner("Processing image..."):
                st.session_state.screenshot_uploads[product_name] = screenshot
                image = Image.open(screenshot)
                st.image(
                    image,
                    caption=f"Screenshot for {product_name}",
                    use_column_width=True,
                )

    with col2:
        st.markdown("##### Excel File Upload")
        excel_file = st.file_uploader(
            f"Upload Excel File for {product_name}",
            type=["xlsx", "xls"],
            key=f"excel_{product_name}",
        )
        if excel_file:
            # Show loading spinner while processing
            with st.spinner("Processing Excel file..."):
                st.session_state.excel_uploads[product_name] = excel_file
                try:
                    # Use cached function for better performance
                    df = load_excel_data(excel_file)
                    st.dataframe(df.head(5))
                    st.markdown(
                        f"<div class='file-preview'>Excel file loaded: {excel_file.name} ({len(df)} rows)</div>",
                        unsafe_allow_html=True,
                    )
                except Exception as e:
                    st.error(f"Error reading Excel file: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


def show_products_grid():
    st.markdown('<div class="products-container">', unsafe_allow_html=True)

    # Split products into rows of 4
    products_list = list(products_info.items())
    for i in range(0, len(products_list), 4):
        st.markdown('<div class="products-row">', unsafe_allow_html=True)

        # Get current row of products (up to 4)
        row_products = products_list[i : i + 4]

        # Fill in any missing slots to ensure 4 per row
        while len(row_products) < 4:
            row_products.append(("", ""))

        # Display each product in the row
        for idx, (prod, desc) in enumerate(row_products):
            if prod:  # Only create clickable cards for real products
                # Create a unique key for each product button
                button_key = f"btn_{prod}_{idx}"

                product_html = f"""
                <div class="product-card" onclick="document.getElementById('{button_key}').click()">
                    <div class="product-title">{prod}</div>
                    <div class="product-desc">{desc}</div>
                    <div style="text-align: right; margin-top: 10px;">
                        <span style="color: #d00000; font-weight: 600;">Learn More →</span>
                    </div>
                </div>
                """
                st.markdown(product_html, unsafe_allow_html=True)

                # Hidden button for Streamlit to handle the click
                if st.button(
                    f"Select {prod}", key=button_key, help=f"Click to use {prod}"
                ):
                    # Add a small delay for smoother transition
                    with st.spinner(f"Loading {prod}..."):
                        time.sleep(0.3)  # Small delay for visual smoothness
                        st.session_state.current_product = prod
                        # Reset states for interview if switching
                        if prod == "Interview Capture":
                            st.session_state.interview_active = True
                            st.session_state.interview_index = 0
                            st.session_state.interview_answers = {}
                            st.session_state.interview_complete = False
                        else:
                            st.session_state.interview_active = False
                        st.experimental_rerun()
            else:  # Empty placeholder to maintain grid
                st.markdown(
                    '<div class="product-card" style="visibility: hidden;"></div>',
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# --- Home or selected product with smooth transitions ---
if st.session_state.current_product is None:
    st.markdown("## Select a product to start:")
    show_products_grid()

    # Big red Start Interview button below the grid with animation
    start_interview_key = "start_interview_button_main"
    st.markdown(
        f"""
    <div class="big-button" onclick="document.getElementById('{start_interview_key}').click();">
        📝 Start Interview
    </div>
    """,
        unsafe_allow_html=True,
    )

    if st.button("Start Interview", key=start_interview_key):
        # Add a small delay for smoother transition
        with st.spinner("Starting interview..."):
            time.sleep(0.5)  # Small delay for visual smoothness
            st.session_state.current_product = "Interview Capture"
            st.session_state.interview_active = True
            st.session_state.interview_index = 0
            st.session_state.interview_answers = {}
            st.session_state.interview_complete = False
            st.experimental_rerun()

else:
    # Show Back button with smooth transition
    col1, col2 = st.columns([1, 5])
    with col1:
        back_button_key = "back_to_products_button"
        if st.button("⬅️ Back to Products", key=back_button_key):
            # Add a small delay for smoother transition
            with st.spinner("Returning to products..."):
                time.sleep(0.3)  # Small delay for visual smoothness
                st.session_state.current_product = None
                st.experimental_rerun()

    with col2:
        product = st.session_state.current_product
        st.markdown(f"## {product}")

    # --- Interview Capture with smooth animations ---
    if product == "Interview Capture":
        if not st.session_state.interview_active:
            start_interview_btn_key = "start_interview_btn_page"
            st.markdown(
                f"""
            <div class="big-button" onclick="document.getElementById('{start_interview_btn_key}').click();">
                Start Interview
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button("Start Interview", key=start_interview_btn_key):
                # Add a small delay for smoother transition
                with st.spinner("Preparing interview..."):
                    time.sleep(0.3)  # Small delay for visual smoothness
                    st.session_state.interview_active = True
                    st.session_state.interview_index = 0
                    st.session_state.interview_answers = {}
                    st.session_state.interview_complete = False
                    st.experimental_rerun()

        if (
            st.session_state.interview_active
            and not st.session_state.interview_complete
        ):
            st.markdown(
                f'<div class="step-box"><b>Step {st.session_state.interview_index + 1} of 3:</b> Answer the following question</div>',
                unsafe_allow_html=True,
            )
            questions = [
                {
                    "field": "application_name",
                    "question": "What is the Application Name?",
                    "options": [],
                },
                {
                    "field": "category",
                    "question": "Category Type?",
                    "options": ["Core", "Support", "Integration", "Other"],
                },
                {
                    "field": "status",
                    "question": "Application Status?",
                    "options": ["Active", "Retired", "On Hold", "Other"],
                },
            ]
            idx = st.session_state.interview_index
            q = questions[idx]

            answer = None
            if q["options"]:
                choice = st.radio(q["question"], q["options"], key=f"q_{q['field']}")
                if choice == "Other":
                    answer = st.text_input("Please specify:", key=f"input_{q['field']}")
                else:
                    answer = choice
            else:
                answer = st.text_input(q["question"], key=f"input_{q['field']}")

            col1, col2 = st.columns([1, 5])
            with col1:
                submit_answer_key = f"submit_answer_{idx}"
                if st.button("Submit Answer", key=submit_answer_key, type="primary"):
                    if answer and answer.strip():
                        # Add a small delay for smoother transition
                        with st.spinner("Processing answer..."):
                            time.sleep(0.3)  # Small delay for visual smoothness
                            st.session_state.interview_answers[
                                q["field"]
                            ] = answer.strip()
                            st.session_state.interview_index += 1
                            if st.session_state.interview_index >= len(questions):
                                st.session_state.interview_complete = True
                                st.success(
                                    "Interview complete! Review your answers below."
                                )
                            st.experimental_rerun()
                    else:
                        st.error("Please provide an answer before submitting.")

        if st.session_state.interview_complete:
            # Add animation for completed interview
            st.markdown(
                """
            <div style="animation: fadeIn 0.5s ease;">
                <h3>Interview Answers:</h3>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.json(st.session_state.interview_answers)

            # Risk analysis with smooth animation
            status = st.session_state.interview_answers.get("status", "").lower()
            category = st.session_state.interview_answers.get("category", "").lower()
            risks, comments = [], []

            if status == "on hold":
                risks.append("High Risk")
                comments.append("Review business and technical dependencies.")
            elif status == "retired":
                risks.append("Decommissioned")
                comments.append("No active dependencies should exist.")
            else:
                risks.append("Active")
                comments.append("System is currently operational.")

            if category == "core":
                comments.append("Ensure high availability and strict SLAs.")
            elif category == "integration":
                comments.append("Test all integration endpoints regularly.")

            st.markdown(
                """
            <div style="animation: fadeInLeft 0.5s ease; animation-delay: 0.2s; opacity: 0;">
                <strong>Risk Level:</strong> {0}
            </div>
            """.format(
                    ", ".join(risks)
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                """
            <div style="animation: fadeInLeft 0.5s ease; animation-delay: 0.4s; opacity: 0;">
                <strong>Comments:</strong>
            </div>
            """,
                unsafe_allow_html=True,
            )

            for i, cmt in enumerate(comments):
                st.markdown(
                    f"""
                <div style="animation: fadeInLeft 0.5s ease; animation-delay: {0.5 + i*0.1}s; opacity: 0;">
                    - {cmt}
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Completion bar with animation
            total = len(questions)
            filled = len(st.session_state.interview_answers)
            percent = int((filled / total) * 100)

            # Create a dynamic progress bar with CSS
            progress_width = f"{percent}%"
            st.markdown(
                f"""
            <div style="animation: fadeIn 0.5s ease; animation-delay: 0.7s; opacity: 0;">
                <div style="background-color: #f0f0f0; border-radius: 5px; height: 20px; width: 100%; margin: 20px 0;">
                    <div style="background-color: #d00000; border-radius: 5px; height: 20px; width: {progress_width}; 
                         animation: growWidth 1s ease-out;">
                        <div style="color: white; text-align: center; font-size: 12px; line-height: 20px;">
                            {percent}% Complete
                        </div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                download_key = "download_interview_results"
                if st.download_button(
                    "Download Interview Results as JSON",
                    json.dumps(st.session_state.interview_answers, indent=2),
                    file_name="Interview_Results.json",
                    mime="application/json",
                    key=download_key,
                ):
                    st.success("Downloaded!")

            # Offer to continue with other products
            st.markdown(
                """
            <div style="animation: fadeIn 0.5s ease; animation-delay: 0.9s; opacity: 0;">
                <hr style="margin: 30px 0;">
                <h3>Continue with another product using interview data:</h3>
            </div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                risk_eval_key = "risk_eval_button"
                if st.button(
                    "Risk & Health Evaluation", key=risk_eval_key, type="primary"
                ):
                    with st.spinner("Loading Risk & Health Evaluation..."):
                        time.sleep(0.3)  # Small delay for visual smoothness
                        st.session_state.current_product = "Risk & Health Evaluation"
                        st.experimental_rerun()
            with col2:
                roadmap_key = "roadmap_button"
                if st.button(
                    "Modernization Roadmap Generator", key=roadmap_key, type="primary"
                ):
                    with st.spinner("Loading Modernization Roadmap Generator..."):
                        time.sleep(0.3)  # Small delay for visual smoothness
                        st.session_state.current_product = (
                            "Modernization Roadmap Generator"
                        )
                        st.experimental_rerun()

        # Add universal file upload section
        file_upload_section(product)

    # --- Diagram Intelligence with smooth animations ---
    elif product == "Diagram Intelligence":
        st.markdown(
            """
        <div style="animation: fadeIn 0.5s ease;">
            <h3>Extract data from architecture diagrams</h3>
            <p>Upload an architecture diagram to automatically extract text and information using OCR technology.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Add universal file upload section first
        file_upload_section(product)

        # Additional diagram-specific functionality
        if product in st.session_state.screenshot_uploads:
            image = st.session_state.screenshot_uploads[product]

            # Process the image with OCR
            try:
                with st.spinner("Processing image with OCR..."):
                    image_pil = Image.open(image)
                    # Use cached function for better performance
                    extracted_text = process_image_ocr(image_pil)

                    st.markdown(
                        """
                    <div style="animation: fadeIn 0.5s ease;">
                        <h4>Extracted Text</h4>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.text_area(
                        "Extracted Text from Diagram", extracted_text, height=200
                    )

                    save_text_key = "save_extracted_text"
                    if st.button(
                        "Save Extracted Text", key=save_text_key, type="primary"
                    ):
                        with st.spinner("Saving extracted text..."):
                            os.makedirs("extracted_texts", exist_ok=True)
                            filename = f"extracted_texts/diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write(extracted_text)
                            st.success(f"Extracted text saved to {filename}")
            except Exception as e:
                st.error(f"Error processing image: {e}")

    # --- Excel Data Import with smooth animations ---
    elif product == "Excel Data Import":
        st.markdown(
            """
        <div style="animation: fadeIn 0.5s ease;">
            <h3>Import and analyze application data from Excel</h3>
            <p>Upload an Excel file containing application data to automatically profile and convert to JSON format.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Add universal file upload section
        file_upload_section(product)

        # Additional Excel-specific functionality
        if product in st.session_state.excel_uploads:
            excel_file = st.session_state.excel_uploads[product]

            try:
                with st.spinner("Processing Excel data..."):
                    # Use cached function for better performance
                    df = load_excel_data(excel_file)

                    # Show full dataframe with animation
                    st.markdown(
                        """
                    <div style="animation: fadeIn 0.5s ease; animation-delay: 0.2s; opacity: 0;">
                        <h3>Excel Data Preview</h3>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.dataframe(df)

                    # Generate and show JSON preview with animation
                    st.markdown(
                        """
                    <div style="animation: fadeIn 0.5s ease; animation-delay: 0.4s; opacity: 0;">
                        <h3>JSON Conversion Preview</h3>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    json_preview = df.to_json(orient="records", indent=2)
                    st.code(json_preview, language="json")

                    # Save option with animation
                    st.markdown(
                        """
                    <div style="animation: fadeIn 0.5s ease; animation-delay: 0.6s; opacity: 0;">
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    save_json_key = "save_json_profile"
                    if st.button(
                        "Save JSON Profile", key=save_json_key, type="primary"
                    ):
                        with st.spinner("Saving JSON profile..."):
                            time.sleep(0.3)  # Small delay for visual smoothness
                            os.makedirs("catalogues", exist_ok=True)
                            path = f"catalogues/appdata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            with open(path, "w", encoding="utf-8") as f:
                                f.write(json_preview)
                            st.success(f"Saved to {path}")

                    # Basic statistics with animation
                    st.markdown(
                        """
                    <div style="animation: fadeIn 0.5s ease; animation-delay: 0.8s; opacity: 0;">
                        <h3>Data Statistics</h3>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Records", len(df))
                    with col2:
                        st.metric("Total Columns", len(df.columns))

                    st.write(f"Columns: {', '.join(df.columns)}")

            except Exception as e:
                st.error(f"Error processing Excel file: {e}")

    # --- Risk & Health Evaluation with smooth animations ---
    elif product == "Risk & Health Evaluation":
        st.markdown(
            """
        <div style="animation: fadeIn 0.5s ease;">
            <h3>Evaluate application risk and health status</h3>
            <p>Assess the risk level and operational health of your applications based on key parameters.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Pre-fill from interview if available
        pre_status = st.session_state.interview_answers.get("status", "Active")
        pre_category = st.session_state.interview_answers.get("category", "Core")

        col1, col2 = st.columns(2)
        with col1:
            status_options = ["Active", "Retired", "On Hold", "Other"]
            try:
                status_index = status_options.index(pre_status)
            except ValueError:
                status_index = 0
            status = st.selectbox(
                "Application Status", status_options, index=status_index
            )

        with col2:
            category_options = ["Core", "Support", "Integration", "Other"]
            try:
                category_index = category_options.index(pre_category)
            except ValueError:
                category_index = 0
            category = st.selectbox(
                "Category Type", category_options, index=category_index
            )

        evaluate_risk_key = "evaluate_risk_button"
        if st.button("Evaluate Risk & Health", key=evaluate_risk_key, type="primary"):
            with st.spinner("Evaluating risk and health..."):
                time.sleep(0.5)  # Small delay for visual smoothness

                risks = []
                comments = []
                s = status.lower()
                c = category.lower()

                if s == "on hold":
                    risks.append("High Risk")
                    comments.append("Review dependencies and business value.")
                elif s == "retired":
                    risks.append("Decommissioned")
                    comments.append("Confirm no active links.")
                else:
                    risks.append("Active")
                    comments.append("Operating normally.")

                if c == "core":
                    comments.append("High availability required.")
                elif c == "integration":
                    comments.append("Test integration points.")

                # Display results with animations
                st.markdown(
                    """
                <div style="animation: fadeIn 0.5s ease;">
                    <h3>Risk Assessment Results</h3>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f"""
                <div style="animation: fadeInLeft 0.5s ease; animation-delay: 0.2s; opacity: 0;">
                    <strong>Risk Level:</strong> {', '.join(risks)}
                </div>
                """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    """
                <div style="animation: fadeInLeft 0.5s ease; animation-delay: 0.4s; opacity: 0;">
                    <strong>Comments:</strong>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                for i, cmt in enumerate(comments):
                    st.markdown(
                        f"""
                    <div style="animation: fadeInLeft 0.5s ease; animation-delay: {0.5 + i*0.1}s; opacity: 0;">
                        - {cmt}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                # Risk visualization with animation
                st.markdown(
                    """
                <div style="animation: fadeIn 0.5s ease; animation-delay: 0.8s; opacity: 0;">
                    <h3>Risk Visualization</h3>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                risk_level = 0
                if "high risk" in [r.lower() for r in risks]:
                    risk_level = 80
                elif "decommissioned" in [r.lower() for r in risks]:
                    risk_level = 30
                else:
                    risk_level = 20

                # Animated risk gauge with fixed CSS (no f-strings)
                risk_position = str(risk_level) + "%"
                st.markdown(
                    f"""
                <div style="animation: fadeIn 0.5s ease; animation-delay: 1s; opacity: 0;">
                    <div style="background-color: #f0f0f0; border-radius: 5px; height: 30px; width: 100%; margin: 20px 0;">
                        <div style="background: linear-gradient(to right, green, yellow, red); border-radius: 5px; height: 30px; width: 100%;">
                            <div style="position: relative; height: 100%;">
                                <div style="position: absolute; top: -10px; left: {risk_position}; transform: translateX(-50%); 
                                     width: 20px; height: 50px; background-color: #333; border-radius: 3px;
                                     animation: slideToPosition 1.5s ease-out;">
                                </div>
                                <div style="position: absolute; bottom: -25px; left: 0%; transform: translateX(-50%);">Low</div>
                                <div style="position: absolute; bottom: -25px; left: 50%; transform: translateX(-50%);">Medium</div>
                                <div style="position: absolute; bottom: -25px; left: 100%; transform: translateX(-50%);">High</div>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        # Add universal file upload section
        file_upload_section(product)

    # --- Governance & Compliance Dashboard with smooth animations ---
    elif product == "Governance & Compliance Dashboard":
        st.markdown(
            """
        <div style="animation: fadeIn 0.5s ease;">
            <h3>Visualize governance compliance scores</h3>
            <p>Upload governance scores to generate compliance dashboards and visualizations.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Add universal file upload section
        file_upload_section(product)

        # Additional governance-specific functionality
        if product in st.session_state.excel_uploads:
            excel_file = st.session_state.excel_uploads[product]

            try:
                with st.spinner("Processing governance data..."):
                    # Use cached function for better performance
                    df = load_excel_data(excel_file)

                    # Convert first two columns to governance scores dictionary
                    if len(df.columns) >= 2:
                        governance_data = {}
                        for _, row in df.iterrows():
                            governance_data[str(row[0])] = float(row[1])

                        st.session_state.governance_scores = governance_data

                        # Display the data with animation
                        st.markdown(
                            """
                        <div style="animation: fadeIn 0.5s ease; animation-delay: 0.2s; opacity: 0;">
                            <h3>Governance Scores</h3>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        st.json(governance_data)

                        # Plot bar chart with animation
                        st.markdown(
                            """
                        <div style="animation: fadeIn 0.5s ease; animation-delay: 0.4s; opacity: 0;">
                            <h3>Compliance Visualization</h3>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        keys = list(governance_data.keys())
                        values = [governance_data[k] for k in keys]

                        fig, ax = plt.subplots(figsize=(10, 5))
                        bars = ax.bar(keys, values, color="#d00000")
                        ax.set_ylim(0, 100)
                        ax.set_ylabel("Score (%)")
                        ax.set_title("Governance Compliance Scores")

                        # Add value labels on top of bars
                        for bar in bars:
                            height = bar.get_height()
                            ax.text(
                                bar.get_x() + bar.get_width() / 2.0,
                                height + 2,
                                f"{height:.1f}%",
                                ha="center",
                                va="bottom",
                            )

                        st.pyplot(fig)

                        # Compliance summary with animation
                        avg_score = sum(values) / len(values)

                        st.markdown(
                            f"""
                        <div style="animation: fadeIn 0.5s ease; animation-delay: 0.6s; opacity: 0;">
                            <h3>Overall Compliance: {avg_score:.1f}%</h3>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        if avg_score >= 80:
                            st.success("High compliance level achieved")
                        elif avg_score >= 60:
                            st.warning(
                                "Moderate compliance level - improvements needed"
                            )
                        else:
                            st.error("Low compliance level - immediate action required")

                        # Animated compliance gauge with fixed CSS (no f-strings)
                        avg_position = str(avg_score) + "%"
                        st.markdown(
                            f"""
                        <div style="animation: fadeIn 0.5s ease; animation-delay: 0.8s; opacity: 0;">
                            <div style="background-color: #f0f0f0; border-radius: 5px; height: 30px; width: 100%; margin: 20px 0;">
                                <div style="background: linear-gradient(to right, red, yellow, green); border-radius: 5px; height: 30px; width: 100%;">
                                    <div style="position: relative; height: 100%;">
                                        <div style="position: absolute; top: -10px; left: {avg_position}; transform: translateX(-50%); 
                                             width: 20px; height: 50px; background-color: #333; border-radius: 3px;
                                             animation: slideToPosition 1.5s ease-out;">
                                        </div>
                                        <div style="position: absolute; bottom: -25px; left: 0%; transform: translateX(-50%);">0%</div>
                                        <div style="position: absolute; bottom: -25px; left: 50%; transform: translateX(-50%);">50%</div>
                                        <div style="position: absolute; bottom: -25px; left: 100%; transform: translateX(-50%);">100%</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                    else:
                        st.error(
                            "Excel file must have at least two columns (Category and Score)"
                        )

            except Exception as e:
                st.error(f"Error processing governance data: {e}")

    # --- Auto-Mapping with smooth animations ---
    elif product == "Auto-Mapping":
        st.markdown(
            """
        <div style="animation: fadeIn 0.5s ease;">
            <h3>Automatically map applications to architecture layers</h3>
            <p>Upload application metadata to automatically map to TOGAF/NORA architecture layers.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Add universal file upload section
        file_upload_section(product)

        # Additional mapping-specific functionality
        if product in st.session_state.excel_uploads:
            excel_file = st.session_state.excel_uploads[product]

            try:
                with st.spinner("Processing application data..."):
                    # Use cached function for better performance
                    df = load_excel_data(excel_file)

                    # Display the data with animation
                    st.markdown(
                        """
                    <div style="animation: fadeIn 0.5s ease; animation-delay: 0.2s; opacity: 0;">
                        <h3>Application Metadata</h3>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.dataframe(df)

                    # Convert dataframe to list of dictionaries
                    data = df.to_dict(orient="records")

                    # Perform mapping with animation
                    st.markdown(
                        """
                    <div style="animation: fadeIn 0.5s ease; animation-delay: 0.4s; opacity: 0;">
                        <h3>Processing Mapping...</h3>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Show a progress bar for visual effect
                    progress_bar = st.progress(0)
                    for i in range(101):
                        time.sleep(0.01)  # Small delay for visual smoothness
                        progress_bar.progress(i)

                    mapping = {}
                    for app in data:
                        app_name = app.get(
                            "application_name", app.get("Application Name", "Unknown")
                        )
                        cat = app.get("category", app.get("Category", "Other"))

                        if isinstance(cat, str):
                            cat = cat.lower()
                            if "core" in cat:
                                layer = "Business Architecture"
                            elif "integration" in cat:
                                layer = "Application Architecture"
                            else:
                                layer = "Technology Architecture"
                        else:
                            layer = "Technology Architecture"

                        mapping[app_name] = layer

                    st.session_state.mapping_result = mapping

                    # Display mapping results with animation
                    st.markdown(
                        """
                    <div style="animation: fadeIn 0.5s ease; animation-delay: 0.6s; opacity: 0;">
                        <h3>Auto-Mapping Results</h3>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Create a dataframe for better visualization
                    mapping_df = pd.DataFrame(
                        {
                            "Application": list(mapping.keys()),
                            "Architecture Layer": list(mapping.values()),
                        }
                    )

                    st.dataframe(mapping_df)

                    # Visualization of mapping distribution with animation
                    st.markdown(
                        """
                    <div style="animation: fadeIn 0.5s ease; animation-delay: 0.8s; opacity: 0;">
                        <h3>Layer Distribution</h3>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    layer_counts = mapping_df["Architecture Layer"].value_counts()

                    fig, ax = plt.subplots(figsize=(8, 5))
                    ax.pie(
                        layer_counts,
                        labels=layer_counts.index,
                        autopct="%1.1f%%",
                        colors=["#d00000", "#ff6b6b", "#ffa5a5"],
                        wedgeprops={
                            "edgecolor": "white",
                            "linewidth": 1,
                            "antialiased": True,
                        },
                    )
                    ax.set_title("Applications by Architecture Layer")
                    st.pyplot(fig)

                    # Download option with animation
                    st.markdown(
                        """
                    <div style="animation: fadeIn 0.5s ease; animation-delay: 1s; opacity: 0;">
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    download_mapping_key = "download_mapping_button"
                    if st.button(
                        "Download Mapping Results",
                        key=download_mapping_key,
                        type="primary",
                    ):
                        with st.spinner("Preparing download..."):
                            time.sleep(0.3)  # Small delay for visual smoothness
                            mapping_json = json.dumps(mapping, indent=2)
                            st.download_button(
                                "Download JSON",
                                mapping_json,
                                file_name="architecture_mapping.json",
                                mime="application/json",
                                key="download_mapping",
                            )

            except Exception as e:
                st.error(f"Error processing application data: {e}")

    # --- Modernization Roadmap Generator with smooth animations ---
    elif product == "Modernization Roadmap Generator":
        st.markdown(
            """
        <div style="animation: fadeIn 0.5s ease;">
            <h3>Generate application modernization roadmaps</h3>
            <p>Create tailored modernization roadmaps based on application characteristics and goals.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Pre-fill from interview if available
        app_name = st.text_input(
            "Application Name",
            value=st.session_state.interview_answers.get("application_name", ""),
        )

        col1, col2 = st.columns(2)
        with col1:
            status_options = ["Active", "On Hold", "Retired"]
            pre_status = st.session_state.interview_answers.get("status", "Active")
            try:
                status_index = status_options.index(pre_status)
            except ValueError:
                status_index = 0
            status = st.selectbox(
                "Application Status", status_options, index=status_index
            )

        with col2:
            tech_stack = st.multiselect(
                "Technology Stack", ["Legacy", "Cloud", "On-Prem", "Hybrid"]
            )

        modernization_goals = st.text_area("Modernization Goals (comma separated)")

        generate_roadmap_key = "generate_roadmap_button"
        if st.button("Generate Roadmap", key=generate_roadmap_key, type="primary"):
            with st.spinner("Generating modernization roadmap..."):
                # Add a small delay for visual smoothness
                time.sleep(0.8)

                roadmap = []
                timeline = []

                if status.lower() == "retired":
                    roadmap.append("Decommission application.")
                    timeline.append("Immediate")
                else:
                    if "Legacy" in tech_stack:
                        roadmap.append("Plan migration from legacy systems.")
                        timeline.append("3-6 months")

                    if "Cloud" in tech_stack:
                        roadmap.append("Enhance cloud adoption and scalability.")
                        timeline.append("1-3 months")

                    if "On-Prem" in tech_stack:
                        roadmap.append("Evaluate cloud migration opportunities.")
                        timeline.append("6-12 months")

                    if "Hybrid" in tech_stack:
                        roadmap.append("Optimize hybrid architecture for performance.")
                        timeline.append("3-6 months")

                    if modernization_goals:
                        goals = [g.strip() for g in modernization_goals.split(",")]
                        for i, goal in enumerate(goals):
                            roadmap.append(f"Implement goal: {goal}")
                            timeline.append(f"{(i+1)*3}-{(i+2)*3} months")

                    if not roadmap:
                        roadmap.append("No specific roadmap steps identified.")
                        timeline.append("N/A")

                st.session_state.roadmap_result = roadmap

                # Display roadmap in a more structured way with animation
                st.markdown(
                    """
                <div style="animation: fadeIn 0.5s ease;">
                    <h3>Modernization Roadmap:</h3>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Create a dataframe for better visualization
                roadmap_df = pd.DataFrame(
                    {
                        "Step": range(1, len(roadmap) + 1),
                        "Action": roadmap,
                        "Timeline": timeline,
                    }
                )

                st.dataframe(roadmap_df)

                # Gantt chart visualization with animation
                st.markdown(
                    """
                <div style="animation: fadeIn 0.5s ease; animation-delay: 0.3s; opacity: 0;">
                    <h3>Roadmap Timeline</h3>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Convert timeline to numeric values for visualization
                timeline_values = []
                for t in timeline:
                    if t == "Immediate":
                        timeline_values.append(1)
                    elif t == "N/A":
                        timeline_values.append(0)
                    else:
                        # Extract the first number from strings like "3-6 months"
                        try:
                            first_num = int(t.split("-")[0])
                            timeline_values.append(first_num)
                        except:
                            timeline_values.append(3)  # Default

                # Create Gantt chart with improved styling
                fig, ax = plt.subplots(figsize=(10, 5))

                # Create gradient colors for bars
                colors = []
                for i in range(len(roadmap)):
                    r = 208 - (i * 10 if i * 10 < 150 else 150)
                    g = i * 20 if i * 20 < 150 else 150
                    b = i * 5 if i * 5 < 100 else 100
                    colors.append(f"#{r:02x}{g:02x}{b:02x}")

                y_pos = range(len(roadmap))
                bars = ax.barh(
                    y_pos,
                    timeline_values,
                    align="center",
                    color=colors,
                    edgecolor="white",
                    linewidth=1,
                )
                ax.set_yticks(y_pos)
                ax.set_yticklabels([f"Step {i+1}" for i in range(len(roadmap))])
                ax.set_xlabel("Timeline (months)")
                ax.set_title("Modernization Roadmap Timeline")

                # Add value labels to bars
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    label_x_pos = width + 0.5
                    ax.text(
                        label_x_pos,
                        bar.get_y() + bar.get_height() / 2,
                        timeline[i],
                        va="center",
                        ha="left",
                        fontsize=9,
                    )

                # Improve grid and styling
                ax.grid(axis="x", linestyle="--", alpha=0.7)
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)

                st.pyplot(fig)

                # Download option with animation
                st.markdown(
                    """
                <div style="animation: fadeIn 0.5s ease; animation-delay: 0.6s; opacity: 0;">
                </div>
                """,
                    unsafe_allow_html=True,
                )

                download_roadmap_btn_key = "download_roadmap_btn"
                if st.button("Download Roadmap", key=download_roadmap_btn_key):
                    with st.spinner("Preparing download..."):
                        time.sleep(0.3)  # Small delay for visual smoothness
                        roadmap_json = json.dumps(
                            {
                                "application": app_name,
                                "status": status,
                                "tech_stack": tech_stack,
                                "roadmap": [
                                    {"step": i + 1, "action": a, "timeline": t}
                                    for i, (a, t) in enumerate(zip(roadmap, timeline))
                                ],
                            },
                            indent=2,
                        )

                        download_roadmap_key = "download_roadmap"
                        st.download_button(
                            "Download JSON",
                            roadmap_json,
                            file_name=f"modernization_roadmap_{app_name.replace(' ', '_')}.json",
                            mime="application/json",
                            key=download_roadmap_key,
                        )

        # Add universal file upload section
        file_upload_section(product)

    # --- Dependency Visualization with smooth animations ---
    elif product == "Dependency Visualization":
        st.markdown(
            """
        <div style="animation: fadeIn 0.5s ease;">
            <h3>Visualize application dependencies</h3>
            <p>Upload dependency data to generate interactive dependency graphs and visualizations.</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Add universal file upload section
        file_upload_section(product)

        # Additional dependency-specific functionality
        if product in st.session_state.excel_uploads:
            excel_file = st.session_state.excel_uploads[product]

            try:
                with st.spinner("Processing dependency data..."):
                    # Use cached function for better performance
                    df = load_excel_data(excel_file)

                    # Check if the dataframe has the required columns
                    required_cols = ["application_name", "depends_on"]
                    alt_cols = ["Application Name", "Depends On"]

                    # Try to find the required columns
                    app_col = None
                    dep_col = None

                    for col in df.columns:
                        if (
                            col.lower() == "application_name"
                            or col == "Application Name"
                        ):
                            app_col = col
                        elif col.lower() == "depends_on" or col == "Depends On":
                            dep_col = col

                    if app_col and dep_col:
                        # Convert to the expected format with animation
                        st.markdown(
                            """
                        <div style="animation: fadeIn 0.5s ease; animation-delay: 0.2s; opacity: 0;">
                            <h3>Processing Dependencies...</h3>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        # Show a progress bar for visual effect
                        progress_bar = st.progress(0)
                        for i in range(101):
                            time.sleep(0.01)  # Small delay for visual smoothness
                            progress_bar.progress(i)

                        data = []
                        for _, row in df.iterrows():
                            app_name = row[app_col]
                            depends_on = row[dep_col]

                            # Handle different formats of dependency data
                            dependencies = []
                            if isinstance(depends_on, str):
                                dependencies = [
                                    d.strip() for d in depends_on.split(",")
                                ]
                            elif not pd.isna(depends_on):
                                dependencies = [str(depends_on)]

                            data.append(
                                {
                                    "application_name": app_name,
                                    "depends_on": dependencies,
                                }
                            )

                        # Create graph using cached function
                        G = create_network_graph(data)

                        # Create network visualization with animation
                        st.markdown(
                            """
                        <div style="animation: fadeIn 0.5s ease; animation-delay: 0.4s; opacity: 0;">
                            <h3>Dependency Graph</h3>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        # Create a more visually appealing network
                        net = Network(
                            height="600px",
                            width="100%",
                            directed=True,
                            bgcolor="#ffffff",
                            font_color="#333333",
                        )

                        # Add nodes with improved styling
                        for node in G.nodes():
                            # Calculate node size based on connections
                            size = 25 + (G.in_degree(node) + G.out_degree(node)) * 5

                            # Assign colors based on connectivity
                            if G.in_degree(node) > G.out_degree(node):
                                color = "#d00000"  # More dependencies on this app
                            elif G.out_degree(node) > G.in_degree(node):
                                color = "#0066cc"  # This app depends on more apps
                            else:
                                color = "#009900"  # Balanced dependencies

                            net.add_node(
                                node,
                                label=node,
                                size=size,
                                color=color,
                                title=f"App: {node}<br>Depends on: {G.out_degree(node)}<br>Used by: {G.in_degree(node)}",
                            )

                        # Add edges with improved styling
                        for source, target in G.edges():
                            net.add_edge(
                                source,
                                target,
                                color="#999999",
                                width=2,
                                title=f"{source} depends on {target}",
                            )

                        # Configure physics for smoother visualization
                        net.barnes_hut(
                            gravity=-80000,
                            central_gravity=0.3,
                            spring_length=150,
                            spring_strength=0.05,
                            damping=0.09,
                            overlap=0,
                        )

                        net.show_buttons(filter_=["physics"])
                        net.show("dependency_graph.html")

                        # Display the graph
                        HtmlFile = open("dependency_graph.html", "r", encoding="utf-8")
                        source_code = HtmlFile.read()

                        # Add loading animation to the graph
                        enhanced_code = source_code.replace(
                            "</head>",
                            """
                        <style>
                        #mynetwork {
                            opacity: 0;
                            animation: fadeIn 1s ease forwards;
                        }
                        @keyframes fadeIn {
                            from { opacity: 0; }
                            to { opacity: 1; }
                        }
                        </style>
                        </head>
                        """,
                        )

                        st.components.v1.html(enhanced_code, height=650)

                        # Display statistics with animation
                        st.markdown(
                            """
                        <div style="animation: fadeIn 0.5s ease; animation-delay: 0.6s; opacity: 0;">
                            <h3>Dependency Statistics</h3>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Applications", len(G.nodes()))
                        with col2:
                            st.metric("Total Dependencies", len(G.edges()))
                        with col3:
                            # Calculate average dependencies
                            if len(G.nodes()) > 0:
                                avg_deps = len(G.edges()) / len(G.nodes())
                                st.metric("Avg Dependencies", f"{avg_deps:.1f}")

                        # Find most dependent-upon applications with animation
                        st.markdown(
                            """
                        <div style="animation: fadeIn 0.5s ease; animation-delay: 0.8s; opacity: 0;">
                            <h3>Most Critical Applications</h3>
                            <p>Applications with the most dependencies from other systems</p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        in_degrees = dict(G.in_degree())
                        most_depended = sorted(
                            in_degrees.items(), key=lambda x: x[1], reverse=True
                        )[:5]

                        if most_depended:
                            # Create a bar chart for most depended applications
                            fig, ax = plt.subplots(figsize=(10, 5))
                            apps = [app for app, count in most_depended if count > 0]
                            counts = [
                                count for app, count in most_depended if count > 0
                            ]

                            if (
                                apps
                            ):  # Only create chart if there are apps with dependencies
                                bars = ax.barh(apps, counts, color="#d00000")
                                ax.set_xlabel("Number of Dependencies")
                                ax.set_title("Most Critical Applications")

                                # Add value labels
                                for i, bar in enumerate(bars):
                                    width = bar.get_width()
                                    ax.text(
                                        width + 0.3,
                                        bar.get_y() + bar.get_height() / 2,
                                        f"{width}",
                                        va="center",
                                    )

                                # Improve styling
                                ax.grid(axis="x", linestyle="--", alpha=0.7)
                                ax.spines["top"].set_visible(False)
                                ax.spines["right"].set_visible(False)

                                st.pyplot(fig)
                            else:
                                st.info("No applications with dependencies found")

                    else:
                        st.error(
                            f"Required columns not found. Please ensure your Excel file has columns for application names and dependencies."
                        )
                        st.write(
                            "Expected columns: 'application_name'/'Application Name' and 'depends_on'/'Depends On'"
                        )
                        st.write("Available columns:", list(df.columns))

            except Exception as e:
                st.error(f"Error processing dependency data: {e}")
                st.exception(e)

    else:
        st.info("This product is under development or not implemented yet.")

        # Add universal file upload section even for under-development products
        file_upload_section(product)

# Add a footer with smooth animation
st.markdown(
    """
<div style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #777; 
            animation: fadeIn 0.5s ease; animation-delay: 1s; opacity: 0;">
    <p>DevoteamAI² Enterprise Architecture Assistant © 2025</p>
    <p style="font-size: 0.8rem;">Version 2.1 - Optimized for Performance & Compatibility</p>
</div>
""",
    unsafe_allow_html=True,
)

# Add page load time metric for performance monitoring
end_time = time.time()
load_time = end_time - st.session_state.page_load_time
st.session_state.page_load_time = end_time

# Only show in development mode
if st.checkbox("Show Performance Metrics", value=False):
    st.markdown(f"Page load time: {load_time:.2f} seconds")
