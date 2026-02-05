
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
    
    
    # Calculate Rank and Perks based on Level
    level = stats['level']
    rank_title = "Reader"
    next_perk = "None"
    
    if level < 5:
        rank_title = "Novice Page-Turner"
        next_perk = "Bronze Border"
    elif level < 10:
        rank_title = "Apprentice Scholar"
        next_perk = "Silver Border & 5% XP Boost"
    elif level < 20:
        rank_title = "Library Guardian"
        next_perk = "Gold Border & 10% XP Boost"
    else:
        rank_title = "Grand Archivist"
        next_perk = "Living Legend Status"

    return {
        "xp": stats['xp'],
        "level": stats['level'],
        "badges": badges,
        "xp_to_next": stats['level'] * 100,
        "rank_title": rank_title,
        "next_perk": next_perk
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
    
    # --- DYNAMIC RULE ENGINE ---
    # Fetch unearned badges that have rules
    unearned_dynamic = fetch_all("""
        SELECT * FROM badges 
        WHERE rule_type IS NOT NULL 
        AND badge_id NOT IN (SELECT badge_id FROM user_achievements WHERE user_id = %s)
    """, (user_id,))
    
    # Pre-fetch stats to avoid N+1 queries
    # 1. Total Reads
    res_reads = fetch_one("SELECT COUNT(*) as cnt FROM issues WHERE user_id = %s", (user_id,))
    total_reads = res_reads['cnt'] if res_reads else 0
    
    # 2. Total Reviews (Assuming 'reviews' table exists, otherwise handle gracefully)
    try:
        res_reviews = fetch_one("SELECT COUNT(*) as cnt FROM reviews WHERE user_id = %s", (user_id,))
        total_reviews = res_reviews['cnt'] if res_reviews else 0
    except:
        total_reviews = 0 # Table might not exist yet
        
    # 3. Unique Genres
    res_genres = fetch_one("""
        SELECT COUNT(DISTINCT b.genre) as cnt 
        FROM issues i 
        JOIN books b ON i.book_id = b.book_id 
        WHERE i.user_id = %s
    """, (user_id,))
    unique_genres = res_genres['cnt'] if res_genres else 0
    
    # 4. Member Days
    res_days = fetch_one("SELECT DATEDIFF(NOW(), join_date) as days FROM users WHERE user_id = %s", (user_id,))
    member_days = res_days['days'] if res_days else 0

    for badge in unearned_dynamic:
        earned = False
        rtype = badge.get('rule_type')
        rval = badge.get('rule_value', 0) or 0 # Handle None/Null safely
        
        if rtype == 'total_reads':
            if total_reads >= rval: earned = True
            
        elif rtype == 'total_reviews':
            if total_reviews >= rval: earned = True
            
        elif rtype == 'unique_genres':
            if unique_genres >= rval: earned = True
            
        elif rtype == 'days_member':
            if member_days >= rval: earned = True
            
        if earned:
            execute("INSERT IGNORE INTO user_achievements (user_id, badge_id) VALUES (%s, %s)", (user_id, badge['badge_id']))
            from backend.services.notification_service import add_notification
            add_notification(user_id, f"🏆 Achievement Unlocked: {badge['icon']} {badge['name']}!")
            
            # Award XP if associated with badge
            if badge.get('xp_required') and badge['xp_required'] > 0:
                 execute("UPDATE user_profile_stats SET xp = xp + %s WHERE user_id = %s", (badge['xp_required'], user_id))
                 
            from backend.services.activity_service import log_user_activity
            log_user_activity(user_id, "BADGE", f"Earned the {badge['name']} badge! {badge['icon']}")

    # --- LEGACY / SPECIAL LOGIC ---
    # Keep this for complex badges that can't be rule-based
    
    # Socialite (check users.is_public)
    # Check if Socialite is unearned
    unearned_legacy = fetch_all("""
        SELECT * FROM badges 
        WHERE name IN ('Socialite', 'Quick Reader', 'Library Legend')
        AND badge_id NOT IN (SELECT badge_id FROM user_achievements WHERE user_id = %s)
    """, (user_id,))
    
    for badge in unearned_legacy:
        earned = False
        if badge['name'] == "Socialite":
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
             # This could be a rule 'min_level', but keeping here for now
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

def get_all_achievements_status(user_id):
    """
    Returns ALL badges with a flag indicating if the user has unlocked them.
    Used for the dedicated "Trophy Room" page.
    """
    # 1. Fetch all badges
    all_badges = fetch_all("SELECT * FROM badges")
    
    # 2. Fetch user's unlocked badge IDs
    unlocked_ids = {
        row['badge_id'] 
        for row in fetch_all("SELECT badge_id FROM user_achievements WHERE user_id = %s", (user_id,))
    }
    
    # 3. Merge and formatting
    results = []
    for badge in all_badges:
        is_unlocked = badge['badge_id'] in unlocked_ids
        
        # Add unlock date if unlocked (Optional enhancement)
        unlocked_date = None
        if is_unlocked:
            res = fetch_one("SELECT earned_at FROM user_achievements WHERE user_id = %s AND badge_id = %s", (user_id, badge['badge_id']))
            if res: unlocked_date = res['earned_at']
            
        results.append({
            "badge_id": badge['badge_id'],
            "name": badge['name'],
            "description": badge['description'],
            "icon": badge['icon'],
            "criteria": badge.get('criteria', ''), # Assuming criteria column exists or is inferred
            "is_unlocked": is_unlocked,
            "earned_at": unlocked_date
        })
        
    return results
