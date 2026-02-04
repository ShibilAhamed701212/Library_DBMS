
from backend.services.channel_service import create_channel
from backend.repository.db_access import execute

# Mock setup if needed, but we can just use DB directly as we are on backend
print("🧪 Testing Channel Creation fix...")

# Create a test channel (NULL guild for global/public test)
try:
    # Use a dummy guild_id if foreign key constraint exists, or None if nullable
    # Assuming guild_id can be NULL for public hub based on earlier schema analysis
    # If fails, we might need a valid guild. Let's try to create one first or use '1' if we know it exists.
    # Actually, create_channel(guild_id, category, name...)
    # We'll use 0 or None.
    
    cid = create_channel(None, None, "Test Channel Fix", "text", "Testing ID Return")
    
    print(f"✅ Returned Channel ID: {cid}")
    
    if cid and cid > 0:
        print("✅ SUCCESS: create_channel returning valid ID")
        # Cleanup
        execute("DELETE FROM channels WHERE channel_id = %s", (cid,))
        print("🧹 Cleanup complete")
    else:
        print(f"❌ FAILURE: create_channel returned invalid ID: {cid}")
        
except Exception as e:
    print(f"❌ EXCEPTION: {e}")
