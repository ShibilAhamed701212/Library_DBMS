
from backend.repository.db_access import execute_query, fetch_one, fetch_all

def get_all_settings():
    """Returns a dictionary of all system settings."""
    try:
        rows = fetch_all("SELECT setting_key, setting_value FROM settings")
        return {r['setting_key']: r['setting_value'] for r in rows}
    except:
        return {}

def get_setting(key, default=None):
    """Returns a single setting value."""
    try:
        res = fetch_one("SELECT setting_value FROM settings WHERE setting_key = %s", (key,))
        return res['setting_value'] if res else default
    except:
        return default

def is_maintenance_mode():
    return get_setting('maintenance_mode', 'false') == 'true'

def set_maintenance_mode(status: bool):
    val = 'true' if status else 'false'
    update_setting('maintenance_mode', val)
    return f"✅ Maintenance Mode set to {val}"

def update_setting(key, value):
    """Updates or inserts a setting key."""
    execute_query("INSERT INTO settings (setting_key, setting_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE setting_value = %s", (key, value, value))

def update_settings(settings_dict):
    """Updates multiple settings at once."""
    for key, val in settings_dict.items():
        update_setting(key, val)
    return "✅ Settings updated successfully."

def get_category_fines():
    return fetch_all("SELECT * FROM category_fines ORDER BY category")

def update_category_fine(category, rate):
    execute_query("INSERT INTO category_fines (category, daily_rate) VALUES (%s, %s) ON DUPLICATE KEY UPDATE daily_rate = %s", (category, rate, rate))
    return f"✅ Fine rate for '{category}' updated to ₹{rate}."

def delete_category_fine(category):
    execute_query("DELETE FROM category_fines WHERE category = %s", (category,))
    return f"✅ Fine rate for '{category}' removed."
