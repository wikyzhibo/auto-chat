import time
from playwright.sync_api import sync_playwright

# Configuration
TARGET_URL = "https://app.ssby.cc/#/"
USERNAME = "18077598368"
PASSWORD = "huangjunjie888"

# Selectors (Best guess based on UniApp structure and analysis)
# We will verify these dynamically
SELECTORS = {
    "login_user": "input[type='text'], input[placeholder*='账号'], input[placeholder*='Phone']",
    "login_pass": "input[type='password']",
    "login_btn": "button, .submit-btn",
    "chat_input": "textarea, input.uni-input-input, .input-box", 
    "send_btn": "text=发送",
    "msg_container": ".chat-scroll-view, .chat-container",
    "msg_item": ".chat-item, .message-content, uni-text" # General text catch
}

def login(page):
    print("Navigating to login page...")
    page.goto(TARGET_URL)
    page.wait_for_load_state("networkidle")
    time.sleep(3) # Wait for splash

    def safe_click(text_or_selector, desc):
        try:
            print(f"[Login] Trying: {desc} ({text_or_selector})")
            # Try specific text first
            elem = page.locator(text_or_selector).first
            if elem.is_visible(timeout=3000):
                elem.click()
                time.sleep(1) # Pace the interaction
                return True
        except:
            pass
        return False

    # 1. Gender Selection
    safe_click("text=我是男生", "Select Gender")
    
    # 2. Agreement
    safe_click("text=同意并接受", "Agree Protocol")

    # 3. 'Pick a bottle' (Main entry)
    safe_click("text=捡一个瓶子", "Start Button")

    # 4. Age Selection
    safe_click("text=18-23", "Select Age")

    # 5. Enter Chat
    safe_click("text=进入聊天", "Enter Chat")

    # 6. Switch to 'Existing Account' / Login
    # This might be on a popup
    res = safe_click("text=点击登录", "Switch to Login")
    if not res:
        # Fallback: sometimes it says "已有账号"
        safe_click("text=已有账号", "Existing Account")

    # 7-9. Enter Credentials
    print("[Login] Entering credentials...")
    try:
        # Phone Input Strategy
        # Try multiple common selectors for phone field
        phone_selectors = [
            "input[type='tel']", 
            "input[placeholder*='手机']", 
            "input[maxlength='11']",
            "input[type='number']"
        ]
        
        phone_input = None
        for sel in phone_selectors:
            input_cand = page.locator(sel).first
            if input_cand.is_visible():
                phone_input = input_cand
                print(f"[Login] Found phone input via: {sel}")
                break
        
        if phone_input:
            phone_input.click()
            time.sleep(0.5)
            # Clear existing? 
            phone_input.fill("") 
            page.keyboard.type(USERNAME)
            time.sleep(0.5)
        else:
            print("[Login] Failed to find phone input field.")
        
        # Password
        # Sometimes default is SMS, check if we need to switch to password?
        # Assuming password field is visible or we find it
        password = page.locator("input[placeholder*='密码'], input[type='password']").first
        if password.is_visible():
            password.click()
            page.keyboard.type(PASSWORD)
            time.sleep(0.5)
        else:
            print("[Login] Password field not found? Trying to switch auth mode...")
            safe_click("text=密码登录", "Switch to Password Mode")
            time.sleep(1)
            password = page.locator("input[placeholder*='密码'], input[type='password']").first
            if password.is_visible():
                password.click()
                page.keyboard.type(PASSWORD)

        # 8. Check Agreement Box
        print("[Login] Checking agreement box...")
        try:
            # Strategy 1: Specific class from previous analysis (.checke-0 is the unchecked circle)
            # We look for it inside the visible dialog
            checkbox = page.locator(".checke-0, .icon-circle, uni-checkbox, .uni-checkbox-input").last
            if checkbox.is_visible():
                print("[Login] Found checkbox via class, clicking...")
                checkbox.click()
                time.sleep(0.5)
            else:
                # Strategy 2: Click the text itself (sometimes works)
                print("[Login] Clicking agreement text...")
                page.locator("text=我已阅读").first.click()
                time.sleep(0.5)
                
                # Strategy 3: Click offset from text (Backup)
                agreement_text = page.locator("text=我已阅读").first
                if agreement_text.is_visible():
                    box = agreement_text.bounding_box()
                    if box:
                        # Click 25px to the left of the text start
                        print("[Login] Clicking offset...")
                        page.mouse.click(box["x"] - 25, box["y"] + box["height"]/2)
                        time.sleep(0.5)
        except Exception as e:
            print(f"[Login] Error checking box: {e}")
        
        # 9. Click Login
        print("[Login] Looking for Login Button...")
        
        # Strategy: Use user-provided structure
        # <uni-view class="... bg-red-500 ..."> 登录 </uni-view>
        # We target the text '登录' inside a red styled container if possible, or just the text
        
        login_btn = None
        
        # 1. Exact text match inside uni-view
        # We look for '登录' that is visible and likely a button
        candidates = page.locator("uni-view:has-text('登录')").all()
        for cand in candidates:
             if cand.is_visible():
                 # Check if it has button-like classes (bg-red, w-3/5 etc)
                 # Or just take the last one (usually modal buttons are last in DOM)
                 login_btn = cand
        
        if not login_btn:
             # Fallback: specific class parts
             login_btn = page.locator(".bg-red-500:has-text('登录')").first

        if login_btn:
            print("[Login] Clicking Login Button...")
            # Just click the button. 
            time.sleep(0.5)
            login_btn.click(force=True)
            time.sleep(1)
        else:
            print("[Login] Login button NOT found. Trying generic click...")
            # Last resort: click the coordinate where the button usually IS
            # Center lower part of dialog?
            dialog = page.locator(".uni-popup__wrapper-box, .uni-popup").last
            if dialog.is_visible():
                box = dialog.bounding_box()
                if box:
                    # Click bottom center area of dialog
                    print("[Login] Clicking bottom area of dialog...")
                    page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"] - 50)
            
        page.wait_for_load_state("networkidle")
        
        # Check if login succeeded (redirected?)
        # If still on login page/popup visible, print warning
        if page.locator("text=登录").last.is_visible():
             print("[Warning] Login button still visible after click. Login likely failed (Agreement not checked?).")
        else:
             print("[Login] Login sequence completed.")

    except Exception as e:
        print(f"[Login] Critical error during credential entry: {e}")

