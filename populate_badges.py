from backend.config.db import get_connection
import random

BADGES = []

# 1. READING MILESTONES (Count)
# Rule Type: 'total_reads'
reads = [1, 5, 10, 25, 50, 100, 250, 500, 1000]
titles = ["Page Turner", "Bookworm", "Bibliophile", "Library Regular", "Scholar", "Sage", "Grand Archivist", "Legendary Reader", "Mythic Reader"]
icons = ["📖", "🐛", "📚", "🏛️", "🎓", "🔮", "🏰", "🌟", "👑"]

for i, count in enumerate(reads):
    BADGES.append({
        "name": f"{titles[i]}",
        "description": f"Read {count} books.",
        "icon": icons[i],
        "xp": count * 10,
        "rule_type": "total_reads",
        "rule_value": count
    })

# 2. REVIEW MILESTONES
# Rule Type: 'total_reviews'
reviews = [1, 5, 10, 25, 50, 100]
r_titles = ["Voice", "Critic", "Reviewer", "Pundit", "Influence", "Taste Maker"]
r_icons = ["🗣️", "✍️", "📝", "📢", "🌟", "💎"]

for i, count in enumerate(reviews):
    BADGES.append({
        "name": f"{r_titles[i]}",
        "description": f"Wrote {count} reviews.",
        "icon": r_icons[i],
        "xp": count * 15,
        "rule_type": "total_reviews",
        "rule_value": count
    })

# 3. GENRE EXPLORER (Simplified to generic 'unique_genres' for now or hardcoded)
# Let's add Generic Genre counts: Read from 3 different genres, 5, 10...
# Rule Type: 'unique_genres'
genres = [3, 5, 10, 15]
g_titles = ["Curious", "Explorer", "Diverse Reader", "Renaissance Mind"]
g_icons = ["🧭", "🌎", "🌈", "🧠"]

for i, count in enumerate(genres):
    BADGES.append({
        "name": f"{g_titles[i]}",
        "description": f"Read books from {count} different genres.",
        "icon": g_icons[i],
        "xp": count * 50,
        "rule_type": "unique_genres",
        "rule_value": count
    })
    
# 4. SOCIALITE (Public Profile) -> Already exists usually, let's skip or handle manually.

# 5. STREAKS (Consecutive Days - harder to track without daily logs, stick to simple counts first)
# How about 'Member for X Days'?
# Rule Type: 'days_member'
days = [30, 90, 180, 365, 730]
d_titles = ["Newcomer", "Regular", "Established", "Yearling", "Veteran"]
d_icons = ["🌱", "🌿", "🌳", "🎂", "🏅"]
for i, count in enumerate(days):
    BADGES.append({
        "name": f"{d_titles[i]}",
        "description": f"Member for {count} days.",
        "icon": d_icons[i],
        "xp": 100 * (i+1),
        "rule_type": "days_member",
        "rule_value": count
    })


def populate():
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"Preparing to insert {len(BADGES)} badges...")
    
    for b in BADGES:
        # Check if exists by name to avoid duplicates
        cursor.execute("SELECT badge_id FROM badges WHERE name = %s", (b['name'],))
        if cursor.fetchone():
            print(f"Skipping {b['name']} (Exists)")
            # Optional: Update rule if missing
            cursor.execute("UPDATE badges SET rule_type=%s, rule_value=%s WHERE name=%s AND rule_type IS NULL", 
                           (b['rule_type'], b['rule_value'], b['name']))
            continue
            
        cursor.execute("""
            INSERT INTO badges (name, description, icon, xp_required, rule_type, rule_value, requirement_type, requirement_value)
            VALUES (%s, %s, %s, %s, %s, %s, 'auto', 0)
        """, (b['name'], b['description'], b['icon'], b['xp'], b['rule_type'], b['rule_value']))
        print(f"Inserted {b['name']}")
        
    conn.commit()
    conn.close()
    print("Done!")

if __name__ == "__main__":
    populate()
