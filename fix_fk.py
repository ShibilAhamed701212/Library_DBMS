
import os
import sys
sys.path.append(os.getcwd())
from backend.repository.db_access import execute

try:
    print("Dropping old foreign key...")
    execute("ALTER TABLE chat_messages DROP FOREIGN KEY chat_messages_ibfk_1")
    print("Adding new foreign key to channels...")
    execute("ALTER TABLE chat_messages ADD CONSTRAINT fk_channel FOREIGN KEY (channel_id) REFERENCES channels(channel_id) ON DELETE CASCADE")
    print("Done!")
except Exception as e:
    print(f"Error: {e}")