def find_chat_elements(page):
    """
    Tries to locate the chat input and send button.
    Returns (input_locator, send_btn_locator) or (None, None).
    """
    try:
        # Try finding textarea first
        input_box = page.locator("textarea").first
        if not input_box.is_visible():
            # Fallback to input
            input_box = page.locator("input[confirm-type='send']").first
            if not input_box.is_visible():
                 input_box = page.locator(".input-box").first

        if input_box.is_visible():
            # Try finding send button
            # Usually '发送' text
            send_btn = page.locator("text=发送").first
            if not send_btn.is_visible():
                # Maybe an icon?
                 send_btn = page.locator(".send-btn, .btn-send").first
            
            return input_box, send_btn
    except:
        pass
    return None, None

def monitor_chat(page):
    print("\n[System] Waiting for you to open a chat window...")
    
    input_box = None
    send_btn = None
    
    # Wait loop for chat interface
    while True:
        input_box, send_btn = find_chat_elements(page)
        if input_box and input_box.is_visible():
            print("[System] Chat interface detected!")
            break
        # Also check if user wants to quit
        time.sleep(1)

    # Updated Selectors for Chat
    CHAT_SELECTORS = {
        "input": "textarea, input.uni-input-input, .input-box", 
        "send_btn": "text=发送, .send-btn, uni-button",
    }
    
    # Text to ignore (System labels)
    # Text to ignore (System labels)
    IGNORE_TEXT = {"举报", "已读", "送达", "已送达", "复制", "删除", "对方离开了", "绿色聊天", "对方正在输入", "对方正在输入...", "发送中"}

    last_msg_count = 0

    def get_messages(page):
        try:
            # Broad selector for any text in chat area
            # We filter for likely message content (non-empty strings)
            elements = page.locator(".chat-scroll-view uni-text span").all()
            msgs = []
            for e in elements:
                txt = e.inner_text().strip()
                # Filter out system labels and empty strings
                if txt and txt not in IGNORE_TEXT and not txt.startswith("绿色聊天") and "正在输入" not in txt:
                    msgs.append(txt)
            return msgs
        except:
            return []

    # Initial check
    monitor_text = get_messages(page)
    if monitor_text:
        print(f"[System] Connected. Found {len(monitor_text)} existing messages.")
        last_msg_count = len(monitor_text)

    # Conversation Sequence
    conversation_script = [
        "你好呀，还在吗？",
        "感觉很神奇哈哈",
        "你那边能看到我发的消息吗？",
        "今天过得怎么样？",
        "这个软件挺有意思的",
        "我回复可能有点慢",
        "你是哪里人啊？",
        "哈哈，这可太酷了",
        "感觉我们要聊不下去了",
        "好了，拜拜啦！"
    ]
    
    script_index = 0
    max_turns = 10
    
    print("\n[System] Starting automated conversation (10 turns).")
    print(f"[System] I will send the first message: {conversation_script[0]}\n")

    # Send first message immediately
    try:
        input_box = page.locator(CHAT_SELECTORS["input"]).first
        if input_box.is_visible():
            input_box.click()
            # Type text
            page.keyboard.type(conversation_script[0])
            # Force event to ensure model updates
            input_box.dispatch_event("input") 
            time.sleep(0.5)
            
            # Try finding send button with multiple selectors
            send_btn = page.locator("text=发送").first
            if not send_btn.is_visible():
                send_btn = page.locator(".send-btn, .icon-send").first
            
            if send_btn.is_visible():
                print("[Debug] Clicking Send Button...")
                send_btn.click()
            else:
                print("[Debug] Send button not visible, pressing Enter on input...")
                input_box.press("Enter")
            
            print(f"[Auto-Self]: {conversation_script[0]}")
            script_index += 1
    except Exception as e:
        print(f"[Error] Failed sending first msg: {e}")

    last_reply_count = last_msg_count

    while script_index < max_turns:
        if page.is_closed():
            print("\n[System] Browser window was closed. Exiting...")
            break

        # 1. READ: Check for new messages
        try:
            current_msgs = get_messages(page)
            # Only count VALID messages (filtering system ones happens in get_messages)
            
            # Detect IF opponent replied
            # We assume if the TOTAL message count increased, and the LAST message is NOT mine (simplified logic)
            # A better way: Check if the last message in current_msgs is different from what we sent
            
            if len(current_msgs) > last_msg_count:
                new_msg_text = current_msgs[-1]
                print(f"[New Msg]: {new_msg_text}")
                
                # Check if it was me (simple check)
                # But actually, get_messages returns everything.
                # So we just wait for *any* update.
                # To be true "turn-taking", we should check if the new message is NOT what we just sent.
                
                if new_msg_text != conversation_script[script_index-1]:
                    # Opponent replied! Time to send next.
                    print(f"[System] Opponent replied. Sending turn {script_index+1}...")
                    time.sleep(1) # Simulated think time
                    
                    next_text = conversation_script[script_index]
                    
                    # SEND LOGIC
                    input_box = page.locator(CHAT_SELECTORS["input"]).first
                    if input_box.is_visible():
                        input_box.click()
                        # Type text
                        page.keyboard.type(next_text)
                        # Force event
                        input_box.dispatch_event("input")
                        time.sleep(0.5)
                        
                        send_btn = page.locator("text=发送").first
                        if not send_btn.is_visible():
                            send_btn = page.locator(".send-btn, .icon-send").first
                        
                        if send_btn.is_visible():
                            print("[Debug] Clicking Send Button...")
                            send_btn.click()
                        else:
                            print("[Debug] Send button not visible, pressing Enter on input...")
                            input_box.press("Enter")
                        
                        print(f"[Auto-Self]: {next_text}")
                        script_index += 1
                    else:
                        print("[Error] Lost input box.")

                last_msg_count = len(current_msgs)
                
        except Exception as e:
             if "Target page, context or browser has been closed" in str(e):
                 print("\n[System] Browser connection lost.")
                 break
             pass

        time.sleep(1) 
    
    print("[System] Conversation finished.")

