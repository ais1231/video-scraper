#!/usr/bin/env python3
"""夸克 Cookie 一次性导出工具（DPAPI 解密）
使用方法：
  1. 关闭夸克浏览器
  2. python export_cookies.py
  3. 之后夸克开着也能下载 Twitter/Bilibili 了
"""
import os
import shutil
import sqlite3
import subprocess
import tempfile
from http.cookiejar import Cookie, MozillaCookieJar
from pathlib import Path

COOKIE_DB = r"C:\Users\csh\AppData\Local\Quark\User Data\Default\Network\Cookies"
OUTPUT = Path(__file__).parent / "cookies.txt"


def _check_quark_running() -> bool:
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq quark.exe", "/NH"],
            capture_output=True, text=True, timeout=3
        )
        return "quark" in r.stdout.lower()
    except Exception:
        return False


def _decrypt_value(encrypted: bytes) -> str:
    """使用 Windows DPAPI 解密 Cookie 值"""
    if not encrypted:
        return ""
    try:
        import win32crypt
        data, _ = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def main():
    if _check_quark_running():
        print("[Error] 夸克浏览器正在运行，请先完全关闭夸克")
        print("        右键任务栏夸克图标 -> 退出")
        return

    if not os.path.exists(COOKIE_DB):
        print(f"[Error] 未找到 Cookie 数据库: {COOKIE_DB}")
        return

    # 复制一份再读（避免锁冲突）
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        tmp_path = tmp.name
        shutil.copy2(COOKIE_DB, tmp_path)

    try:
        conn = sqlite3.connect(tmp_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT host_key, path, is_secure, expires_utc, name, encrypted_value, is_httponly, samesite
            FROM cookies
        """)

        jar = MozillaCookieJar()
        decrypted = 0
        failed = 0

        for row in cursor.fetchall():
            host_key, path, secure, expires, name, enc_val, http_only, samesite = row
            if expires == 0:
                continue

            value = _decrypt_value(enc_val)
            if not value:
                failed += 1
                continue

            jar.set_cookie(Cookie(
                version=0, name=name, value=value,
                port=None, port_specified=False,
                domain=host_key,
                domain_specified=bool(host_key.startswith(".")),
                domain_initial_dot=host_key.startswith("."),
                path=path, path_specified=True,
                secure=bool(secure),
                expires=int(expires) if expires else None,
                discard=False, comment=None, comment_url=None,
                rest={"HttpOnly": str(http_only).lower()},
                rfc2109=False,
            ))
            decrypted += 1

        conn.close()
        jar.save(OUTPUT, ignore_discard=True, ignore_expires=True)
        print(f"[OK] 已导出 {decrypted} 条 Cookie（{failed} 条解密失败）")
        print(f"     文件: {OUTPUT}")
        print(f"\n配置已自动更新为使用 cookies.txt，夸克开着也能下载了")

    except Exception as e:
        print(f"[Error] 导出失败: {e}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


if __name__ == "__main__":
    main()
