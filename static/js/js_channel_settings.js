    // --- Channel Settings Logic ---
    let settingsAvatarFile = null;

    async function openChannelSettings() {
        if(!activeRoomId) return;
        
        // Find current room data
        const room = allRooms.find(r => r.room_id == activeRoomId);
        if(!room) return;
        
        const modal = document.getElementById('channelSettingsModal');
        const content = document.getElementById('settingsContent');
        modal.style.display = 'block';
        document.getElementById('modalBackdrop').style.display = 'block';
        
        const isPrivate = room.room_type === 'private';
        const avatarSrc = room.room_avatar ? `/static/${room.room_avatar}` : null;
        const avatarInitial = (room.room_name || room.name || '?')[0].toUpperCase();
        
        content.innerHTML = `
            <div style="text-align: center; margin-bottom: 2rem;">
                <div style="width: 100px; height: 100px; margin: 0 auto 1rem; position: relative; cursor: pointer;" onclick="document.getElementById('settingsAvatarInput').click()">
                    ${avatarSrc ? 
                        `<img src="${avatarSrc}" style="width:100%; height:100%; border-radius:50%; object-fit:cover; border: 3px solid var(--primary);">` : 
                        `<div style="width:100%; height:100%; border-radius:50%; background: linear-gradient(135deg, #e0e7ff, #f3e8ff); display: flex; align-items: center; justify-content: center; font-size: 2.5rem; color: #6366f1; border: 3px solid var(--primary);">${avatarInitial}</div>`
                    }
                    <div style="position: absolute; bottom: 0; right: 0; background: var(--primary); color: white; border-radius: 50%; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 0.9rem;">📷</div>
                </div>
                <input type="file" id="settingsAvatarInput" style="display: none;" accept="image/*" onchange="handleSettingsAvatarSelect(this)">
                <div style="font-size: 0.8rem; color: var(--text-sub);">Click to change icon</div>
            </div>

            <form onsubmit="event.preventDefault(); saveChannelSettings();">
                <div style="margin-bottom: 1rem;">
                    <label style="display: block; font-weight: 600; font-size: 0.85rem; color: var(--text-sub); margin-bottom: 5px;">Channel Name</label>
                    <input type="text" id="editRoomName" class="form-control" value="${room.room_name || room.name}" style="width: 100%; padding: 10px; border-radius: 8px;">
                </div>
                
                <div style="margin-bottom: 1rem;">
                    <label style="display: block; font-weight: 600; font-size: 0.85rem; color: var(--text-sub); margin-bottom: 5px;">Topic / Description</label>
                    <textarea id="editRoomDesc" class="form-control" rows="2" style="width: 100%; padding: 10px; border-radius: 8px;">${room.description || ''}</textarea>
                </div>
                
                <div style="margin-bottom: 2rem; background: rgba(0,0,0,0.03); padding: 12px; border-radius: 8px; display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <div style="font-size: 0.75rem; color: var(--text-sub); font-weight: 600; text-transform: uppercase;">Channel ID</div>
                        <div style="font-family: monospace; font-size: 1.1rem; font-weight: 700; color: var(--text-main);">${room.room_id}</div>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="navigator.clipboard.writeText('${room.room_id}'); alert('Coppied ID: ${room.room_id}')">Copy ID</button>
                </div>

                <div style="display: flex; gap: 10px; margin-top: 2rem;">
                    <button type="submit" class="btn btn-primary" style="flex: 1;">Save Changes</button>
                    ${(activeUserRole === 'admin' || isPrivate) ? 
                        `<button type="button" class="btn btn-outline-danger" onclick="deleteChannel('${room.room_id}')">Delete Channel</button>` : ''
                    }
                </div>
            </form>
        `;
    }
    
    function handleSettingsAvatarSelect(input) {
         if (input.files && input.files[0]) {
            settingsAvatarFile = input.files[0];
            // Preview
            const reader = new FileReader();
            reader.onload = function(e) {
                // Update the img src or div content
                // Simplest: Refind the container and update HTML
                // But efficient: just alert "Selected"
            }
            reader.readAsDataURL(input.files[0]);
        }
    }
    
    async function saveChannelSettings() {
        const name = document.getElementById('editRoomName').value;
        const desc = document.getElementById('editRoomDesc').value;
        
        let avatarPath = null;
        
        // Upload avatar first if selected
        if(settingsAvatarFile) {
             const formData = new FormData();
             formData.append('file', settingsAvatarFile);
             try {
                 const res = await fetch('/chat/upload', { method: 'POST', body: formData });
                 const data = await res.json();
                 if(data.success) {
                     avatarPath = data.file_url;
                 } else {
                     alert("Failed to upload avatar: " + data.error);
                     return;
                 }
             } catch(e) { alert("Upload error"); return; }
        }
        
        // Update Room
        const formData = new FormData();
        formData.append('room_id', activeRoomId);
        formData.append('name', name);
        formData.append('description', desc);
        if(avatarPath) formData.append('avatar_path', avatarPath);
        
        try {
            const res = await fetch('/chat/room/update', { method: 'POST', body: formData });
            if(res.ok) {
                // Reload
                closeChannelSettings();
                loadRooms(); // Refresh sidebar to show new name/icon
                // Ideally refresh header too without full reload
                 document.getElementById('headerName').textContent = name;
                 if(avatarPath) {
                     document.getElementById('headerAvatar').innerHTML = `<img src="/static/${avatarPath}" style="width:100%;height:100%;object-fit:cover;">`;
                 }
            } else {
                alert("Update failed");
            }
        } catch(e) { alert("Error updating channel"); }
    }

    function closeChannelSettings() {
        document.getElementById('channelSettingsModal').style.display = 'none';
        document.getElementById('modalBackdrop').style.display = 'none';
        settingsAvatarFile = null; // Reset
    }