# --- Automation Logic ---

def leave_chat(page):
    """
    主动离开聊天：点击"离开" → 点击"确认离开"
    """
    print("[System] Leaving current chat...")
    leave_btn = page.locator("text=离开").first
    if leave_btn.is_visible():
        leave_btn.click()
        time.sleep(2)
        
        # 点击确认离开（弹窗中的按钮）
        try:
            confirm_btn = page.locator(".uni-modal__btn_primary").filter(has_text="确认离开").first
            if confirm_btn.is_visible():
                print("[System] Clicking '确认离开'...")
                confirm_btn.click()
                time.sleep(2)
                return
        except: pass
        
        # 备选：纯文字匹配
        try:
            confirm_btn = page.locator("text=确认离开").last
            if confirm_btn.is_visible():
                print("[System] Clicking '确认离开' (text fallback)...")
                confirm_btn.click()
                time.sleep(2)
        except: pass
            
    print("[System] Left chat.")

def click_rematch(page):
    """
    点击重新匹配按钮。点击后等待自动进入新聊天。
    """
    print("[System] Clicking '重新匹配'...")
    
    # 优先用 class
    btn = page.locator(".rematch-btn").first
    if not btn.is_visible():
        btn = page.locator("text=重新匹配").last
    
    if btn.is_visible():
        btn.click()
        print("[System] Waiting for new chat...")
        time.sleep(5)  # 等待系统自动匹配进入新聊天
    else:
        print("[Warning] Rematch button not found.")

