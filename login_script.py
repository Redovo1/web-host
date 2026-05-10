from playwright.sync_api import sync_playwright
import os


def login_webhost(email, password):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        # 访问登录页面
        page.goto("https://client.webhostmost.com/login")

        # 输入邮箱和密码
        page.get_by_placeholder("Enter email").fill(email)
        page.get_by_placeholder("Password").fill(password)

        # 点击登录按钮
        page.get_by_role("button", name="Login").click()

        try:
            # 尝试等待错误提示
            error_message = page.wait_for_selector('.MuiAlert-message', timeout=5000)
            error_text = error_message.inner_text()
            return f"账号 `{email}` 登录失败: {error_text}"
        except Exception:
            # 未出现错误提示，判断是否成功跳转
            try:
                page.wait_for_url("https://client.webhostmost.com/clientarea.php", timeout=5000)
                return f"账号 `{email}` 登录成功 ✅"
            except Exception:
                return f"账号 `{email}` 登录失败: 未跳转到仪表板页面 ❌"
        finally:
            browser.close()


if __name__ == "__main__":
    accounts_raw = os.environ.get('WEBHOST')
    if not accounts_raw:
        print("未配置任何 WEBHOST 账号")
        exit(1)

    accounts = accounts_raw.strip().split()
    login_statuses = []
    has_failure = False

    for account in accounts:
        try:
            email, password = account.split(':', 1)
            status = login_webhost(email, password)
            login_statuses.append(status)
            print(status)
            if "登录失败" in status:
                has_failure = True
        except ValueError:
            msg = f"账号格式错误: `{account}`，请使用 email:password 格式"
            login_statuses.append(msg)
            print(msg)
            has_failure = True

    print("\n==== WEBHOST 登录状态汇总 ====")
    for s in login_statuses:
        print(s)

    # 有任一账号失败时以非零状态退出，方便在 Actions 里醒目失败
    if has_failure:
        exit(1)
