from flask import Blueprint, render_template, request, jsonify, session, redirect, flash, current_app
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
            'name': d['partner_name'], # Use partner name
            'type': 'personal',
            'public_id': 1000000000 + d['channel_id'],
            'icon': d.get('partner_pic') # User avatar
        })

    # 2. Fetch Public Channels (Global Community, etc.)
    # We define 'public' as channels with guild_id IS NULL and is_private = FALSE
    public_channels = fetch_all("""
        SELECT channel_id, name, topic, icon FROM channels 
        WHERE guild_id IS NULL AND is_private = FALSE
    """)
    formatted_public = []
    for p in public_channels:
        formatted_public.append({
            'channel_id': p['channel_id'],
            'name': p['name'],
            'type': 'public',
            'icon': p.get('icon'),
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
            
    # 4. Fetch Private Global Groups (Non-Guild Private Channels)
    # Re-using get_my_dms logic but filtering for non-DM names
    # Or strict query:
    private_groups = fetch_all("""
        SELECT c.channel_id, c.name, c.icon 
        FROM channels c
        JOIN dm_participants dp ON c.channel_id = dp.channel_id
        WHERE dp.user_id = %s AND c.guild_id IS NULL AND c.is_private = TRUE AND c.name != 'DM'
    """, (user_id,))
    
    for pg in private_groups:
        formatted_groups.append({
            'channel_id': pg['channel_id'],
            'name': pg['name'],
            'icon': pg.get('icon'),
            'guild_name': 'Private Group',
            'type': 'group', # Display in Group Tab
            'public_id': 1000000000 + pg['channel_id']
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
    is_private = data.get('is_private', False)
    
    try:
        cid = create_channel(guild_id, cat_id, name, type, is_private=is_private, creator_id=session['user_id'])
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
    from backend.repository.db_access import execute, fetch_one
    user_id = session['user_id']
    user_role = session.get('role', 'member')
    
    # Check if user is admin OR channel creator
    channel = fetch_one("SELECT created_by FROM channels WHERE channel_id = %s", (channel_id,))
    
    if user_role != 'admin':
        # Check if user is channel creator
        if not channel or channel.get('created_by') != user_id:
            return jsonify({'success': False, 'error': 'Only admins or channel creators can delete channels'}), 403
    
    execute("DELETE FROM chat_messages WHERE channel_id = %s", (channel_id,))
    execute("DELETE FROM dm_participants WHERE channel_id = %s", (channel_id,))
    execute("DELETE FROM channels WHERE channel_id = %s", (channel_id,))
    return jsonify({'success': True})

# --- Leave Channel ---
@chat_bp.route('/channels/<int:channel_id>/leave', methods=['POST'])
@member_required
def route_leave_channel(channel_id):
    """Leave a channel (remove from dm_participants)."""
    from backend.repository.db_access import execute
    user_id = session['user_id']
    
    # Remove user from participants
    execute("DELETE FROM dm_participants WHERE channel_id = %s AND user_id = %s", (channel_id, user_id))
    
    return jsonify({'success': True})

# --- Kick Member (Admin/Owner only) ---
@chat_bp.route('/channels/<int:channel_id>/kick/<int:target_user_id>', methods=['POST'])
@member_required
def route_kick_member(channel_id, target_user_id):
    """Kick a member from the channel (admin or channel creator only)."""
    from backend.repository.db_access import execute, fetch_one
    user_id = session['user_id']
    user_role = session.get('role', 'member')
    
    # Check if user is admin OR channel creator
    channel = fetch_one("SELECT created_by FROM channels WHERE channel_id = %s", (channel_id,))
    
    if user_role != 'admin':
        if not channel or channel.get('created_by') != user_id:
            return jsonify({'success': False, 'error': 'Only admins or channel creators can kick members'}), 403
    
    # Cannot kick yourself
    if target_user_id == user_id:
        return jsonify({'success': False, 'error': 'Cannot kick yourself'}), 400
    
    # Remove user from channel
    execute("DELETE FROM dm_participants WHERE channel_id = %s AND user_id = %s", (channel_id, target_user_id))
    
    # LOGGING
    log_audit_action(channel_id, user_id, "KICK_MEMBER", f"Kicked User ID {target_user_id}")

    return jsonify({'success': True, 'message': 'Member kicked successfully'})

# --- Channel Members ---
@chat_bp.route('/channels/<int:channel_id>/members', methods=['GET'])
@member_required
def route_get_channel_members(channel_id):
    """Get list of members in a channel."""
    from backend.repository.db_access import fetch_all, fetch_one
    user_id = session['user_id']
    user_role = session.get('role', 'member')
    
    # Get channel info
    channel = fetch_one("SELECT * FROM channels WHERE channel_id = %s", (channel_id,))
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
    
    channel_creator = channel.get('created_by')
    members = []
    
    # Check if current user is owner
    is_current_user_owner = (channel_creator == user_id) or (user_role == 'admin')
    
    # For private channels, get from dm_participants
    if channel.get('is_private') or channel.get('guild_id') is None:
        # Special Case: Global Chat (ID 1) - Include ALL Admins (Library Admins)
        if channel_id == 1:
            participants = fetch_all("""
                SELECT u.user_id, u.name, u.profile_pic, u.role, NULL as channel_role
                FROM users u
                WHERE u.role = 'admin'
                UNION
                SELECT u.user_id, u.name, u.profile_pic, u.role, dp.role as channel_role
                FROM dm_participants dp
                JOIN users u ON dp.user_id = u.user_id
                WHERE dp.channel_id = %s
            """, (channel_id,))
        else:
            # Regular Groups/DMs: Only participants
            participants = fetch_all("""
                SELECT u.user_id, u.name, u.profile_pic, u.role, dp.role as channel_role
                FROM dm_participants dp
                JOIN users u ON dp.user_id = u.user_id
                WHERE dp.channel_id = %s
            """, (channel_id,))
        
        # Remove duplicates (in case admin is also in participants)
        seen_ids = set()
        unique_participants = []
        for p in participants:
            if p['user_id'] not in seen_ids:
                unique_participants.append(p)
                seen_ids.add(p['user_id'])
                
        for p in unique_participants:
            members.append({
                'user_id': p['user_id'],
                'name': p['name'],
                'profile_pic': p['profile_pic'] or 'default.jpg',
                'role': p.get('channel_role') or p['role'], # Prefer channel role (admin) if set, else global role
                'is_owner': p['user_id'] == channel_creator
            })
    else:
        # For guild channels, get guild members
        guild_id = channel.get('guild_id')
        guild_members = fetch_all("""
            SELECT u.user_id, u.name, u.profile_pic, gm.role 
            FROM guild_members gm
            JOIN users u ON gm.user_id = u.user_id
            WHERE gm.guild_id = %s
        """, (guild_id,))
        
        for m in guild_members:
            members.append({
                'user_id': m['user_id'],
                'name': m['name'],
                'profile_pic': m['profile_pic'] or 'default.jpg',
                'role': m['role'], # Guild role
                'is_owner': m.get('role') == 'owner'
            })
    
    return jsonify({'success': True, 'members': members, 'is_owner': is_current_user_owner})

# --- Member Management ---
@chat_bp.route('/channels/<int:channel_id>/members/<int:target_user_id>/role', methods=['POST'])
@member_required
def route_update_member_role(channel_id, target_user_id):
    """Update a member's role in the channel (Promote/Demote)."""
    from backend.repository.db_access import execute, fetch_one
    
    # Check permissions
    # Only Channel Creator (Owner) or System Admin can change roles
    user_id = session['user_id']
    user_role = session.get('role', 'member') # Global role
    
    channel = fetch_one("SELECT * FROM channels WHERE channel_id = %s", (channel_id,))
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
        
    # Is requester authorized?
    is_owner = (channel.get('created_by') == user_id)
    is_sys_admin = (user_role == 'admin')
    
    if not (is_owner or is_sys_admin):
        return jsonify({'error': 'Unauthorized'}), 403
        
    # Update role in dm_participants
    new_role = request.json.get('role', 'member') # 'admin' or 'member'
    
    # Prevent demoting the Owner
    if channel.get('created_by') == target_user_id and new_role != 'admin':
         # Actually owner should probably stay owner, but let's allow them to be 'admin' in role column
         pass
         
    execute("UPDATE dm_participants SET role = %s WHERE channel_id = %s AND user_id = %s", 
            (new_role, channel_id, target_user_id))
            
    # LOGGING
    log_audit_action(channel_id, user_id, "UPDATE_ROLE", f"Changed User {target_user_id} role to {new_role}")

    return jsonify({'success': True})

# --- Channel Settings ---
@chat_bp.route('/channels/<int:channel_id>/settings', methods=['GET'])
@member_required
def route_get_channel_settings(channel_id):
    """Get channel settings."""
    from backend.repository.db_access import fetch_one
    
    channel = fetch_one("""
        SELECT c.*, u.name as owner_name 
        FROM channels c
        LEFT JOIN users u ON c.created_by = u.user_id
        WHERE c.channel_id = %s
    """, (channel_id,))
    
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
    
    return jsonify({
        'success': True,
        'name': channel.get('name'),
        'owner_name': channel.get('owner_name') or 'System',
        'is_private': bool(channel.get('is_private')),
        'type': channel.get('type'),
        'topic': channel.get('topic'),
        'icon': channel.get('icon')  # If exists in schema
    })

@chat_bp.route('/channels/<int:channel_id>/settings', methods=['POST'])
@member_required
def route_update_channel_settings(channel_id):
    """Update channel settings."""
    from backend.repository.db_access import execute, fetch_one
    from werkzeug.utils import secure_filename
    import os
    import uuid
    
    channel = fetch_one("SELECT * FROM channels WHERE channel_id = %s", (channel_id,))
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
        
    # --- RESTRICTION: Global Community (ID 1) is Admin-Only for settings ---
    if channel_id == 1:
        user_role = session.get('role', 'member')
        if user_role != 'admin':
            return jsonify({'success': False, 'error': 'Only admins can change Global Community settings'}), 403
    
    # Handle form data
    is_private = request.form.get('is_private') == 'true'
    chat_type = request.form.get('type', 'text')
    
    # Handle icon upload
    icon_path = None
    if 'icon' in request.files:
        file = request.files['icon']
        if file and file.filename:
            ext = os.path.splitext(file.filename)[1]
            unique_name = f"channel_{channel_id}_{uuid.uuid4().hex[:8]}{ext}"
            save_dir = os.path.join(current_app.static_folder, 'uploads', 'channels')
            os.makedirs(save_dir, exist_ok=True)
            file.save(os.path.join(save_dir, unique_name))
            icon_path = f"uploads/channels/{unique_name}"
    
    # Update channel
        execute("""
            UPDATE channels SET is_private = %s, type = %s, icon = %s WHERE channel_id = %s
        """, (is_private, chat_type, icon_path, channel_id))
    else:
        execute("""
            UPDATE channels SET is_private = %s, type = %s WHERE channel_id = %s
        """, (is_private, chat_type, channel_id))
    
    # FIX: If switching to PRIVATE, ensure the owner is in participants list
    if is_private:
        # Get creator (use existing channel obj)
        owner_id = channel.get('created_by')
        
        if owner_id:
             # Insert ignore to avoid duplicates
            execute("""
                INSERT IGNORE INTO dm_participants (channel_id, user_id, role) 
                VALUES (%s, %s, 'admin')
            """, (channel_id, owner_id))
            
        # Also ensure the CURRENT user (if different from owner, e.g. Admin) is added
        current_user_id = session['user_id']
        if owner_id != current_user_id:
             execute("""
                INSERT IGNORE INTO dm_participants (channel_id, user_id, role) 
                VALUES (%s, %s, 'admin')
                INSERT IGNORE INTO dm_participants (channel_id, user_id, role) 
                VALUES (%s, %s, 'admin')
            """, (channel_id, current_user_id))
            
    # LOGGING
    log_details = f"Updated settings. Private: {is_private}"
    log_audit_action(channel_id, session['user_id'], "UPDATE_SETTINGS", log_details)
    
    response = {'success': True}
    if icon_path:
        response['icon'] = icon_path
    return jsonify(response)

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

# ==========================================
# RULES & LOGS IMPLEMENTATION
# ==========================================

def log_audit_action(channel_id, user_id, action_type, details=None):
    """Helper to insert audit log entry."""
    from backend.repository.db_access import execute
    try:
        execute("""
            INSERT INTO audit_logs (channel_id, user_id, action_type, details)
            VALUES (%s, %s, %s, %s)
        """, (channel_id, user_id, action_type, details))
    except Exception as e:
        print(f"❌ Failed to log action: {e}")

@chat_bp.route('/channels/<int:channel_id>/rules', methods=['GET'])
@member_required
def route_get_rules(channel_id):
    """Get channel rules."""
    from backend.repository.db_access import fetch_one
    channel = fetch_one("SELECT rules, guild_id, created_by FROM channels WHERE channel_id = %s", (channel_id,))
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
        
    rules = channel.get('rules') or "No rules set for this channel."
    
    # If global chat, maybe return hardcoded rules if empty?
    if channel_id == 1 and not channel.get('rules'):
        rules = "1. Be respectful.\n2. No spamming.\n3. Keep it family friendly."

    # Determine Edit Permissions
    user_id = session['user_id']
    user_role = session.get('role', 'member')
    can_edit = (user_role == 'admin') or (channel.get('created_by') == user_id)
        
    return jsonify({'success': True, 'rules': rules, 'can_edit': can_edit})

@chat_bp.route('/channels/<int:channel_id>/rules', methods=['POST'])
@member_required
def route_update_rules(channel_id):
    """Update channel rules (Admin/Owner only)."""
    from backend.repository.db_access import execute, fetch_one
    
    data = request.json
    new_rules = data.get('rules')
    
    if new_rules is None:
        return jsonify({'error': 'Rules content required'}), 400
        
    user_id = session['user_id']
    user_role = session.get('role', 'member')
    
    channel = fetch_one("SELECT created_by FROM channels WHERE channel_id = %s", (channel_id,))
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
        
    # Check permissions
    if user_role != 'admin' and channel.get('created_by') != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    execute("UPDATE channels SET rules = %s WHERE channel_id = %s", (new_rules, channel_id))
    
    # Log it
    log_audit_action(channel_id, user_id, "UPDATE_RULES", "Updated channel rules")
    
    return jsonify({'success': True})

@chat_bp.route('/channels/<int:channel_id>/logs', methods=['GET'])
@member_required
def route_get_logs(channel_id):
    """Get audit logs for a channel."""
    from backend.repository.db_access import fetch_all, fetch_one
    
    user_id = session['user_id']
    user_role = session.get('role', 'member')
    
    channel = fetch_one("SELECT created_by FROM channels WHERE channel_id = %s", (channel_id,))
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
    
    # Permission: Admins, Channel Owners, or maybe Channel Admins
    # For now: Global Admin or Channel Creator
    if user_role != 'admin' and channel.get('created_by') != user_id:
        return jsonify({'error': 'Unauthorized access to verify logs'}), 403
        
    logs = fetch_all("""
        SELECT a.log_id, a.action_type, a.details, a.created_at, u.name as user_name, u.role as user_role
        FROM audit_logs a
        JOIN users u ON a.user_id = u.user_id
        WHERE a.channel_id = %s
        ORDER BY a.created_at DESC
        LIMIT 50
    """, (channel_id,))
    
    return jsonify({'success': True, 'logs': logs})
