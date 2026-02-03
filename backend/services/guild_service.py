from backend.repository.db_access import execute, fetch_one, fetch_all

def create_guild(owner_id, name, description=None, icon_url=None):
    """Creates a new Guild (Server) and adds owner."""
    execute("""
        INSERT INTO guilds (owner_id, name, description, icon_url)
        VALUES (%s, %s, %s, %s)
    """, (owner_id, name, description, icon_url))
    
    guild_id = fetch_one("SELECT LAST_INSERT_ID() as id")['id']
    
    # Add owner as member
    execute("INSERT INTO guild_members (guild_id, user_id) VALUES (%s, %s)", (guild_id, owner_id))
    
    # Create Default Categories and Channels
    execute("INSERT INTO categories (guild_id, name, position) VALUES (%s, 'Text Channels', 0)", (guild_id,))
    cat_id = fetch_one("SELECT LAST_INSERT_ID() as id")['id']
    
    execute("INSERT INTO channels (guild_id, category_id, name, type) VALUES (%s, %s, 'general', 'text')", (guild_id, cat_id))
    
    return guild_id

def get_my_guilds(user_id):
    """Returns all guilds the user is a member of."""
    return fetch_all("""
        SELECT g.* 
        FROM guilds g
        JOIN guild_members m ON g.guild_id = m.guild_id
        WHERE m.user_id = %s
    """, (user_id,))

def get_guild_details(guild_id):
    """Returns full guild hierarchy (Categories -> Channels)."""
    guild = fetch_one("SELECT * FROM guilds WHERE guild_id = %s", (guild_id,))
    if not guild: return None
    
    categories = fetch_all("SELECT * FROM categories WHERE guild_id = %s ORDER BY position", (guild_id,))
    channels = fetch_all("SELECT * FROM channels WHERE guild_id = %s ORDER BY position", (guild_id,))
    
    # Hierarchy Assembly
    grid = []
    
    # Uncategorized channels first
    uncategorized = [c for c in channels if not c['category_id']]
    if uncategorized:
        grid.append({'id': 'null', 'name': 'Channels', 'channels': uncategorized})
        
    for cat in categories:
        cat_channels = [c for c in channels if c['category_id'] == cat['category_id']]
        grid.append({
            'id': cat['category_id'],
            'name': cat['name'],
            'channels': cat_channels
        })
        
    return {
        'guild': guild,
        'hierarchy': grid
    }
