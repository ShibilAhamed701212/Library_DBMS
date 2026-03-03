from backend.repository.db_access import execute, fetch_all, fetch_one
import sys

def silent_setup():
    print("Initializing Gamification...")
    # Badges
    badges = [
        ('Knowledge Seeker', 'Borrow 5 unique books', '📚', 'total_reads', 5, 'total_reads', 5),
        ('Library Legend', 'Reach Level 10', '💎', 'min_level', 10, 'min_level', 10),
        ('Quick Reader', 'Return a book within 3 days', '⚡', 'quick_return', 1, 'quick_return', 1),
        ('Socialite', 'Make your profile public', '🌐', 'is_public', 1, 'is_public', 1),
        ('Critic', 'Submit 5 book reviews', '✍️', 'total_reviews', 5, 'total_reviews', 5),
        ('Diverse Reader', 'Explore 5 different categories', '🌈', 'unique_genres', 5, 'unique_genres', 5)
    ]
    
    for name, desc, icon, rtype, rval, req_type, req_val in badges:
        existing = fetch_one("SELECT badge_id FROM badges WHERE name = %s", (name,))
        if not existing:
            execute("INSERT INTO badges (name, description, icon, rule_type, rule_value, requirement_type, requirement_value) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                   (name, desc, icon, rtype, rval, req_type, req_val))

    print("Checking membership tiers...")
    try:
        execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tier ENUM('Silver', 'Gold', 'Platinum') DEFAULT 'Silver'")
    except:
        pass # Handle if IF NOT EXISTS isn't supported or fails

    print("Setup complete.")

if __name__ == "__main__":
    silent_setup()
