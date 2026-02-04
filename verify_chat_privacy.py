
from playwright.sync_api import sync_playwright
import time

def test_chat_privacy_toggle():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Run headless for speed, or False to watch
        context = browser.new_context()
        page = context.new_page()

        # 1. Login
        print("Logging in...")
        page.goto("http://127.0.0.1:5000/login")
        page.fill("input[name='email']", "admin@library.com") # Assuming admin account exists
        page.fill("input[name='password']", "admin123")
        page.click("button:has-text('Login')")
        page.wait_for_url("**/dashboard")
        
        # Go to Community
        print("Navigating to Community...")
        page.goto("http://127.0.0.1:5000/community")
        
        # 2. Create Public Group
        group_name = f"TestGroup_{int(time.time())}"
        print(f"Creating Public Group: {group_name}")
        page.click("button[title='Create Group']")
        page.fill("#newGroupName", group_name)
        page.select_option("#groupPrivacy", "public") # Public Hub
        page.click("button:has-text('Create Group')")
        
        # Wait for reload/update
        time.sleep(2)
        
        # 3. Verify in Public Tab
        print("Verifying in Public Tab...")
        page.click("#tab-public")
        time.sleep(1)
        if page.locator(f".chat-name:has-text('{group_name}')").is_visible():
            print("PASS: Group found in Public Tab")
        else:
            print("FAIL: Group NOT found in Public Tab")
            print(page.inner_html("#dynamicChatList"))
            return

        # 4. Switch to Private
        print("Switching to Private...")
        # Open settings for the new group (it should be active)
        page.click("#chatSettingsBtn")
        time.sleep(1)
        
        # Change type to Private
        page.select_option("#chatTypeSelect", "private")
        page.click("button:has-text('Save Changes')")
        
        # Handle alert
        # (Playwright handles dialogs automatically by dismissing, but we want to accept?)
        # Actually page.on('dialog') needs to be set up if we need to interact, but default dismissal might be issue if it's confirm.
        # But 'Save Changes' usually just alerts success.
        
        time.sleep(2) # Wait for fetchConversations
        
        # 5. Verify in Private Groups Tab
        print("Verifying in Private Groups Tab...")
        page.click("#tab-group") # Private Groups tab
        time.sleep(1)
        
        if page.locator(f".chat-name:has-text('{group_name}')").is_visible():
            print("PASS: Group found in Private Groups Tab")
        else:
            print("FAIL: Group NOT found in Private Groups Tab")
            # Check Public tab just in case
            page.click("#tab-public")
            if page.locator(f".chat-name:has-text('{group_name}')").is_visible():
                print("... But it is still in Public Tab!")
            else:
                 print("... And it is NOT in Public Tab either. It disappeared.")
            return

        # 6. Switch back to Public
        print("Switching back to Public...")
        # Since we are in the group tab and it's visible (hopefully), click it to make sure it's active
        # page.click(f".chat-name:has-text('{group_name}')") 
        # Open settings
        page.click("#chatSettingsBtn")
        time.sleep(1)
        
        page.select_option("#chatTypeSelect", "public")
        page.click("button:has-text('Save Changes')")
        time.sleep(2)
        
        # 7. Verify in Public Tab
        print("Verifying in Public Tab (After Revert)...")
        page.click("#tab-public")
        time.sleep(1)
        
        if page.locator(f".chat-name:has-text('{group_name}')").is_visible():
            print("PASS: Group returned to Public Tab")
        else:
             print("FAIL: Group NOT found in Public Tab after revert")
             
        browser.close()

if __name__ == "__main__":
    try:
        test_chat_privacy_toggle()
    except Exception as e:
        print(f"Test Error: {e}")
