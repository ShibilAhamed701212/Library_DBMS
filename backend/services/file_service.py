import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_chat_file(file):
    """
    Saves a file uploaded in chat.
    Returns the relative path to be stored in DB.
    """
    if not file or file.filename == '':
        return None
        
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")
        
    # Create secure filename with UUID prefix to avoid collisions
    original_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex[:8]}_{original_name}"
    
    # Check upload folder exists
    upload_folder = os.path.join(current_app.static_folder, 'uploads', 'chat')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save
    file_path = os.path.join(upload_folder, unique_name)
    file.save(file_path)
    
    # Return relative path for URL usage
    return f"uploads/chat/{unique_name}"
