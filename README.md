# BUU_ZhengFang - 北京联合大学正方教务系统抢课助手

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

自动登录北京联合大学正方教务系统，爬取课程信息并模拟发包进行抢课。支持校内直连和校外通过 WebVPN 访问两种模式。

## 功能

- **自动登录**：RSA 加密密码 + OCR 识别验证码，全自动完成教务系统登录
- **双网络模式**：
  - 校内模式：直连 `jwxt.buu.edu.cn`
  - 校外模式：通过 `wvpn.buu.edu.cn` WebVPN 代理访问，自动从浏览器提取认证 cookie
- **三种选课类型**：
  - 培养方案选课（计划内课程）
  - 通识教育选修课（校选课）
  - 跨专业选课
- **自动抢课**：循环发包直到选课成功
- **依赖自动安装**：首次运行自动 `pip install -r requirements.txt`

## 环境要求

- Python 3.10+
- Windows / macOS / Linux
- Firefox 或 Chrome / Edge 浏览器（校外模式需要）

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/BUU_ZhengFang.git
cd BUU_ZhengFang

# 2. 运行（首次运行会自动安装依赖）
python main.py
```

首次运行会提示设置账号密码（保存在 `account.json` 中）。之后直接选择网络模式即可。

## 使用说明

### 校内模式

```
python main.py
→ 选择 [1] 校内
→ 登录 → 选课菜单 → 选择课程 → 自动抢课
```

### 校外模式

```
python main.py
→ 选择 [2] 校外
→ 程序自动从浏览器提取 WebVPN cookie
  （如果浏览器未登录 WebVPN，会打开登录页面）
→ 配置 WebVPN 代理 URL
→ 登录 → 选课菜单 → 选择课程 → 自动抢课
```

> **首次使用校外模式**：程序会尝试从 Firefox/Chrome/Edge 自动提取 cookie。如果浏览器未登录过 `wvpn.buu.edu.cn`，程序会打开登录页面，扫码或输入账号密码登录后按 Enter，程序自动提取 cookie 并保存到 `wvpn_cookies.json`，下次无需重复登录。

### 设置账号密码

程序运行后在主菜单选择 `[1] 设置账号密码`，输入学号和教务系统密码。凭据保存在 `account.json` 中。

## 项目结构

```
BUU_ZhengFang/
├── main.py                       # 入口：网络模式选择 + 主菜单
├── LOGIN.py                      # 教务系统登录（RSA 加密 + OCR 验证码）
├── wvpn_login.py                 # WebVPN 认证（浏览器 cookie 自动提取）
├── wengine_url.py                # Wengine WebVPN URL 加密/解密工具
├── CATCH_PLANNED_COURSE.py       # 培养方案选课
├── CATCH_PUBLIC_COURSE.py        # 通识教育选修（校选）课
├── CATCH_OUTPLANNED_COURSE.py    # 跨专业选课
├── OCR_CODE.py                   # 验证码 OCR 识别
├── RW_ACCOUNT.py                 # 账号密码读写
├── MENU.py                       # 命令行菜单工具
├── _ensure_deps.py               # 依赖自动安装
├── requirements.txt              # Python 依赖列表
├── zfgetcode/                    # OCR 模型数据
├── LICENSE                       # Apache 2.0
└── README.md
```

## 依赖

主要依赖：

| 包 | 用途 |
|---|---|
| `requests` | HTTP 请求 |
| `beautifulsoup4` / `lxml` | HTML 解析 |
| `rsa` | RSA 密码加密 |
| `pycryptodome` | AES 加密（WebVPN URL / cookie） |
| `browser-cookie3` | 浏览器 cookie 自动提取 |
| `numpy` / `Pillow` / `numba` | 验证码 OCR |

完整列表见 [requirements.txt](requirements.txt)。

## 第三方代码致谢

- `wengine_url.py` 中的 BUU WebVPN URL 加密/解密实现基于 [ZYTEric/BUU-WebVPN-Conventor](https://github.com/ZYTEric/BUU-WebVPN-Conventor) (MIT)
- 密钥捕获思路参考 [wengine-vpn-decryptor](https://github.com/xiaobei97/wengine-vpn-decryptor)
- OCR 模型数据 (`zfgetcode/`) 由原项目作者提供

## 免责声明

本项目仅供学习和研究使用。使用者应自行承担使用本工具的一切风险和责任。请遵守学校相关规定，合理使用教务系统资源。

## 许可证

Copyright 2025 BUU_ZhengFang Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