def is_in_chat(page):
    """
    判断是否在聊天界面（有输入框 + 底部有"离开"按钮）。
    注意：不能只靠 text=离开 判断，因为"离开聊天"和"确认离开"也包含"离开"。
    关键判据：输入框可见。
    """
    try:
        input_box = page.locator("textarea, input.uni-input-input, .input-box").first
        if input_box.is_visible():
            return True
    except: pass
    return False

def is_on_rematch_page(page):
    """
    判断是否在"分享对话或重新匹配"页面。
    """
    try:
        if page.locator(".rematch-btn").first.is_visible():
            return True
        if page.locator("text=重新匹配").first.is_visible():
            return True
    except: pass
    return False

def is_partner_left(page):
    """
    判断对方是否已离开（页面出现"离开聊天"大按钮）。
    """
    try:
        btn = page.locator("text=离开聊天").last
        if btn.is_visible():
            return True
    except: pass
    return False

def chat_session(page):
    """
    管理一次聊天会话。
    返回: 'timeout', 'finished', 'partner_left', 'closed'
    """
    print("\n[Chat] Session started.")
    
    conversation_script = [
        "你好呀，还在吗？",
        "感觉很神奇哈哈",
        "你那边能看到我发的消息吗？",
        "今天过得怎么样？",
        "这个软件挺有意思的",
        "我回复可能有点慢",
        "你是哪里人啊？",
        "哈哈，这可太酷了",
        "感觉我们要聊不下去了",
        "好了，拜拜啦！"
    ]
    
    script_index = 0
    max_turns = len(conversation_script)
    TIMEOUT_SECONDS = 30
    last_action_time = time.time()
    
    IGNORE_TEXT = {"举报", "已读", "送达", "已送达", "复制", "删除", "对方离开了", 
                   "绿色聊天", "对方正在输入", "对方正在输入...", "发送中", "点击重试"}

    # 发送第一条消息
    try:
        input_box = page.locator("textarea, input.uni-input-input, .input-box").first
        if input_box.is_visible():
            input_box.click()
            page.keyboard.type(conversation_script[0])
            input_box.dispatch_event("input")
            time.sleep(0.5)
            
            send_btn = page.locator("text=发送").first
            if not send_btn.is_visible():
                 send_btn = page.locator(".send-btn, .icon-send").first
            
            if send_btn.is_visible():
                send_btn.click()
            else:
                input_box.press("Enter")
                
            print(f"[Auto-Self]: {conversation_script[0]}")
            script_index += 1
            last_action_time = time.time()
    except Exception as e:
        print(f"[Error] First msg failed: {e}")

    last_msg_count = 0
    try:
         elements = page.locator(".chat-scroll-view uni-text span").all()
         last_msg_count = len([e for e in elements if e.inner_text().strip()])
    except: pass

    while script_index < max_turns:
        if page.is_closed(): return "closed"
        
        # 超时检测
        if time.time() - last_action_time > TIMEOUT_SECONDS:
            print(f"[Chat] Timeout! No reply for {TIMEOUT_SECONDS}s.")
            return "timeout"
        
        # 对方离开检测：页面出现"离开聊天"按钮
        if is_partner_left(page):
            print("[Chat] Partner left! Clicking '离开聊天'...")
            try:
                page.locator("text=离开聊天").last.click()
                time.sleep(2)
            except: pass
            return "partner_left"
        
        # 重新匹配页检测（可能对方离开后直接跳到这里）
        if is_on_rematch_page(page):
            print("[Chat] Rematch page detected mid-chat.")
            return "partner_left"

        # 检查新消息
        try:
            elements = page.locator(".chat-scroll-view uni-text span").all()
            msgs = []
            for e in elements:
                txt = e.inner_text().strip()
                if txt and txt not in IGNORE_TEXT and not txt.startswith("绿色聊天") and "正在输入" not in txt and "点击重试" not in txt:
                    msgs.append(txt)
            
            current_count = len(msgs)
            
            if current_count > last_msg_count:
                new_msg = msgs[-1]
                print(f"[New Msg]: {new_msg}")
                
                if new_msg != conversation_script[script_index-1]:
                    print("[Chat] Opponent replied. Replying...")
                    time.sleep(1)
                    
                    next_text = conversation_script[script_index]
                    input_box = page.locator("textarea, input.uni-input-input, .input-box").first
                    if input_box.is_visible():
                        input_box.click()
                        page.keyboard.type(next_text)
                        input_box.dispatch_event("input")
                        time.sleep(0.5)
                        
                        send_btn = page.locator("text=发送").first
                        if not send_btn.is_visible():
                            send_btn = page.locator(".send-btn, .icon-send").first
                        
                        if send_btn.is_visible():
                            send_btn.click()
                        else:
                            input_box.press("Enter")
                        
                        print(f"[Auto-Self]: {next_text}")
                        script_index += 1
                        last_action_time = time.time()
                
                last_msg_count = current_count
                
        except Exception as e:
            pass
            
        time.sleep(1)
    
    print("[Chat] Script finished for this session.")
    return "finished"

