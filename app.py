import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from models.resume_parser import process_resume, fallback_process_resume
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)

# Configure secret key
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    logger.error("No SECRET_KEY set for Flask application")
    raise ValueError("No SECRET_KEY set for Flask application")

app.config['SECRET_KEY'] = SECRET_KEY
logger.info("Secret key configured successfully")

# Configure Google API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY not found in environment variables")
    raise EnvironmentError("GOOGLE_API_KEY not found in environment variables.")
    
genai.configure(api_key=GOOGLE_API_KEY)
logger.info("Google API configured successfully")

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
logger.info(f"Upload folder set to: {UPLOAD_FOLDER}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def home():
    logger.info("Home page accessed")
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    logger.info("File upload initiated")
    if 'file' not in request.files:
        logger.warning("No file part in the request")
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        logger.warning("No selected file")
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        logger.info(f"File saved to {file_path}")
        
        try:
            # Try to process the resume using Google's Generative AI
            parsed_data = process_resume(file_path)
            logger.info(f"Resume processed successfully: {parsed_data}")
        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Google API Error: {str(e)}")
            # Fallback to a simpler resume parsing method
            parsed_data = fallback_process_resume(file_path)
            logger.info(f"Fallback resume processing used: {parsed_data}")
        except Exception as e:
            logger.error(f"Unexpected error in resume processing: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred while processing the resume'}), 500
        
        # Store parsed_data in session for use in chatbot
        session['resume_data'] = parsed_data
        logger.info("Resume data stored in session")
        
        return redirect(url_for('chatbot'))
    logger.warning("File type not allowed")
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/chatbot')
def chatbot():
    logger.info("Chatbot page accessed")
    resume_data = session.get('resume_data', {})
    return render_template('chatbot.html', resume_data=resume_data)

@app.route('/chatbot_response', methods=['POST'])
def chatbot_response():
    logger.info("Chatbot response requested")
    message = request.json.get('message')
    resume_data = session.get('resume_data', {})
    
    response = f"You said: {message}\n\nHere's some info from the resume:\nName: {resume_data.get('Name', 'N/A')}\nSkills: {', '.join(resume_data.get('Skills', []))}"
    logger.info(f"Chatbot response generated: {response}")
    
    return jsonify({'response': response})

@app.route('/search', methods=['POST'])
def search_resumes():
    logger.info("Resume search initiated")
    query = request.json.get('query')
    # TODO: Implement resume search logic
    logger.info(f"Search query: {query}")
    return jsonify({'results': f"Searching for: {query}"}), 200

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    logger.info(f"Application started. Upload folder: {UPLOAD_FOLDER}")
    app.run(debug=True)