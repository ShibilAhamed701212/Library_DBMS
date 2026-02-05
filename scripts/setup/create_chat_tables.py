from backend.repository.db_access import execute_query

print("Creating chat_rooms table...")
execute_query("""
CREATE TABLE IF NOT EXISTS chat_rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_official BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
);
""")

print("Creating chat_messages table...")
execute_query("""
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES chat_rooms(room_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
""")

print("Seeding initial room...")
execute_query("""
INSERT IGNORE INTO chat_rooms (room_id, name, description, is_official) 
VALUES (1, 'General Lounge', 'The main lobby for all library members. Say hello!', TRUE);
""")

print("Done!")
