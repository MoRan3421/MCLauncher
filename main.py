#!/usr/bin/env python3
"""
MCLauncher Pro v2.0 - Minecraft 全能启动器
支持多版本 · 多加载器 · 模组管理 · 整合包 · AI助手
"""

import sys
import os

sys.dont_write_bytecode = True

if __name__ == '__main__':
    try:
        import customtkinter as ctk
    except ImportError:
        print('正在安装依赖...')
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r',
                               os.path.join(os.path.dirname(__file__), 'requirements.txt')])
        import customtkinter as ctk

    from launcher.gui.app import App
    ctk.set_appearance_mode('dark')
    app = App()
    app.mainloop()
