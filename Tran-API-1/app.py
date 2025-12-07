"""Document Processing Agent - Web API and Interface."""

import os
import uuid
import json
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from src.agent import DocumentAgent

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET')

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx', 'xlsx', 'xlsm', 'txt', 'md', 'markdown'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/formats', methods=['GET'])
def get_formats():
    return jsonify({
        'input_formats': DocumentAgent.get_supported_input_formats(),
        'output_formats': ['html', 'docx', 'markdown', 'json']
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '' or file.filename is None:
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not supported. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())[:8]
    safe_filename = f"{unique_id}_{filename}"
    filepath = os.path.join(UPLOAD_FOLDER, safe_filename)
    file.save(filepath)
    
    try:
        agent = DocumentAgent()
        agent.load(filepath)
        summary = agent.get_summary()
        
        return jsonify({
            'success': True,
            'file_id': unique_id,
            'filename': filename,
            'filepath': safe_filename,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/extract', methods=['POST'])
def extract_document():
    data = request.json
    if not data or 'filepath' not in data:
        return jsonify({'error': 'No filepath provided'}), 400
    
    filepath = os.path.join(UPLOAD_FOLDER, data['filepath'])
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        agent = DocumentAgent()
        agent.load(filepath)
        
        result = {
            'text': agent.get_text(),
            'links': [{'text': l.text, 'url': l.url} for l in agent.get_links()],
            'images': len(agent.get_images()),
            'tables': len(agent.get_tables()),
            'metadata': agent.get_metadata()
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/convert', methods=['POST'])
def convert_document():
    data = request.json
    if not data or 'filepath' not in data or 'format' not in data:
        return jsonify({'error': 'filepath and format required'}), 400
    
    filepath = os.path.join(UPLOAD_FOLDER, data['filepath'])
    output_format = data['format'].lower()
    preserve_styles = data.get('preserve_styles', True)
    embed_images = data.get('embed_images', True)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    if output_format not in ['html', 'docx', 'markdown', 'md', 'json']:
        return jsonify({'error': 'Invalid format. Use: html, docx, markdown, json'}), 400
    
    try:
        agent = DocumentAgent()
        agent.load(filepath)
        
        base_name = Path(filepath).stem
        unique_id = str(uuid.uuid4())[:8]
        
        output_file = ""
        content = ""
        output_path = ""
        
        if output_format == 'html':
            output_file = f"{base_name}_{unique_id}.html"
            output_path = os.path.join(OUTPUT_FOLDER, output_file)
            content = agent.export_to_html(
                output_path=None, 
                include_styles=preserve_styles, 
                embed_images=embed_images
            )
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        elif output_format == 'docx':
            output_file = f"{base_name}_{unique_id}.docx"
            output_path = os.path.join(OUTPUT_FOLDER, output_file)
            agent.export_to_docx(output_path, embed_images=embed_images)
            content = "[ملف DOCX - لا يمكن عرضه مباشرة، قم بتحميله]"
        elif output_format in ['markdown', 'md']:
            output_file = f"{base_name}_{unique_id}.md"
            output_path = os.path.join(OUTPUT_FOLDER, output_file)
            content = agent.export_to_markdown(
                output_path=None, 
                include_frontmatter=True, 
                embed_images=embed_images
            )
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        elif output_format == 'json':
            output_file = f"{base_name}_{unique_id}.json"
            output_path = os.path.join(OUTPUT_FOLDER, output_file)
            content = agent.export_to_json(output_path=None, indent=2)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return jsonify({
            'success': True,
            'output_file': output_file,
            'download_url': f'/api/download/{output_file}',
            'content': content,
            'format': output_format
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    filepath = os.path.join(OUTPUT_FOLDER, secure_filename(filename))
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath, as_attachment=True)


@app.route('/api/preview', methods=['POST'])
def preview_document():
    data = request.json
    if not data or 'filepath' not in data:
        return jsonify({'error': 'No filepath provided'}), 400
    
    filepath = os.path.join(UPLOAD_FOLDER, data['filepath'])
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        agent = DocumentAgent()
        agent.load(filepath)
        html_content = agent.export_to_html(output_path=None, include_styles=True, embed_images=True)
        return jsonify({'html': html_content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/source', methods=['POST'])
def get_source():
    data = request.json
    if not data or 'filepath' not in data:
        return jsonify({'error': 'No filepath provided'}), 400
    
    filepath = os.path.join(UPLOAD_FOLDER, data['filepath'])
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        agent = DocumentAgent()
        agent.load(filepath)
        text_content = agent.get_text()
        
        metadata = agent.get_metadata()
        links = [{'text': l.text, 'url': l.url} for l in agent.get_links()]
        
        return jsonify({
            'text': text_content,
            'metadata': metadata,
            'links': links
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
