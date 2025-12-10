"""
BureauBot Flask Backend Server
Provides REST API for the chatbot frontend
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import sys
from datetime import timedelta

# Add parent directory to path to import chatbot module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatbot import SessionState, chat_with_agent

# Configure Flask to serve static files from the parent directory (frontend)
app = Flask(__name__, static_folder="../", static_url_path="/")
app.secret_key = "bureaubot-secret-key-change-in-production"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Enable CORS for frontend
CORS(app, supports_credentials=True)

# In-memory storage for sessions (in production, use Redis or database)
sessions_store = {}



@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Handle chat messages from the frontend
    
    Request JSON:
    {
        "message": "user message text",
        "session_id": "optional session identifier"
    }
    
    Response JSON:
    {
        "reply": "bot response text",
        "session_id": "session identifier",
        "stage": "current conversation stage"
    }
    """
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get or create session
        if session_id and session_id in sessions_store:
            chat_session = sessions_store[session_id]
        else:
            # Create new session
            import uuid
            session_id = str(uuid.uuid4())
            chat_session = {
                'state': SessionState(),
                'history': []
            }
            sessions_store[session_id] = chat_session
        
        # Process message
        state = chat_session['state']
        history = chat_session['history']
        
        reply, updated_history = chat_with_agent(user_message, state, history)
        
        # Update session
        chat_session['history'] = updated_history
        
        return jsonify({
            'reply': reply,
            'session_id': session_id,
            'stage': state.stage,
            'pdf_path': state.filled_pdf_path if state.filled_pdf_path else None
        })
    
    except Exception as e:
        print(f"[ERROR] Chat endpoint failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<path:filename>', methods=['GET'])
def download_pdf(filename):
    """Download a filled PDF file"""
    try:
        import os
        from flask import send_file
        
        # Security: only allow downloads from filled_pdfs directory
        if not filename.endswith('.pdf'):
            return jsonify({'error': 'Invalid file type'}), 400
        
        file_path = os.path.join('filled_pdfs', filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    
    except Exception as e:
        print(f"[ERROR] Download endpoint failed: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def reset_session():
    """Reset a chat session"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if session_id and session_id in sessions_store:
            del sessions_store[session_id]
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    print("=" * 60)
    print("BureauBot Backend Server Starting...")
    print("=" * 60)
    print("Server will run on: http://localhost:5001")
    print("API endpoint: http://localhost:5001/api/chat")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5001)
