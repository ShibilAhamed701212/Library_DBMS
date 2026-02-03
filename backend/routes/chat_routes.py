from flask import Blueprint, render_template, request, jsonify, session, redirect, flash
from backend.middleware.auth import member_required
from backend.services.guild_service import get_my_guilds, create_guild, get_guild_details
from backend.services.channel_service import create_channel, get_channel_messages
from backend.services.social_service import get_friends_list

chat_bp = Blueprint('chat_bp', __name__)

# --- Guild Routes ---
@chat_bp.route('/guilds', methods=['GET'])
@member_required
def list_guilds():
    """Returns list of guilds user is in."""
    try:
        guilds = get_my_guilds(session['user_id'])
        return jsonify({'success': True, 'guilds': guilds})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@chat_bp.route('/guilds', methods=['POST'])
@member_required
def route_create_guild():
    data = request.json
    name = data.get('name')
    if not name: return jsonify({'error': 'Name required'}), 400
    
    try:
        guild_id = create_guild(session['user_id'], name)
        return jsonify({'success': True, 'guild_id': guild_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/conversations')
@member_required
def get_conversations_route():
    from backend.services.channel_service import get_my_dms
    from backend.services.guild_service import get_my_guilds
    from backend.repository.db_access import fetch_all
    
    user_id = session['user_id']
    
    # 1. Fetch DMs
    dms = get_my_dms(user_id)
    formatted_dms = []
    for d in dms:
        formatted_dms.append({
            'channel_id': d['channel_id'],
            'name': d['name'] if d['name'] != 'DM' else "Private Chat",
            'type': 'personal',
            'public_id': 1000000000 + d['channel_id']
        })

    # 2. Fetch Public Channels (Global Community, etc.)
    # We define 'public' as channels with guild_id IS NULL and is_private = FALSE
    public_channels = fetch_all("""
        SELECT channel_id, name, topic FROM channels 
        WHERE guild_id IS NULL AND is_private = FALSE
    """)
    formatted_public = []
    for p in public_channels:
        formatted_public.append({
            'channel_id': p['channel_id'],
            'name': p['name'],
            'type': 'public',
            'public_id': 1000000000 + p['channel_id']
        })

    # 3. Fetch Private Groups (Channels in joined guilds)
    guilds = get_my_guilds(user_id)
    formatted_groups = []
    for g in guilds:
        # Fetch channels for this guild
        channels = fetch_all("SELECT channel_id, name FROM channels WHERE guild_id = %s", (g['guild_id'],))
        for c in channels:
            formatted_groups.append({
                'channel_id': c['channel_id'],
                'name': c['name'],
                'guild_name': g['name'],
                'type': 'group',
                'public_id': 1000000000 + c['channel_id']
            })

    return jsonify({
        'success': True,
        'conversations': {
            'personal': formatted_dms,
            'public': formatted_public,
            'group': formatted_groups
        }
    })
@chat_bp.route('/dms', methods=['POST'])
@member_required
def create_dm_route():
    from backend.services.channel_service import create_dm
    data = request.json
    target_id = data.get('target_id')
    
    if not target_id:
        return jsonify({'error': 'Target ID required'}), 400
        
    cid = create_dm(session['user_id'], target_id)
    return jsonify({'success': True, 'channel_id': cid})


@chat_bp.route('/guilds/<int:guild_id>', methods=['GET'])
@member_required
def route_get_guild(guild_id):
    """Returns full hierarchy for a guild."""
    try:
        data = get_guild_details(guild_id)
        if not data: return jsonify({'error': 'Guild not found'}), 404
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Channel Routes ---
@chat_bp.route('/channels', methods=['POST'])
@member_required
def route_create_channel():
    data = request.json
    guild_id = data.get('guild_id')
    name = data.get('name')
    cat_id = data.get('category_id') # Optional
    type = data.get('type', 'text')
    
    try:
        cid = create_channel(guild_id, cat_id, name, type)
        return jsonify({'success': True, 'channel_id': cid})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@chat_bp.route('/channels/<int:channel_id>/messages', methods=['GET'])
@member_required
def route_get_messages(channel_id):
    try:
        msgs = get_channel_messages(channel_id)
        return jsonify({'success': True, 'messages': msgs})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@chat_bp.route('/join/<int:channel_id>', methods=['POST'])
@member_required
def route_join_channel(channel_id):
    from backend.services.chat_service import join_room
    try:
        join_room(session['user_id'], channel_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# --- Legacy/Helper Routes (Social, etc) ---
@chat_bp.route('/social/friends', methods=['GET'])
@member_required
def route_get_friends():
    try:
        friends = get_friends_list(session['user_id'])
        return jsonify({'success': True, 'friends': friends})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Include other necessary routes like upload/me if needed...
# For brevity in this large rebuild, focusing on core structure.
@chat_bp.route('/me', methods=['GET'])
@member_required
def route_get_me():
    from backend.services.chat_service import get_or_create_anon_id
    try:
        anon_id = get_or_create_anon_id(session['user_id'])
        return jsonify({'success': True, 'anon_id': anon_id})
    except:
        return jsonify({'error': 'Error'}), 500

@chat_bp.route('/anonymous', methods=['POST'])
@member_required
def toggle_anonymous():
    """Toggle anonymous mode for the user."""
    data = request.json
    is_anon = data.get('is_anon', False)
    session['is_anon'] = is_anon
    return jsonify({'success': True, 'is_anon': is_anon})

@chat_bp.route('/channels/<int:channel_id>', methods=['PATCH'])
@member_required
def route_update_channel(channel_id):
    data = request.json
    name = data.get('name')
    if not name: return jsonify({'error': 'Name required'}), 400
    from backend.repository.db_access import execute
    execute("UPDATE channels SET name = %s WHERE channel_id = %s", (name, channel_id))
    return jsonify({'success': True})

@chat_bp.route('/channels/<int:channel_id>', methods=['DELETE'])
@member_required
def route_delete_channel(channel_id):
    from backend.repository.db_access import execute
    execute("DELETE FROM chat_messages WHERE channel_id = %s", (channel_id,))
    execute("DELETE FROM channels WHERE channel_id = %s", (channel_id,))
    return jsonify({'success': True})

# --- Invitation System ---
@chat_bp.route('/invites/send', methods=['POST'])
@member_required
def send_invite():
    data = request.json
    target_user_id = data.get('target_user_id')
    target_channel_id = data.get('target_channel_id')
    invite_type = data.get('type', 'DM')
    
    from backend.utils.snowflake import SnowflakeGenerator
    from backend.repository.db_access import execute
    
    gen = SnowflakeGenerator()
    invite_id = gen.next_id()
    
    execute("""
        INSERT INTO chat_invitations (invite_id, sender_id, target_user_id, target_channel_id, type)
        VALUES (%s, %s, %s, %s, %s)
    """, (invite_id, session['user_id'], target_user_id, target_channel_id, invite_type))
    
    return jsonify({'success': True, 'invite_id': str(invite_id)})

@chat_bp.route('/invites/pending', methods=['GET'])
@member_required
def get_pending_invites():
    from backend.repository.db_access import fetch_all
    user_id = session['user_id']
    
    # 1. Invites sent TO me (Friend reqs + Group invites)
    my_invites = fetch_all("""
        SELECT i.*, u.name as sender_name, u.profile_pic as sender_pic, c.name as channel_name 
        FROM chat_invitations i
        JOIN users u ON i.sender_id = u.user_id
        LEFT JOIN channels c ON i.target_channel_id = c.channel_id
        WHERE i.target_user_id = %s AND i.status = 'pending'
    """, (user_id,))
    
    # 2. Group invites for channels I own (via guild)
    group_invites = fetch_all("""
        SELECT i.*, u.name as sender_name, u.profile_pic as sender_pic, c.name as channel_name
        FROM chat_invitations i
        JOIN users u ON i.sender_id = u.user_id
        JOIN channels c ON i.target_channel_id = c.channel_id
        JOIN guilds g ON c.guild_id = g.guild_id
        WHERE g.owner_id = %s AND i.status = 'pending' AND i.type = 'GROUP'
    """, (user_id,))
    
    all_invites = my_invites + group_invites
    
    # Stringify invite_id for JSON safety
    for iv in all_invites:
        iv['invite_id'] = str(iv['invite_id'])
        
    return jsonify({'success': True, 'invites': all_invites})

@chat_bp.route('/invites/handle', methods=['POST'])
@member_required
def handle_invite():
    data = request.json
    invite_id = data.get('invite_id')
    action = data.get('action') # 'accept' or 'reject'
    
    if action not in ['accept', 'reject']:
        return jsonify({'error': 'Invalid action'}), 400
        
    status = 'accepted' if action == 'accept' else 'rejected'
    
    from backend.repository.db_access import execute, fetch_one
    execute("UPDATE chat_invitations SET status = %s WHERE invite_id = %s", (status, invite_id))
    
    if action == 'accept':
        invite = fetch_one("SELECT * FROM chat_invitations WHERE invite_id = %s", (invite_id,))
        if not invite: return jsonify({'error': 'Invite not found'}), 404
        
        if invite['type'] == 'DM':
            from backend.services.channel_service import create_dm
            cid = create_dm(invite['sender_id'], invite['target_user_id'])
            return jsonify({'success': True, 'channel_id': cid})
        
        elif invite['type'] == 'GROUP':
            chan = fetch_one("SELECT guild_id FROM channels WHERE channel_id = %s", (invite['target_channel_id'],))
            if chan and chan['guild_id']:
                execute("INSERT IGNORE INTO guild_members (guild_id, user_id) VALUES (%s, %s)", (chan['guild_id'], invite['sender_id']))
                return jsonify({'success': True})
            
    return jsonify({'success': True})
@chat_bp.route('/upload', methods=['POST'])
@member_required
def route_upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    import os
    import uuid
    from werkzeug.utils import secure_filename
    
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        
        # Save to static/uploads/chat using Flask's configured static folder
        from flask import current_app
        save_dir = os.path.join(current_app.static_folder, 'uploads', 'chat')
        os.makedirs(save_dir, exist_ok=True)
        
        save_path = os.path.join(save_dir, unique_name)
        file.save(save_path)
        
        return jsonify({
            'success': True, 
            'file_path': f"/static/uploads/chat/{unique_name}", 
            'filename': filename,
            'type': 'image' if ext in ['png', 'jpg', 'jpeg', 'gif'] else 'file'
        })
        
    return jsonify({'error': 'File type not allowed'}), 400
