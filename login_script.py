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


def collect_accounts():
    """
    收集账号，支持两种方式（都配置也可以，会一起跑）：

    1) 多 Secret 方式（推荐）：
       WEBHOST_1 = email1:password1
       WEBHOST_2 = email2:password2
       ...
       （脚本会自动查找所有 WEBHOST_ 开头的环境变量）

    2) 兼容老方式：
       WEBHOST = email1:password1
                 email2:password2
                 ...
    """
    accounts = []

    # 1) 读取所有 WEBHOST_* 的环境变量
    multi = []
    for key, value in os.environ.items():
        if key.startswith("WEBHOST_") and value.strip():
            multi.append((key, value.strip()))
    # 按名字排序，保证 WEBHOST_1 在 WEBHOST_2 之前
    multi.sort(key=lambda kv: kv[0])
    for _, value in multi:
        # 每个 secret 里也允许多行
        for line in value.splitlines():
            line = line.strip()
            if line:
                accounts.append(line)

    # 2) 兼容老的 WEBHOST（可选）
    legacy = os.environ.get("WEBHOST", "").strip()
    if legacy:
        for line in legacy.split():
            line = line.strip()
            if line:
                accounts.append(line)

    return accounts


if __name__ == "__main__":
    accounts = collect_accounts()
    if not accounts:
        print("未配置任何账号。请在 GitHub Secrets 里添加 WEBHOST_1, WEBHOST_2 ...")
        exit(1)

    print(f"共发现 {len(accounts)} 个账号，开始逐个登录...\n")

    login_statuses = []
    has_failure = False

    for account in accounts:
        try:
            email, password = account.split(':', 1)
            status = login_webhost(email.strip(), password.strip())
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

    # 有任一账号失败时以非零状态退出，让 GitHub Actions 标红并发失败邮件
    if has_failure:
        exit(1)
