import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from rag_pipeline import rag_instance
from gemini_client import generate_answer

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            rag_instance.process_document(filepath)
            return jsonify({'message': 'Document processed successfully! Ready to chat.'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Unsupported file type. Please upload PDF, DOCX, or TXT.'}), 400

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    if not data or 'question' not in data:
        return jsonify({'error': 'No question provided'}), 400
        
    question = data['question']
    if not question.strip():
        return jsonify({'error': 'Empty question'}), 400
        
    try:
        # 1. Retrieve chunks
        chunks = rag_instance.retrieve(question, top_k=3)
        
        # 2. Check threshold / chunks existence
        if not chunks:
            return jsonify({
                'answer': "I don't have information on that in the provided document.",
                'sources': []
            }), 200
            
        # 3. Generate answer via Gemini
        answer = generate_answer(question, chunks)
        
        return jsonify({
            'answer': answer,
            'sources': chunks
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
