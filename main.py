# from flask import *
# from google import genai
# import os
# import markdown

# app = Flask(__name__)
# UPLOAD_FOLDER = 'uploads/src'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# print("API Key fetched successfully! ") if GOOGLE_API_KEY else print("API key not found")
# client=genai.Client(api_key=GOOGLE_API_KEY)
# model_id="gemini-2.0-flash"

# app.secret_key='RandomKey'

# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)

# @app.route('/', methods=['GET', 'POST'])
# def home():
#     if request.method == 'POST':
#         if 'file' not in request.files:
#             flash('No file part')
#             return render_template("index.html")
        
#         files = request.files.getlist('file')
#         uploaded_files = []
        
#         for file in files:
#             if file.filename == '':
#                 continue
#             filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
#             file.save(filename)
#             uploaded_files.append(file.filename)
        
#         if not uploaded_files:
#             flash('No file selected for uploading')
#             return render_template("index.html")
        
#         flash("Files uploaded successfully!")
    
#     # Get the list of files in the uploads folder
#     files_in_directory = os.listdir(app.config['UPLOAD_FOLDER'])
#     return render_template("index.html", files=files_in_directory)

#  # Import for decoding URL-encoded filenames

# @app.route('/delete/<filename>', methods=['POST'])
# def delete_file(filename):
#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#     if os.path.exists(file_path):
#         os.remove(file_path)  # Delete the file directly
#         flash(f"File '{filename}' has been deleted successfully.")
#     else:
#         flash(f"File '{filename}' not found.")
#     return redirect(url_for('home')) 


# @app.route('/generate-questions', methods=['GET', 'POST'])
# def GenerateQuestions():
#     if request.method == 'POST':
#         # Get the inputs from the form
#         mcq_questions = request.form.get('mcq-questions')
#         short_questions = request.form.get('short-questions')
#         long_questions = request.form.get('long-questions')
#         numerical_questions = request.form.get('numerical-questions')
#         difficulty_level = request.form.get('difficulty-level')

#         # Get the list of files in the uploads folder
#         files_in_directory = os.listdir(app.config['UPLOAD_FOLDER'])
#         file_paths = [os.path.join(app.config['UPLOAD_FOLDER'], file) for file in files_in_directory]

#         # Upload files and generate content
#         try:
#             for file_path in file_paths:
#                 file_upload = client.files.upload(file=file_path)

#             # Generate the prompt
#             prompt = (
#                 f"You are an expert educator. Given the source material, you are to devise "
#                 f"{mcq_questions} MCQ questions, {short_questions} short answer type questions, "
#                 f"{long_questions} long-form questions, and {numerical_questions} numerical type questions from it. "
#                 f"Make sure the questions are of {difficulty_level} difficulty and assess a student on all aspects such as cognitive ability, "
#                 f"critical thinking, active recall, etc. Do not include anything else in the response other than the questions themselves, also give the output in json format."
#             )

#             # Call the LLM API
#             response = client.models.generate_content(
#                 model=model_id,
#                 contents=[
#                     file_upload,
#                     prompt
#                 ]
#             )

#             # Debugging: Print the response
#             print("LLM Response:", response.text)

#             # Parse the response text (assuming it's JSON)
#             response_data = response.text  # If the response is already JSON, no need to parse

#         except Exception as e:
#             print("Error during LLM API call:", str(e))
#             flash("An error occurred while generating questions. Please try again.")
#             return redirect(url_for('home'))

#         # Render the response in the template
#         return render_template('questions.html', response=response_data)
#     else:
#         return redirect(url_for('home'))

# if __name__ == '__main__':
#     app.run(debug=True)

import os
import markdown
from datetime import datetime
from flask import (
    Flask, request, render_template, redirect, url_for, flash,
    session, send_from_directory, jsonify
)
from werkzeug.utils import secure_filename
# Use the NEW SDK package
from google import genai # Main import
from google.genai import types # Often needed for specific configurations/types
from dotenv import load_dotenv
from fpdf import FPDF
from docx import Document

# --- Configuration ---
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback-insecure-secret-key-CHANGE-ME')

