"""
依赖自动安装模块
==================
在程序启动时检查 requirements.txt 中的依赖是否已安装，
如有缺失则自动调用 pip 安装。仅执行一次，安装成功后
创建标记文件跳过后续检查。
"""

import sys
import os
import subprocess


_MARKER_FILE = ".deps_installed"


def ensure_dependencies() -> bool:
    """确保所有依赖已安装。已安装则跳过，未安装则自动 pip install。
    Returns True 表示依赖就绪（原本就有 或 安装成功）。
    """
    # 已安装过，跳过
    req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "requirements.txt")
    marker_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               _MARKER_FILE)

    if os.path.isfile(marker_path):
        return True

    if not os.path.isfile(req_path):
        print("[deps] requirements.txt 不存在，跳过依赖检查")
        return True

    # 检查每个依赖
    missing = _find_missing(req_path)
    if not missing:
        _touch(marker_path)
        return True

    print(f"[deps] 检测到 {len(missing)} 个缺失依赖，正在自动安装...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", req_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        _touch(marker_path)
        print("[deps] 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[deps] 自动安装失败: {e}")
        print("[deps] 请手动运行: pip install -r requirements.txt")
        return False


def _find_missing(req_path: str) -> list[str]:
    """返回未安装的包名列表。"""
    missing = []
    try:
        with open(req_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # 提取包名（去掉版本号）
                pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                pkg = pkg.replace("-", "_")  # pip 用连字符，import 用下划线
                # 处理特殊映射
                pkg_import = _pkg_to_import(pkg)
                if not _is_installed(pkg_import):
                    missing.append(line)
    except IOError:
        pass
    return missing


def _pkg_to_import(pkg: str) -> str:
    """pip 包名 → Python import 名映射。"""
    mapping = {
        "beautifulsoup4": "bs4",
        "browser_cookie3": "browser_cookie3",
        "pillow": "PIL",
        "pycryptodome": "Crypto",
    }
    return mapping.get(pkg.lower(), pkg)


def _is_installed(import_name: str) -> bool:
    """检查 Python 包是否可导入。"""
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def _touch(filepath: str):
    """创建空标记文件。"""
    try:
        with open(filepath, "w") as f:
            f.write("")
    except IOError:
        pass
