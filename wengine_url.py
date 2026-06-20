#!/usr/bin/env python3
"""
Wengine WebVPN URL 转换器
==================================
北京网瑞达 Wengine SSL VPN 的 URL 加密/解密工具

算法: AES-256-CFB (segment_size=128)
密钥: 由各高校自行配置 (BUU默认: wrdvpnisthebest!)
用途: 将内网域名转换为 WebVPN 可访问的加密URL

用法:
  # 交互式
  python wengine_url.py

  # 直接转换
  python wengine_url.py https://my.buu.edu.cn
  python wengine_url.py http://xgxt.buu.edu.cn/mobile/comprehensive/myBaseScores

  # 解密
  python wengine_url.py --decrypt 77726476706e69737468656265737421fdee0f9e322526557a1dc7af96

依赖: pip install pycryptodome
"""

import sys
import re
import argparse
from urllib.parse import urlparse

try:
    from Crypto.Cipher import AES
except ImportError:
    print("缺少依赖，请运行: pip install pycryptodome")
    sys.exit(1)


# ============================================================
# 配置区 - 根据本校实际情况修改
# ============================================================
WVPN_HOST = "wvpn.buu.edu.cn"       # WebVPN 域名
DEFAULT_KEY = "wrdvpnisthebest!"     # 加密密钥 (16字节)
DEFAULT_IV = "wrdvpnisthebest!"      # 初始化向量 (16字节)
# ============================================================


def pad_zero(data: bytes, block_size: int = 16) -> bytes:
    """零填充至 block_size 的整数倍"""
    pad_len = block_size - len(data) % block_size
    if pad_len == block_size:
        return data
    return data + b'\x00' * pad_len


def unpad_zero(data: bytes) -> bytes:
    """移除零填充"""
    return data.rstrip(b'\x00')


def encrypt_host(host: str, key: str = DEFAULT_KEY, iv: str = DEFAULT_IV) -> str:
    """
    加密主机名，返回十六进制字符串 (IV + 密文)

    加密流程:
      1. 将 host 编码为 UTF-8 字节
      2. 零填充至16字节倍数
      3. AES-CFB 加密 (segment_size=128)
      4. 拼接 IV (16字节) + 密文
      5. 输出小写十六进制

    对应 Wengine JS 中的:
      v = function(text, e, t) {
        text = f(text, "utf8");
        var n = o.toBytes(e), c = o.toBytes(t),
            v = o.toBytes(text),
            m = new l(n, c, 16).encrypt(v);
        return d.fromBytes(c) + d.fromBytes(m).slice(0, 2 * r)
      }
    """
    key_bytes = key.encode('utf-8')
    iv_bytes = iv.encode('utf-8')
    plaintext = host.encode('utf-8')

    padded = pad_zero(plaintext, 16)
    cipher = AES.new(key_bytes, AES.MODE_CFB, iv=iv_bytes, segment_size=128)
    ciphertext = cipher.encrypt(padded)

    # IV(16字节) + 密文(与明文等长)
    result = iv_bytes.hex() + ciphertext[:len(plaintext)].hex()
    return result


def decrypt_hex(encrypted_hex: str, key: str = DEFAULT_KEY, iv: str = DEFAULT_IV) -> str:
    """
    解密 WebVPN 加密十六进制字符串

    输入格式: IV_hex(32字符) + Ciphertext_hex

    解密流程:
      1. 前32字符 = IV
      2. 剩余部分 = 密文
      3. AES-CFB 解密
      4. 移除零填充
      5. UTF-8 解码
    """
    key_bytes = key.encode('utf-8')
    iv_hex = encrypted_hex[:32]
    cipher_hex = encrypted_hex[32:]

    iv_bytes = bytes.fromhex(iv_hex)
    ciphertext = bytes.fromhex(cipher_hex)

    cipher = AES.new(key_bytes, AES.MODE_CFB, iv=iv_bytes, segment_size=128)
    decrypted = cipher.decrypt(ciphertext)
    return unpad_zero(decrypted).decode('utf-8', errors='replace')


def convert_url(original_url: str, key: str = DEFAULT_KEY, iv: str = DEFAULT_IV) -> str:
    """
    将内网URL转换为WebVPN加密URL

    支持的协议: http, https
    支持自定义端口: http://host:8080/path

    输出格式:
      https://{WVPN_HOST}/{协议}/{加密串}/{路径}
      例: https://wvpn.buu.edu.cn/https/77726476706e69737468656265737421fdee0f9e322526557a1dc7af96/
    """
    parsed = urlparse(original_url)

    scheme = parsed.scheme or "https"
    host = parsed.hostname or original_url.split('/')[0]
    port = parsed.port
    path = parsed.path or "/"
    query = parsed.query

    # 处理端口
    if port:
        if scheme == "https" and port == 443:
            proto = "https"
        elif scheme == "http" and port == 80:
            proto = "http"
        else:
            proto = f"{scheme}-{port}"
    else:
        proto = scheme

    # 主机名部分: host(不含协议和端口)
    host_only = host

    # 加密主机名
    encrypted = encrypt_host(host_only, key, iv)

    # 拼接路径和查询
    full_path = path
    if query:
        full_path += "?" + query

    # 构造最终URL (与 Wengine 生成的格式一致)
    wvpn_url = f"https://{WVPN_HOST}/{proto}/{encrypted}{full_path}"
    return wvpn_url


