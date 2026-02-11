from playwright.sync_api import sync_playwright
import time

TARGET_URL = "https://app.ssby.cc/#/"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"Navigating to {TARGET_URL}...")
        page.goto(TARGET_URL)
        
        print("\n*** 请手动登录并进入聊天界面 ***")
        input("进入聊天界面后，请按回车键继续...")

        # Dump HTML
        html_content = page.content()
        with open("chat_page_source.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print("Page source saved to chat_page_source.html")
        
        # Also try to find frames if any
        for frame in page.frames:
            try:
                print(f"Dumping frame: {frame.url}")
                with open(f"frame_{frame.name or 'main'}.html", "w", encoding="utf-8") as f:
                    f.write(frame.content())
            except Exception as e:
                print(f"Could not dump frame: {e}")

        browser.close()

if __name__ == "__main__":
    run()
