
from backend.repository.db_access import fetch_one, execute, fetch_all

def get_user_tier(user_id):
    """Returns the membership tier of a user (Silver, Gold, or Platinum)."""
    res = fetch_one("SELECT tier FROM users WHERE user_id = %s", (user_id,))
    return res['tier'] if (res and res['tier']) else 'Silver'

def get_tier_config(tier):
    """Returns the borrowing limits and duration (max_books, loan_days) for a given tier."""
    from backend.services.settings_service import get_setting
    
    # Fetch global defaults for base tier (Silver)
    default_max = int(get_setting('max_books_per_user', 3))
    default_days = int(get_setting('default_issue_days', 7))

    configs = {
        'Silver': {'max_books': default_max, 'loan_days': default_days},
        'Gold': {'max_books': 6, 'loan_days': 21},
        'Platinum': {'max_books': 10, 'loan_days': 30}
    }
    return configs.get(tier, configs['Silver'])

def get_user_membership_config(user_id):
    """Returns the membership configuration for a specific user based on their tier."""
    tier = get_user_tier(user_id)
    config = get_tier_config(tier)
    if not config:
        # Default fallback to Silver if config is missing (safety)
        return {'tier': 'Silver', 'max_books': 3, 'loan_days': 14}
    return config

def update_user_tier(user_id, new_tier):
    """Updates a user's membership tier."""
    valid_tiers = ['Silver', 'Gold', 'Platinum']
    if new_tier not in valid_tiers:
        return "❌ Invalid tier"
    execute("UPDATE users SET tier = %s WHERE user_id = %s", (new_tier, user_id))
    return f"✅ User {user_id} updated to {new_tier}"

def get_all_tiers():
    """Returns all available membership configurations."""
    return [
        {'tier': 'Silver', 'max_books': 3, 'loan_days': 14},
        {'tier': 'Gold', 'max_books': 6, 'loan_days': 21},
        {'tier': 'Platinum', 'max_books': 10, 'loan_days': 30}
    ]
