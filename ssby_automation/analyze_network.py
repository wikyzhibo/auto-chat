import json
import time
from playwright.sync_api import sync_playwright

LOG_FILE = "network_log.json"
TARGET_URL = "https://app.ssby.cc/#/"
USERNAME = "18077598368"
PASSWORD = "huangjunjie888"

captured_requests = []

def log_request(request):
    try:
        if request.resource_type in ["xhr", "fetch", "websocket"]:
            entry = {
                "url": request.url,
                "method": request.method,
                "headers": request.headers,
                "post_data": request.post_data,
                "type": request.resource_type
            }
            captured_requests.append(entry)
            print(f"Captured {request.method}: {request.url}")
    except Exception as e:
        print(f"Error logging request: {e}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Subscribe to network events
        page.on("request", log_request)

        print(f"Navigating to {TARGET_URL}...")
        page.goto(TARGET_URL)
        
        # Helper to wait
        page.wait_for_load_state("networkidle")
        
        print("Attempting to fill login form...")
        try:
            # Try generic selectors first, specific ones might be needed if these fail
            # Based on inspection or common patterns
            page.fill("input[type='text'], input[placeholder*='账号'], input[placeholder*='Phone']", USERNAME)
            page.fill("input[type='password']", PASSWORD)
            
            # Click login button
            page.click("button, input[type='submit'], .login-btn") 
            print("Submitted login form.")
        except Exception as e:
            print(f"Auto-login attempt failed (might need manual intervention): {e}")
            print("Please log in manually if needed.")

        print("\n*** 请在浏览器中操作 ***")
        print("1. 登录 (如果未自动登录)")
        print("2. 进入聊天界面")
        print("3. 发送任意消息")
        print("\n*** 操作完成后，请在控制台按回车键结束 ***")
        
        input("按回车键保存并退出...")

        # Capture Storage
        try:
            local_storage = page.evaluate("() => JSON.stringify(localStorage)")
            session_storage = page.evaluate("() => JSON.stringify(sessionStorage)")
            cookies = context.cookies()
            
            storage_data = {
                "localStorage": json.loads(local_storage) if local_storage else {},
                "sessionStorage": json.loads(session_storage) if session_storage else {},
                "cookies": cookies
            }
            
            # Save storage data separately
            with open("storage_dump.json", "w", encoding="utf-8") as f:
                json.dump(storage_data, f, indent=2, ensure_ascii=False)
            print("Storage dumped to storage_dump.json")
            
        except Exception as e:
            print(f"Error dumping storage: {e}")

        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(captured_requests, f, indent=2, ensure_ascii=False)
        
        print(f"\nNetwork traffic saved to {LOG_FILE}")
        browser.close()

if __name__ == "__main__":
    run()