def run_automation_loop(page):
    """
    主循环状态机。
    
    状态检测优先级（从高到低）：
    1. 重新匹配页（有"重新匹配"按钮）→ 点击重新匹配
    2. 对方已离开（有"离开聊天"按钮）→ 点击离开聊天
    3. 聊天中（有输入框）→ 进入聊天会话
    4. 其他 → 短暂等待
    """
    print("\n[System] Automation Loop Started. Press Ctrl+C to stop.")
    
    while True:
        try:
            if page.is_closed(): break
            
            # === 状态 1：重新匹配页 ===
            # 优先检测！因为这个页面可能也包含"离开"等文字
            if is_on_rematch_page(page):
                print("[State] Re-match page.")
                click_rematch(page)
                continue
            
            # === 状态 2：对方已离开（聊天界面中出现"离开聊天"按钮）===
            if is_partner_left(page):
                print("[State] Partner left.")
                try:
                    page.locator("text=离开聊天").last.click()
                    time.sleep(2)
                except: pass
                continue
                
            # === 状态 3：聊天中（输入框可见）===
            if is_in_chat(page):
                print("[State] In Chat.")
                result = chat_session(page)
                
                if result in ["timeout", "finished"]:
                    # 我方主动离开
                    leave_chat(page)
                elif result == "partner_left":
                    # 对方已离开，chat_session 内已点击"离开聊天"
                    # 接下来主循环会检测到重新匹配页
                    pass
                elif result == "closed":
                    break
                continue
            
            # === 状态 4：未识别页面 ===
            # 可能是页面加载中，短暂等待
            time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n[System] Stopping...")
            break
        except Exception as e:
            print(f"[Loop Error] {e}")
            time.sleep(2)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login(page)
        
        # 进入主循环
        run_automation_loop(page)
        
        browser.close()

if __name__ == "__main__":
    run()
