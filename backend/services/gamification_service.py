
from backend.repository.db_access import fetch_all, fetch_one, execute
from datetime import datetime

def get_user_stats(user_id):
    """Fetches user's level, XP, and earned badges."""
    stats = fetch_one("SELECT * FROM user_profile_stats WHERE user_id = %s", (user_id,))
    if not stats:
        # Lazy initialization
        execute("INSERT IGNORE INTO user_profile_stats (user_id) VALUES (%s)", (user_id,))
        stats = {'user_id': user_id, 'xp': 0, 'level': 1}
    
    badges = fetch_all("""
        SELECT b.* FROM badges b
        JOIN user_achievements ua ON b.badge_id = ua.badge_id
        WHERE ua.user_id = %s
    """, (user_id,))
    
    return {
        "xp": stats['xp'],
        "level": stats['level'],
        "badges": badges,
        "xp_to_next": stats['level'] * 100  # XP needed for NEXT level relative to current
    }

def award_xp(user_id, amount, reason=""):
    """Adds XP to a user and checks for level up."""
    execute("UPDATE user_profile_stats SET xp = xp + %s WHERE user_id = %s", (amount, user_id))
    
    # Check for level up
    stats = fetch_one("SELECT xp, level FROM user_profile_stats WHERE user_id = %s", (user_id,))
    current_xp = stats['xp']
    current_level = stats['level']
    
    # Formula: XP for level L = (L-1)*L/2 * 100
    # Let's simplify: Level = 1 + floor(sqrt(xp / 50))? No.
    # We will just iterate to see if they leveled up.
    new_level = current_level
    while True:
        xp_needed_for_next = (new_level * (new_level + 1) / 2) * 100
        if current_xp >= xp_needed_for_next:
            new_level += 1
        else:
            break
            
    if new_level > current_level:
        execute("UPDATE user_profile_stats SET level = %s WHERE user_id = %s", (new_level, user_id))
        from backend.services.notification_service import add_notification
        add_notification(user_id, f"🎉 Level Up! You are now Level {new_level}!")
        
    # Check if this qualifies for any badges
    check_for_badges(user_id)
    return True

def check_for_badges(user_id):
    """Evaluates if user qualifies for any unearned badges."""
    # 1. First Borrow (check if user has at least 1 record in issues)
    # 2. Knowledge Seeker (10 unique books)
    # 3. Socialite (check users.is_public)
    # 4. Library Legend (Level 10)
    
    # Fetch unearned badges
    unearned = fetch_all("""
        SELECT * FROM badges 
        WHERE badge_id NOT IN (SELECT badge_id FROM user_achievements WHERE user_id = %s)
    """, (user_id,))
    
    for badge in unearned:
        earned = False
        if badge['name'] == "First Borrow":
            res = fetch_one("SELECT COUNT(*) as cnt FROM issues WHERE user_id = %s", (user_id,))
            if res['cnt'] > 0: earned = True
            
        elif badge['name'] == "Knowledge Seeker":
            res = fetch_one("SELECT COUNT(DISTINCT book_id) as cnt FROM issues WHERE user_id = %s", (user_id,))
            if res['cnt'] >= 10: earned = True
            
        elif badge['name'] == "Socialite":
            res = fetch_one("SELECT is_public FROM users WHERE user_id = %s", (user_id,))
            if res and res['is_public']: earned = True
            
        elif badge['name'] == "Quick Reader":
            res = fetch_one("""
                SELECT COUNT(*) as cnt FROM issues 
                WHERE user_id = %s AND return_date IS NOT NULL 
                AND DATEDIFF(return_date, issue_date) <= 3
            """, (user_id,))
            if res['cnt'] > 0: earned = True
            
        elif badge['name'] == "Library Legend":
            res = fetch_one("SELECT level FROM user_profile_stats WHERE user_id = %s", (user_id,))
            if res and res['level'] >= 10: earned = True
            
        if earned:
            execute("INSERT IGNORE INTO user_achievements (user_id, badge_id) VALUES (%s, %s)", (user_id, badge['badge_id']))
            from backend.services.notification_service import add_notification
            add_notification(user_id, f"🏆 Achievement Unlocked: {badge['icon']} {badge['name']}!")
            
            from backend.services.activity_service import log_user_activity
            log_user_activity(user_id, "BADGE", f"Earned the {badge['name']} badge! {badge['icon']}")

def get_leaderboard():
    """Returns top 10 players based on level and XP."""
    return fetch_all("""
        SELECT u.name, ups.level, ups.xp 
        FROM user_profile_stats ups
        JOIN users u ON ups.user_id = u.user_id
        ORDER BY ups.level DESC, ups.xp DESC
        LIMIT 10
    """)
    
def get_user_badges(user_id):
    """Fetches just the badges of a user."""
    return fetch_all("""
        SELECT b.* FROM badges b
        JOIN user_achievements ua ON b.badge_id = ua.badge_id
        WHERE ua.user_id = %s
    """, (user_id,))
