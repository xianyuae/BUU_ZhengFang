"""
WebVPN 认证模块 (v5 - browser_cookie3)
=======================================
从系统浏览器自动提取 WebVPN 认证 cookie，零手动操作。

依赖: browser-cookie3 (pip install browser-cookie3)
"""

import time, os, json, requests, urllib3, sys, webbrowser

COOKIE_FILE = "wvpn_cookies.json"
WVPN_BASE = "https://wvpn.buu.edu.cn"
WVPN_LOGIN_PAGE = f"{WVPN_BASE}/login"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
_jwxt_mode = "campus"

# ---------------------------------------------------------------------------
#  Cookie 提取
# ---------------------------------------------------------------------------
def _extract_from_browser() -> dict | None:
    """用 browser_cookie3 从系统浏览器提取 cookie。依次尝试 Firefox / Chrome / Edge。"""
    try:
        import browser_cookie3
    except ImportError:
        return None

    for loader_name, loader in [
        ("Firefox", browser_cookie3.firefox),
        ("Chrome", browser_cookie3.chrome),
        ("Edge", browser_cookie3.edge),
        ("Chromium", browser_cookie3.chromium),
    ]:
        try:
            cj = loader()
            cookies = {}
            for c in cj:
                if "wvpn.buu.edu.cn" in c.domain:
                    cookies[c.name] = c.value
            if cookies:
                print(f"[wvpn_login] 从 {loader_name} 提取到 {len(cookies)} 个 cookie")
                return cookies
        except Exception:
            continue
    return None


def _load_from_file() -> dict | None:
    try:
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data:
            print(f"[wvpn_login] 从文件加载了 {len(data)} 个 cookie")
            return data
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        pass
    return None


def _save_to_file(cookies: dict):
    try:
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"[wvpn_login] cookie 已保存到 {COOKIE_FILE}")
    except IOError:
        pass


def _inject(session: requests.Session, cookies: dict):
    for name, value in cookies.items():
        session.cookies.set(name, value, domain="wvpn.buu.edu.cn")


# ---------------------------------------------------------------------------
#  验证
# ---------------------------------------------------------------------------
def _verify(session: requests.Session) -> bool:
    try:
        r = session.get(f"{WVPN_BASE}/wengine-vpn/config/security", timeout=10, allow_redirects=False)
        if r.status_code == 200 and r.text.strip().startswith("{"):
            return True
    except requests.RequestException:
        pass
    try:
        r = session.get(WVPN_LOGIN_PAGE, timeout=10, allow_redirects=False)
        if r.status_code in (301, 302, 303, 307, 308):
            if "/login" not in r.headers.get("Location", ""):
                return True
    except requests.RequestException:
        pass
    return False


# ---------------------------------------------------------------------------
#  公开 API
# ---------------------------------------------------------------------------
def authenticate() -> requests.Session | None:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()
    session.verify = False
    session.headers.update({"User-Agent": USER_AGENT})

    # 通道1: 文件
    cookies = _load_from_file()
    if cookies:
        _inject(session, cookies)
        if _verify(session):
            print("[wvpn_login] 文件 cookie 有效")
            return session
        print("[wvpn_login] 文件 cookie 已过期")

    # 通道2: 浏览器自动提取
    cookies = _extract_from_browser()
    if cookies:
        _inject(session, cookies)
        if _verify(session):
            _save_to_file(cookies)
            print("[wvpn_login] 浏览器 cookie 已认证")
            return session

    # 通道3: 打开浏览器登录
    print("[wvpn_login] 正在打开登录页面...")
    try:
        webbrowser.open(WVPN_LOGIN_PAGE)
    except Exception:
        print(f"  请手动打开: {WVPN_LOGIN_PAGE}")
    input("登录完成后按 Enter 继续...")

    cookies = _extract_from_browser()
    if cookies:
        _inject(session, cookies)
        if _verify(session):
            _save_to_file(cookies)
            print("[wvpn_login] 登录成功，cookie 已保存")
            return session

    print("[wvpn_login] 未能获取有效 cookie")
    return None


# ---------------------------------------------------------------------------
#  URL 辅助
# ---------------------------------------------------------------------------
def jwxt_url(raw_url: str) -> str:
    if _jwxt_mode == "off_campus":
        import wengine_url
        return wengine_url.convert_url(raw_url)
    return raw_url


def configure_jwxt_urls():
    global _jwxt_mode; _jwxt_mode = "off_campus"
    import wengine_url, LOGIN, CATCH_PUBLIC_COURSE as pub
    Z, cv = LOGIN.ZUCC, wengine_url.convert_url
    Z.DOMAIN = "wvpn.buu.edu.cn"
    Z.MainURL = cv("https://jwxt.buu.edu.cn/default2.aspx")
    Z.CheckCodeURL = cv("https://jwxt.buu.edu.cn/")
    Z.PlanCourageURL = cv("https://jwxt.buu.edu.cn/xsxk.aspx")
    Z.xsmain = cv("https://jwxt.buu.edu.cn/xs_main.aspx?xh=")
    Z.GetCodeKeyURL = cv("https://jwxt.buu.edu.cn/ajaxRequest/Handler1.ashx")
    Z.InitHeader["Host"] = "wvpn.buu.edu.cn"
    pub.info.InitHeader["Host"] = "wvpn.buu.edu.cn"
    pub.info.public_course_page_main = cv("https://jwxt.buu.edu.cn/xf_xsqxxxk.aspx")
    print("[wvpn_login] 教务系统 URL 已配置为 WebVPN 代理地址")
