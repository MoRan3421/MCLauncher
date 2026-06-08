# ⛏ MCLauncher Pro

<div align="center">

![MCLauncher](assets/logo_256.png)

### 🚀 强大的 Minecraft 全能启动器

**多版本 · 多加载器 · 模组管理 · 整合包 · AI 助手**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=flat)]()
[![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-00bcd4?style=flat)](https://github.com/TomSchimansky/CustomTkinter)

---

![Screenshot](assets/splash_bg.png)

</div>

## ✨ 特性

### 📦 版本管理
- 支持所有 **Minecraft 正式版 / 快照版** 自动下载
- 一键集成主流 Mod Loader：
  - **Vanilla** — 原版纯净
  - **Fabric** — 轻量级模组平台
  - **Forge** — 经典模组平台
  - **Quilt** — Fabric 分支增强版
  - **NeoForge** — Forge 下一代
  - **OptiFine** — 性能优化
- 版本隔离管理，每个版本独立运行

### 🔧 模组管理
- **Modrinth API 集成** — 搜索、浏览、一键安装
- **CurseForge 支持** — 配置 API Key 后可用
- 本地模组管理 — 启用/禁用/删除
- 自动解析模组元数据（名称、版本、加载器、作者）
- 加载器与 Minecraft 版本筛选

### 📦 整合包
- **Modrinth 整合包** 一键安装
- 整合包导入/导出
- 本地整合包管理

### 🤖 AI 小助手
- 智能自然语言对话引擎
- 支持：问候、帮助、启动游戏、模组推荐、Minecraft 技巧、冷笑话
- 快速问答按钮
- 可爱的机器人界面

### 👤 账户系统
- **微软 OAuth 登录** — 完整正版验证流程
- **离线模式** — 自定义玩家名
- 多账户切换

### ⚙ 强大设置
- **Java 自动检测** — 扫描系统已安装的 Java
- 内存分配设置
- JVM 自定义参数
- 窗口分辨率 / 全屏
- 多主题支持 (Dark Blue / Green / Dark / Blue)
- 实例管理

---

## 🚀 快速开始

### 环境要求
- **Python 3.10+**
- **Git** (可选)

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/MoRan3421/MCLauncher.git
cd MCLauncher

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

或者直接双击 `start.bat` 🚀

### 📦 依赖

| 库 | 版本 | 用途 |
|---|---|---|
| customtkinter | ≥5.2.2 | 现代化 GUI 框架 |
| Pillow | ≥10.0.0 | 图像处理、Logo 渲染 |
| requests | ≥2.28.0 | HTTP 请求 (Mojang API, Modrinth) |
| aiohttp | ≥3.8.0 | 异步下载加速 |
| aiofiles | ≥23.0.0 | 异步文件操作 |
| packaging | ≥23.0 | 版本号比较 |

---

## 🗂 项目结构

```
MCLauncher/
├── main.py                     # 入口文件
├── requirements.txt            # 依赖列表
├── start.bat                   # Windows 一键启动
├── logo_generator.py           # Logo & 资源生成器
├── assets/                     # 静态资源 (Logo, 图片)
│   ├── logo.png / logo_64.png
│   ├── robot.png / robot_64.png
│   └── splash_bg.png
├── launcher/
│   ├── config.py               # 配置管理 (JSON 持久化)
│   ├── downloader.py           # 异步下载器 (断点续传, SHA1)
│   ├── utils.py                # 工具函数 (Java检测, 格式化)
│   ├── version_manager.py      # 版本管理核心
│   ├── mod_manager.py          # 模组管理 (Modrinth/CurseForge)
│   ├── account_manager.py      # 账户管理 (微软/离线)
│   ├── modpack_manager.py      # 整合包管理
│   ├── bot_manager.py          # AI 小助手引擎
│   └── gui/
│       ├── app.py              # 主窗口 (侧边栏导航, 启动逻辑)
│       ├── home_tab.py         # 首页面板
│       ├── versions_tab.py     # 版本管理页
│       ├── mods_tab.py         # 模组管理页
│       ├── modpacks_tab.py     # 整合包管理页
│       ├── bot_tab.py          # AI 助手聊天页
│       ├── accounts_tab.py     # 账户管理页
│       ├── settings_tab.py     # 设置页
│       └── widgets.py          # 可复用组件
└── data/                       # 运行时数据 (自动生成)
```

---

## 🎨 UI 预览

| 页面 | 说明 |
|------|------|
| 🏠 **首页** | 状态概览、快速启动、版本统计 |
| 📦 **版本管理** | 浏览/安装/筛选版本，支持加载器 |
| 🔧 **模组管理** | Modrinth 搜索 + 本地管理 |
| 📦 **整合包** | 浏览/安装 Modrinth 整合包 |
| 🤖 **AI 小助手** | 智能聊天机器人 |
| 👤 **账户** | 微软/离线账户管理 |
| ⚙ **设置** | Java、内存、主题等配置 |

---

## 🛠 技术栈

- **前端**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — 现代化 Tkinter 扩展
- **UI 设计**: 深色主题 + 玻璃拟态卡片 + 圆角设计
- **异步网络**: aiohttp 高速下载 Mojang 资源
- **API 集成**: Mojang Manifest / Modrinth / Microsoft OAuth
- **AI**: 自然语言规则引擎 (Bot)

---

## 📸 截图

> 启动器主界面包含侧边栏导航、状态面板、版本列表等，采用深色渐变主题。

---

## 📄 许可证

本项目基于 **MIT License** 开源。

---

<div align="center">
  <sub>Made with ❤️ by MoRan3421</sub>
  <br>
  <sub>Minecraft 版权归 Mojang Studios 所有</sub>
</div>
