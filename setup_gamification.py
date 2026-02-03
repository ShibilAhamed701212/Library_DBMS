
from backend.repository.db_access import execute, fetch_one

def setup_gamification():
    print("🚀 Initializing Gamification System...")
    
    # 1. Create table for user levels and XP
    execute("""
        CREATE TABLE IF NOT EXISTS user_profile_stats (
            user_id INT PRIMARY KEY,
            xp INT DEFAULT 0,
            level INT DEFAULT 1,
            last_award_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)

    # 2. Create badges table
    execute("""
        CREATE TABLE IF NOT EXISTS badges (
            badge_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            icon VARCHAR(255)
        )
    """)
    
    # Ensure xp_required exists
    try:
        execute("ALTER TABLE badges ADD COLUMN xp_required INT DEFAULT 0")
    except:
        pass

    # 3. Create user_achievements bridge table
    execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            achievement_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            badge_id INT,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (badge_id) REFERENCES badges(badge_id) ON DELETE CASCADE,
            UNIQUE(user_id, badge_id)
        )
    """)

    # 4. Seed initial badges
    initial_badges = [
        ("First Borrow", "Borrow your very first book from the library.", "📖", 0),
        ("Quick Reader", "Return a book within 3 days.", "⚡", 50),
        ("Socialite", "Make your reading profile public.", "🌐", 20),
        ("Knowledge Seeker", "Borrow 10 unique books.", "🧠", 200),
        ("Library Legend", "Reach Level 10.", "👑", 1000)
    ]
    
    for name, desc, icon, xp in initial_badges:
        execute("INSERT IGNORE INTO badges (name, description, icon, xp_required) VALUES (%s, %s, %s, %s)", (name, desc, icon, xp))
    
    # 5. Initialize stats for existing users
    execute("INSERT IGNORE INTO user_profile_stats (user_id) SELECT user_id FROM users")
    print("✅ Gamification initialized successfully.")

if __name__ == "__main__":
    setup_gamification()