# --- File Upload Configuration ---
UPLOAD_SOURCE_FOLDER = 'uploads/sources'
UPLOAD_ANSWER_FOLDER = 'uploads/answers'
GENERATED_FOLDER = 'generated'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'md'}

app.config['UPLOAD_SOURCE_FOLDER'] = UPLOAD_SOURCE_FOLDER
app.config['UPLOAD_ANSWER_FOLDER'] = UPLOAD_ANSWER_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

# --- Create directories ---
os.makedirs(UPLOAD_SOURCE_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_ANSWER_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# --- Gemini API Configuration (NEW SDK - google-genai with Client) ---
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
client = None # Initialize client variable
model_id = "gemini-2.0-flash" # Or your preferred model compatible with the new SDK

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY not found in environment variables.")
else:
    try:
        # Instantiate the Client - This is the core change
        # The client automatically picks up GOOGLE_API_KEY from env if not passed explicitly
        client = genai.Client()
        # You can optionally pass api_key: client = genai.Client(api_key=GOOGLE_API_KEY)

        # Configuration options are often passed directly in method calls or via types.GenerationConfig
        # Example config object (can be passed to generate_content)
        generation_config = types.GenerationConfig(
            # temperature=0.7,
            # max_output_tokens=8192,
            response_mime_type="text/plain"
        )
        # Example safety settings (can be passed to generate_content)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        print(f"Gemini client configured successfully for model usage (defaulting to models like {model_id}).")

    except Exception as e:
        print(f"Error configuring Gemini client: {e}")
        # client remains None, routes should check for this

# --- Helper Functions (Mostly unchanged, ensure they handle potential errors) ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def make_safe_filename(filename):
    try:
        base, ext = filename.rsplit('.', 1)
        safe_base = secure_filename(base)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{safe_base}_{timestamp}.{ext.lower()}"
    except ValueError:
        safe_base = secure_filename(filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{safe_base}_{timestamp}"

def create_pdf(content, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    if isinstance(content, bytes):
        try:
            content = content.decode('utf-8')
        except UnicodeDecodeError:
            content = content.decode('latin-1', errors='replace')
    pdf.multi_cell(0, 5, txt=content)
    filepath = os.path.join(app.config['GENERATED_FOLDER'], filename)
    try:
        pdf.output(filepath, "F")
        return filepath
    except Exception as e:
        print(f"Error writing PDF file {filepath}: {e}")
        return None

def create_docx(content, filename):
    document = Document()
    if isinstance(content, bytes):
        try:
            content = content.decode('utf-8')
        except UnicodeDecodeError:
            content = content.decode('latin-1', errors='replace')
    document.add_paragraph(content)
    filepath = os.path.join(app.config['GENERATED_FOLDER'], filename)
    try:
        document.save(filepath)
        return filepath
    except Exception as e:
        print(f"Error writing DOCX file {filepath}: {e}")
        return None

def cleanup_uploaded_files(filenames, folder_path):
    if not filenames: return
    for fname in filenames:
        try:
            safe_fname = secure_filename(fname)
            if safe_fname == fname:
                file_path = os.path.join(folder_path, safe_fname)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Cleaned up local file: {file_path}")
        except Exception as e:
            print(f"Error removing file during cleanup {fname}: {e}")

def cleanup_gemini_files(file_objects):
    """Safely deletes uploaded files from Gemini service using file objects."""
    if not file_objects or not client: # Need the client to delete
        return
    for file_obj in file_objects:
        try:
            # The file object returned by client.files.upload has a 'name' attribute
            if hasattr(file_obj, 'name'):
                client.files.delete(name=file_obj.name) # Use client.files.delete
                print(f"Deleted temporary Gemini file: {file_obj.name}")
            else:
                 print(f"Could not delete Gemini file: Invalid file object {file_obj}")
        except Exception as del_e:
            print(f"Could not delete temporary Gemini file {getattr(file_obj, 'name', 'UNKNOWN')}: {del_e}")


# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Question Generation Flow ---
@app.route('/generate', methods=['GET', 'POST'])
def generate_upload():
    if request.method == 'POST':
        if not client: # Check if the client was initialized
             flash("Gemini API client not initialized. Please check configuration.", "danger")
             return render_template('generate_upload.html', allowed_extensions=ALLOWED_EXTENSIONS)

        # --- File Handling ---
        if 'source_files' not in request.files:
            flash('No source file part in the request.', 'warning')
            return redirect(request.url)

        files = request.files.getlist('source_files')
        uploaded_filenames = []
        gemini_file_objects = [] # Store File objects returned by client.files.upload
        temp_local_paths = []

        for file in files:
            if file and file.filename != '' and allowed_file(file.filename):
                original_filename = file.filename
                safe_name = make_safe_filename(original_filename)
                filepath = os.path.join(app.config['UPLOAD_SOURCE_FOLDER'], safe_name)
                try:
                    file.save(filepath)
                    temp_local_paths.append(filepath)
                    uploaded_filenames.append(safe_name)

                    # Upload to Gemini (NEW SDK - client.files.upload)
                    print(f"Uploading {safe_name} to Gemini...")
                    # Pass the path directly
                    gemini_file = client.files.upload(file=filepath) # Use client.files.upload
                    gemini_file_objects.append(gemini_file)
                    print(f"Uploaded to Gemini: {gemini_file.name}")

                except Exception as e:
                    flash(f"Error saving or uploading file {original_filename}: {e}", "danger")
                    cleanup_uploaded_files([os.path.basename(p) for p in temp_local_paths], app.config['UPLOAD_SOURCE_FOLDER'])
                    cleanup_gemini_files(gemini_file_objects)
                    return redirect(request.url)
            elif file.filename != '':
                 flash(f"File type not allowed for {file.filename}", "warning")

        if not uploaded_filenames or not gemini_file_objects:
            flash('No valid files selected or uploaded to Gemini.', 'warning')
            return redirect(request.url)

        # --- Get Form Parameters ---
        try:
            mcq_questions = int(request.form.get('mcq-questions', 0))
            short_questions = int(request.form.get('short-questions', 0))
            long_questions = int(request.form.get('long-questions', 0))
            difficulty_level = request.form.get('difficulty-level', 'medium')
        except ValueError:
            flash("Invalid number format for question counts.", "danger")
            cleanup_uploaded_files(uploaded_filenames, app.config['UPLOAD_SOURCE_FOLDER'])
            cleanup_gemini_files(gemini_file_objects)
            return redirect(request.url)

        # --- Construct Prompt for Gemini ---
        # (Prompt remains the same as the previous good version)
        prompt = (
            f"Act as an expert educator. Analyze the provided document(s) thoroughly. "
            f"Based *strictly* on the content within these documents, generate the following educational questions:\n"
            f"- {mcq_questions} Multiple Choice Questions (MCQs). Each MCQ should have 4 distinct options (A, B, C, D) and clearly indicate the single correct answer.\n"
            f"- {short_questions} Short Answer Questions requiring concise, factual answers derived directly from the text.\n"
            f"- {long_questions} Long Answer Questions designed to assess deeper understanding, critical thinking, or application of concepts from the source material.\n\n"
            f"All questions must be at a '{difficulty_level}' difficulty level relative to the source material's complexity.\n"
            f"Format the output clearly using Markdown:\n"
            f"## Multiple Choice Questions\n1. [Question text]...\nA. [Option]\nB. [Option]\nC. [Option]\nD. [Option]\n**Answer: [Correct Letter]**\n\n"
            f"## Short Answer Questions\n1. [Question text]...\n\n"
            f"## Long Answer Questions\n1. [Question text]...\n\n"
            f"Do not add any introduction, conclusion, or commentary outside of the requested question structure."
        )

        # --- Call Gemini API (NEW SDK - client.models.generate_content) ---
        try:
            print("Sending request to Gemini API...")
            # Combine file objects and the text prompt into a list for 'contents'
            # The file objects returned by client.files.upload are directly usable here
            full_prompt_parts = gemini_file_objects + [prompt]

            # Use the client object to call generate_content
            # Pass model name and contents. Optional config can be added.
            response = client.models.generate_content(
                model=f'models/{model_id}', # Model name often needs 'models/' prefix with client
                contents=full_prompt_parts,
                # generation_config=generation_config, # Optional
                # safety_settings=safety_settings      # Optional
            )

            # Access the generated text (structure might vary slightly, check response object)
            # print("Raw Gemini Response:", response) # Debugging
            if hasattr(response, 'text'):
                 generated_text = response.text
                 print("Gemini response received.")
            # Handling potential blocks (check response structure if needed)
            elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                 block_reason = response.prompt_feedback.block_reason
                 flash(f"Content generation blocked. Reason: {block_reason}", "danger")
                 generated_text = f"Error: Content generation blocked. Reason: {block_reason}"
                 print(f"Gemini request blocked: {block_reason}")
                 # Proceed to show error, cleanup happens after redirect
            else:
                 print("Unexpected Gemini response structure:", response)
                 flash("Received an unexpected response format from the AI.", "danger")
                 generated_text = "Error: Unexpected response format from AI."

            # Store results in session
            session['generated_questions'] = generated_text
            session['source_filenames'] = uploaded_filenames # Keep track of local names

            # Cleanup Gemini files after use (important!)
            # cleanup_gemini_files(gemini_file_objects) # Moved cleanup

            return redirect(url_for('generate_review'))

        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            flash(f"An error occurred while generating questions: {e}", "danger")
            cleanup_uploaded_files(uploaded_filenames, app.config['UPLOAD_SOURCE_FOLDER'])
            cleanup_gemini_files(gemini_file_objects)
            return redirect(request.url)

    # GET request
    return render_template('generate_upload.html', allowed_extensions=ALLOWED_EXTENSIONS)


# --- Review Route (Largely unchanged, ensure template handles HTML) ---
@app.route('/generate/review')
def generate_review():
    generated_questions = session.get('generated_questions')
    if generated_questions is None:
        flash("No generated questions found. Please generate first.", "warning")
        return redirect(url_for('generate_upload'))
    try:
        # Using 'extra' extension for things like tables, fenced code etc.
        html_content = markdown.markdown(generated_questions, extensions=['extra'])
    except Exception as md_err:
        print(f"Markdown conversion error: {md_err}")
        html_content = f"<pre><code>{generated_questions}</code></pre>" # Fallback
    return render_template('generate_review.html', questions_html=html_content)


# --- Refinement Route (Updated for Client SDK) ---
@app.route('/generate/refine', methods=['POST'])
def generate_refine():
    if not client:
        return jsonify({"error": "Gemini client not initialized."}), 500

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid request data."}), 400

    user_message = data['message']
    original_questions = session.get('generated_questions', '')
    # TODO: Consider if source files need to be re-sent or referenced for refinement

    refinement_prompt = (
         f"You previously generated the following questions:\n\n---\n{original_questions}\n---\n\n"
         f"The user has the following request for refinement: '{user_message}'.\n\n"
         f"Please provide the revised set of questions based on this feedback, maintaining the original structure and constraints."
     )

    try:
        # Simple refinement call without re-uploading files
        response = client.models.generate_content(
            model=f'models/{model_id}',
            contents=[refinement_prompt] # Just the text prompt for refinement
            # Add original file objects here if needed for context
        )

        if hasattr(response, 'text'):
            refined_text = response.text
            session['generated_questions'] = refined_text # Update session
            refined_html = markdown.markdown(refined_text, extensions=['extra'])
            return jsonify({"refined_html": refined_html, "refined_text": refined_text})
        elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
             return jsonify({"error": f"Refinement blocked: {response.prompt_feedback.block_reason}"}), 400
        else:
             return jsonify({"error": "Unexpected response during refinement."}), 500

    except Exception as e:
        print(f"Error during refinement API call: {e}")
        return jsonify({"error": f"An error occurred during refinement: {e}"}), 500


# --- Download Route (Unchanged) ---
@app.route('/generate/download/<format>')
def generate_download(format):
    generated_questions = session.get('generated_questions')
    if not generated_questions:
        flash("No generated questions found to download.", "warning")
        return redirect(url_for('generate_review'))

    filename_base = f"generated_questions_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    filepath = None

    try:
        if format == 'pdf':
            filename = f"{filename_base}.pdf"
            filepath = create_pdf(generated_questions, filename)
        elif format == 'docx':
            filename = f"{filename_base}.docx"
            filepath = create_docx(generated_questions, filename)
        else:
            flash("Invalid download format.", "danger")
            return redirect(url_for('generate_review'))

        if filepath and os.path.exists(filepath):
            return send_from_directory(
                directory=app.config['GENERATED_FOLDER'],
                path=filename,
                as_attachment=True
            )
        else:
            flash("Failed to create download file.", "danger")
            return redirect(url_for('generate_review'))

    except Exception as e:
        flash(f"Error creating/sending download file: {e}", "danger")
        print(f"Error during download: {e}")
        return redirect(url_for('generate_review'))


# --- Question Evaluation Flow (Updated for Client SDK) ---
@app.route('/evaluate', methods=['GET', 'POST'])
def evaluate_upload():
    if request.method == 'POST':
        if not client:
             flash("Gemini API client not initialized.", "danger")
             return render_template('evaluate_upload.html', allowed_extensions=ALLOWED_EXTENSIONS)

        # --- File Handling (Sources) ---
        source_files = request.files.getlist('source_files')
        eval_source_filenames = []
        eval_source_gemini_objects = []
        eval_source_temp_paths = []

        if not source_files or all(f.filename == '' for f in source_files):
             flash('No source files selected.', 'warning'); return redirect(request.url)

        for file in source_files:
            if file and file.filename != '' and allowed_file(file.filename):
                original_filename = file.filename
                safe_name = make_safe_filename(f"src_{original_filename}")
                filepath = os.path.join(app.config['UPLOAD_SOURCE_FOLDER'], safe_name)
                try:
                    file.save(filepath)
                    eval_source_temp_paths.append(filepath)
                    eval_source_filenames.append(safe_name)
                    print(f"Uploading source {safe_name} to Gemini...")
                    gemini_file = client.files.upload(file=filepath) # Use client
                    eval_source_gemini_objects.append(gemini_file)
                    print(f"Uploaded source to Gemini: {gemini_file.name}")
                except Exception as e:
                    flash(f"Error saving/uploading source file {original_filename}: {e}", "danger")
                    cleanup_uploaded_files([os.path.basename(p) for p in eval_source_temp_paths], app.config['UPLOAD_SOURCE_FOLDER'])
                    cleanup_gemini_files(eval_source_gemini_objects)
                    return redirect(request.url)
            elif file.filename != '':
                 flash(f"File type not allowed for source: {file.filename}", "warning")

        if not eval_source_filenames or not eval_source_gemini_objects:
            flash('No valid source files uploaded to Gemini.', 'warning')
            cleanup_uploaded_files([os.path.basename(p) for p in eval_source_temp_paths], app.config['UPLOAD_SOURCE_FOLDER'])
            return redirect(request.url)

        # --- File Handling (Answers) ---
        answer_files = request.files.getlist('answer_files')
        eval_answer_filenames = []
        eval_answer_gemini_objects = []
        eval_answer_temp_paths = []

        if not answer_files or all(f.filename == '' for f in answer_files):
             flash('No answer files selected.', 'warning')
             cleanup_uploaded_files(eval_source_filenames, app.config['UPLOAD_SOURCE_FOLDER'])
             cleanup_gemini_files(eval_source_gemini_objects)
             return redirect(request.url)

        for file in answer_files:
             if file and file.filename != '' and allowed_file(file.filename):
                original_filename = file.filename
                safe_name = make_safe_filename(f"ans_{original_filename}")
                filepath = os.path.join(app.config['UPLOAD_ANSWER_FOLDER'], safe_name)
                try:
                    file.save(filepath)
                    eval_answer_temp_paths.append(filepath)
                    eval_answer_filenames.append(safe_name)
                    print(f"Uploading answer sheet {safe_name} to Gemini...")
                    gemini_file = client.files.upload(file=filepath) # Use client
                    eval_answer_gemini_objects.append(gemini_file)
                    print(f"Uploaded answer sheet to Gemini: {gemini_file.name}")
                except Exception as e:
                    flash(f"Error saving/uploading answer file {original_filename}: {e}", "danger")
                    cleanup_uploaded_files(eval_source_filenames, app.config['UPLOAD_SOURCE_FOLDER'])
                    cleanup_uploaded_files([os.path.basename(p) for p in eval_answer_temp_paths], app.config['UPLOAD_ANSWER_FOLDER'])
                    cleanup_gemini_files(eval_source_gemini_objects + eval_answer_gemini_objects)
                    return redirect(request.url)
             elif file.filename != '':
                 flash(f"File type not allowed for answer sheet: {file.filename}", "warning")

        if not eval_answer_filenames or not eval_answer_gemini_objects:
            flash('No valid answer files uploaded to Gemini.', 'warning')
            cleanup_uploaded_files(eval_source_filenames, app.config['UPLOAD_SOURCE_FOLDER'])
            cleanup_uploaded_files([os.path.basename(p) for p in eval_answer_temp_paths], app.config['UPLOAD_ANSWER_FOLDER'])
            cleanup_gemini_files(eval_source_gemini_objects)
            return redirect(request.url)

        # --- Construct Prompt for Gemini Evaluation ---
        # (Prompt remains the same)
        prompt = (
            "Act as an expert teaching assistant providing detailed evaluation.\n"
            "You are given the original source material document(s) AND one or more student answer sheet document(s).\n\n"
            "**Your Task:** Evaluate the submitted answer sheet(s) based *strictly* on the information present in the provided source material(s).\n\n"
            "**Evaluation Criteria:**\n"
            "1.  **Accuracy:** Are the answers factually correct according to the source material?\n"
            "2.  **Completeness:** Do the answers address all parts of the question asked (implicitly or explicitly)?\n"
            "3.  **Relevance:** Are the answers directly related to the question and derived from the source?\n"
            "4.  **Clarity:** Are the answers presented clearly and understandably?\n\n"
            "**Output Format:**\n"
            "Provide a structured evaluation, ideally question-by-question if the answer sheet format allows. For each question/answer:\n"
            "-   State the question (or reference number).\n"
            "-   Summarize the student's answer briefly.\n"
            "-   Provide specific feedback based on the criteria above (Accuracy, Completeness, Relevance, Clarity).\n"
            "-   Assign a score or points for the answer (e.g., X out of Y points) and justify it briefly.\n\n"
            "After evaluating all answers, provide:\n"
            "-   **Overall Score:** Calculate a total score (e.g., total points, percentage).\n"
            "-   **Overall Feedback:** Summarize the student's performance, highlighting strengths and key areas for improvement.\n\n"
            "Use Markdown for clear formatting (headings, bullet points).\n\n"
            "**IMPORTANT:** Base your entire evaluation *only* on the provided source documents. Do not use external knowledge. The source documents are provided first, followed by the answer sheet documents."
        )

        # --- Call Gemini API for Evaluation (NEW SDK - client.models.generate_content) ---
        all_gemini_objects_for_eval = eval_source_gemini_objects + eval_answer_gemini_objects
        try:
            print("Sending evaluation request to Gemini API...")
            full_prompt_parts = all_gemini_objects_for_eval + [prompt]
            response = client.models.generate_content(
                model=f'models/{model_id}',
                contents=full_prompt_parts
                # Add config/safety if needed
            )

            if hasattr(response, 'text'):
                 evaluation_text = response.text
                 print("Gemini evaluation received.")
            elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                 block_reason = response.prompt_feedback.block_reason
                 flash(f"Evaluation blocked. Reason: {block_reason}", "danger")
                 evaluation_text = f"Error: Evaluation blocked. Reason: {block_reason}"
                 print(f"Gemini evaluation blocked: {block_reason}")
            else:
                 print("Unexpected Gemini response structure during evaluation:", response)
                 flash("Received an unexpected response format during evaluation.", "danger")
                 evaluation_text = "Error: Unexpected response format from AI."

            # Store results
            session['evaluation_results'] = evaluation_text
            session['eval_source_filenames'] = eval_source_filenames
            session['eval_answer_filenames'] = eval_answer_filenames

            # Cleanup Gemini files
            # cleanup_gemini_files(all_gemini_objects_for_eval) # Moved cleanup

            return redirect(url_for('evaluate_results'))

        except Exception as e:
            print(f"Error calling Gemini API for evaluation: {e}")
            flash(f"An error occurred during evaluation: {e}", "danger")
            cleanup_uploaded_files(eval_source_filenames, app.config['UPLOAD_SOURCE_FOLDER'])
            cleanup_uploaded_files(eval_answer_filenames, app.config['UPLOAD_ANSWER_FOLDER'])
            cleanup_gemini_files(all_gemini_objects_for_eval)
            return redirect(request.url)

    # GET request
    return render_template('evaluate_upload.html', allowed_extensions=ALLOWED_EXTENSIONS)


# --- Evaluation Results Route (Largely unchanged) ---
@app.route('/evaluate/results')
def evaluate_results():
    evaluation_results = session.get('evaluation_results')
    if evaluation_results is None:
        flash("No evaluation results found.", "warning")
        return redirect(url_for('evaluate_upload'))
    try:
        html_content = markdown.markdown(evaluation_results, extensions=['extra'])
    except Exception as md_err:
        print(f"Markdown conversion error for eval results: {md_err}")
        html_content = f"<pre><code>{evaluation_results}</code></pre>" # Fallback
    return render_template('evaluate_results.html', results_html=html_content)


# --- Evaluation Download Route (Unchanged) ---
@app.route('/evaluate/download/<format>')
def evaluate_download(format):
    evaluation_results = session.get('evaluation_results')
    if not evaluation_results:
        flash("No evaluation results found to download.", "warning")
        return redirect(url_for('evaluate_results'))

    filename_base = f"evaluation_results_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    filepath = None

    try:
        if format == 'pdf':
            filename = f"{filename_base}.pdf"
            filepath = create_pdf(evaluation_results, filename)
        elif format == 'docx':
            filename = f"{filename_base}.docx"
            filepath = create_docx(evaluation_results, filename)
        else:
            flash("Invalid download format.", "danger")
            return redirect(url_for('evaluate_results'))

        if filepath and os.path.exists(filepath):
            return send_from_directory(
                directory=app.config['GENERATED_FOLDER'],
                path=filename,
                as_attachment=True
            )
        else:
            flash("Failed to create download file.", "danger")
            return redirect(url_for('evaluate_results'))

    except Exception as e:
        flash(f"Error creating/sending evaluation download: {e}", "danger")
        print(f"Error during eval download: {e}")
        return redirect(url_for('evaluate_results'))


# --- Optional: File Deletion (Needs UI integration) ---
# This route remains the same as it only deals with local files
@app.route('/delete/<folder>/<filename>', methods=['POST'])
def delete_file(folder, filename):
    if folder not in ['sources', 'answers']:
        flash("Invalid folder specified.", "danger")
        return redirect(request.referrer or url_for('index'))

    safe_filename = secure_filename(filename)
    if safe_filename != filename:
         flash("Invalid filename.", "danger")
         return redirect(request.referrer or url_for('index'))

    target_folder = app.config['UPLOAD_SOURCE_FOLDER'] if folder == 'sources' else app.config['UPLOAD_ANSWER_FOLDER']
    file_path = os.path.join(target_folder, safe_filename)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f"File '{filename}' deleted from {folder}.", "success")
        else:
            flash(f"File '{filename}' not found in {folder}.", "warning")
    except OSError as e:
        flash(f"Error deleting file '{filename}': {e}", "danger")
        print(f"Error deleting {file_path}: {e}")

    return redirect(request.referrer or url_for('index'))
#for using the datetime in the base.html template
@app.context_processor
def inject_now():
    """Injects the current UTC date and time into the template context."""
    return {'now': datetime.now()} # Use UTC for consistency
    # Or use datetime.now() if you specifically need the server's local time

# --- Main Execution ---
if __name__ == '__main__':
    if not client:
        print("\n--- Cannot start Flask server: Gemini client failed to initialize. Check API Key and configuration. ---\n")
    else:
        print("\n--- Starting Flask Development Server (Using google-genai SDK) ---")
        # Use host='0.0.0.0' to make accessible on local network if needed
        app.run(debug=True, host='0.0.0.0') # debug=True for development ONLY!