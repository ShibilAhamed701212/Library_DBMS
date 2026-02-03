import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)

from backend.repository.db_access import execute, fetch_one, fetch_all

def migrate_to_discord_schema():
    print("🚀 Starting Discord Architecture Migration (V2)...")
    
    # Disable foreign key checks temporarily to avoid constraint issues during creation
    execute("SET FOREIGN_KEY_CHECKS = 0")

    # 1. Create GUILDS
    print("1. Creating 'guilds' table...")
    execute("""
        CREATE TABLE IF NOT EXISTS guilds (
            guild_id INT AUTO_INCREMENT PRIMARY KEY,
            owner_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            icon_url VARCHAR(255),
            region VARCHAR(50) DEFAULT 'us-east',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)

    # 2. Create CATEGORIES
    execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            guild_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            position INT DEFAULT 0,
            is_private BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
        )
    """)

    # 3. Create CHANNELS
    execute("""
        CREATE TABLE IF NOT EXISTS channels (
            channel_id INT AUTO_INCREMENT PRIMARY KEY,
            guild_id INT, 
            category_id INT,
            name VARCHAR(100) NOT NULL,
            topic VARCHAR(255),
            type VARCHAR(20) DEFAULT 'text',
            position INT DEFAULT 0,
            is_private BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
        )
    """)
    
    # 4. Create ROLES
    execute("""
        CREATE TABLE IF NOT EXISTS roles (
            role_id INT AUTO_INCREMENT PRIMARY KEY,
            guild_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            color VARCHAR(7) DEFAULT '#99aab5',
            permissions BIGINT DEFAULT 0,
            position INT DEFAULT 0,
            hoist BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE
        )
    """)

    # 5. Create GUILD_MEMBERS
    execute("""
        CREATE TABLE IF NOT EXISTS guild_members (
            guild_id INT NOT NULL,
            user_id INT NOT NULL,
            nickname VARCHAR(50),
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (guild_id, user_id),
            FOREIGN KEY (guild_id) REFERENCES guilds(guild_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    
    # Re-enable foreign keys
    execute("SET FOREIGN_KEY_CHECKS = 1")
    
    # --- MIGRATION ---
    if fetch_one("SELECT COUNT(*) as c FROM guilds")['c'] > 0:
        print("⚠️ Data already exists. Skipping migration.")
        return

    print("🔄 Migrating Legacy Data...")
    
    # Get Owner
    owner = fetch_one("SELECT user_id FROM users LIMIT 1")
    if not owner: 
        print("No users found.")
        return
        
    owner_id = owner['user_id']
    
    # Create Default Guild
    execute("INSERT INTO guilds (name, owner_id) VALUES ('Legacy Community', %s)", (owner_id,))
    guild_id = fetch_one("SELECT LAST_INSERT_ID() as id")['id']
    print(f"   -> Legacy Guild ID: {guild_id}")
    
    # Categories
    execute("INSERT INTO categories (guild_id, name) VALUES (%s, 'Text Channels')", (guild_id,))
    cat_id = fetch_one("SELECT LAST_INSERT_ID() as id")['id']
    
    # Migrate Old Rooms
    try:
        old_rooms = fetch_all("SELECT * FROM chat_rooms")
        for room in old_rooms:
            # Skip private DMs for now or put them in NULL guild
            is_dm = (room['room_type'] == 'private')
            gid = None if is_dm else guild_id
            cid = None if is_dm else cat_id
            
            execute("""
                INSERT INTO channels (guild_id, category_id, name, topic, type)
                VALUES (%s, %s, %s, %s, 'text')
            """, (gid, cid, room['room_name'] or 'channel', room.get('description')))
            
            new_id = fetch_one("SELECT LAST_INSERT_ID() as id")['id']
            
            # Migrate Messages
            execute("UPDATE chat_messages SET room_id = %s WHERE room_id = %s", (new_id, room['room_id']))
            print(f"      - Room {room['room_id']} -> Channel {new_id}")
            
    except Exception as e:
        print(f"Migration Error: {e}")

    # Rename column in messages
    try:
        execute("ALTER TABLE chat_messages CHANGE room_id channel_id INT")
    except:
        pass # Might already be renamed

    print("✅ Done!")

if __name__ == "__main__":
    migrate_to_discord_schema()