def batch_convert(domain_list: list) -> list:
    """批量转换域名列表"""
    results = []
    for item in domain_list:
        if not item.startswith(('http://', 'https://')):
            item = 'https://' + item
        wvpn_url = convert_url(item)
        results.append((item, wvpn_url))
    return results


# ============================================================
#  交互式模式
# ============================================================
def interactive_mode():
    print("=" * 60)
    print("  Wengine WebVPN URL 转换器")
    print("=" * 60)
    print(f"  WebVPN 主机: {WVPN_HOST}")
    print(f"  加密算法: AES-256-CFB")
    print(f"  技术支持: https://github.com/xiaobei97/wengine-vpn-decryptor")
    print("=" * 60)
    print("  支持的操作:")
    print("    1. 内网域名 → WebVPN URL (加密)")
    print("    2. WebVPN 加密串 → 内网域名 (解密)")
    print("    3. 批量转换 (空格分隔多个域名)")
    print("    q  退出")
    print("=" * 60)
    print()

    while True:
        try:
            inp = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not inp:
            continue
        if inp.lower() in ('q', 'quit', 'exit'):
            break

        # 判断输入类型
        # 如果是纯十六进制(32字符以上) → 解密
        if re.match(r'^[0-9a-fA-F]{32,}$', inp):
            try:
                result = decrypt_hex(inp)
                print(f"  解密结果: {result}")
            except Exception as e:
                print(f"  解密失败: {e}")

        # 如果是WebVPN URL → 提取加密串并解密
        elif WVPN_HOST in inp:
            # 提取加密串: /{proto}/{hex}/path
            match = re.search(r'/(?:https?|https?-\d+)/([0-9a-fA-F]{32,})(/[^ ]*)?', inp)
            if match:
                encrypted = match.group(1)
                sub_path = match.group(2) or ''
                try:
                    domain = decrypt_hex(encrypted)
                    result = f"https://{domain}{sub_path}"
                    print(f"  解密结果: {result}")
                except Exception as e:
                    print(f"  解密失败: {e}")
            else:
                print("  无法从URL中提取加密串")

        # 否则作为域名/URL → 加密
        else:
            # 支持空格分隔的多个域名
            items = inp.split()
            if len(items) > 1:
                print(f"  批量转换 {len(items)} 个域名:")
                results = batch_convert(items)
                for original, wvpn_url in results:
                    print(f"    {original}")
                    print(f"      → {wvpn_url}")
                    print()
            else:
                try:
                    wvpn_url = convert_url(inp)
                    print(f"  WebVPN URL:")
                    print(f"  {wvpn_url}")
                except Exception as e:
                    print(f"  转换失败: {e}")

        print()


# ============================================================
#  命令行模式
# ============================================================
def cli_mode():
    parser = argparse.ArgumentParser(
        description="Wengine WebVPN URL 转换器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s https://my.buu.edu.cn
  %(prog)s http://xgxt.buu.edu.cn/mobile/comprehensive/myBaseScores
  %(prog)s --decrypt 77726476706e69737468656265737421fdee0f9e322526557a1dc7af96
  %(prog)s --decrypt https://wvpn.buu.edu.cn/https/77726476706e69737468656265737421e8f0598869327d45300d8db9d6562d/mobile/comprehensive/myBaseScores
  %(prog)s --batch domains.txt
        """
    )
    parser.add_argument('url', nargs='?', help='内网URL或域名')
    parser.add_argument('-d', '--decrypt', metavar='HEX', help='解密十六进制加密串')
    parser.add_argument('-b', '--batch', metavar='FILE', help='批量转换(文件每行一个域名)')

    args = parser.parse_args()

    # 解密模式
    if args.decrypt:
        encrypted_input = args.decrypt
        sub_path = ''
        # 如果是完整 WebVPN URL，自动提取 hex 部分
        if WVPN_HOST in encrypted_input:
            match = re.search(r'/(?:https?|https?-\d+)/([0-9a-fA-F]{32,})(/[^ ]*)?', encrypted_input)
            if match:
                encrypted_input = match.group(1)
                sub_path = match.group(2) or ''
            else:
                print("无法从URL中提取加密串", file=sys.stderr)
                sys.exit(1)
        try:
            domain = decrypt_hex(encrypted_input)
            result = f"https://{domain}{sub_path}" if sub_path else domain
            print(result)
        except Exception as e:
            print(f"解密失败: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # 批量模式 (文件)
    if args.batch:
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                domains = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"文件不存在: {args.batch}", file=sys.stderr)
            sys.exit(1)

        results = batch_convert(domains)
        for original, wvpn_url in results:
            print(f"{wvpn_url}")
        return

    # 单个URL模式
    if args.url:
        # 检测是否为 WebVPN URL → 解密模式
        if WVPN_HOST in args.url:
            match = re.search(r'/(?:https?|https?-\d+)/([0-9a-fA-F]{32,})(/[^ ]*)?', args.url)
            if match:
                encrypted = match.group(1)
                sub_path = match.group(2) or ''
                try:
                    domain = decrypt_hex(encrypted)
                    print(f"https://{domain}{sub_path}")
                except Exception as e:
                    print(f"解密失败: {e}", file=sys.stderr)
                    sys.exit(1)
            else:
                print("无法从URL中提取加密串", file=sys.stderr)
                sys.exit(1)
            return

        if not args.url.startswith(('http://', 'https://')):
            args.url = 'https://' + args.url
        try:
            wvpn_url = convert_url(args.url)
            print(wvpn_url)
        except Exception as e:
            print(f"转换失败: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # 无参数 → 交互式
    interactive_mode()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cli_mode()
    else:
        interactive_mode()
