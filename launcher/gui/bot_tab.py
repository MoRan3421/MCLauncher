import customtkinter as ctk
import threading
import time
from datetime import datetime
from pathlib import Path
from PIL import Image

from ..config import Config
from ..bot_manager import BotBrain


class BotTab(ctk.CTkFrame):
    ACCENT = '#00bcd4'
    CARD = '#1a1f2e'
    BG = '#0d1117'
    MSG_USER = '#1a3a4e'
    MSG_BOT = '#1a2f1e'

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color='transparent', **kwargs)
        self.config = Config()
        self.bot = BotBrain()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._setup_header()
        self._setup_chat()
        self._bot_greeting()

    def _setup_header(self):
        header = ctk.CTkFrame(self, fg_color='transparent', height=60)
        header.grid(row=0, column=0, sticky='ew', pady=(15, 5), padx=20)
        header.grid_columnconfigure(1, weight=1)

        try:
            robot_path = Path('D:\\minecraft cllent\\assets\\robot.png')
            if robot_path.exists():
                img = ctk.CTkImage(Image.open(robot_path), size=(40, 40))
                ctk.CTkLabel(header, image=img, text='').grid(row=0, column=0, padx=(0, 12))
        except:
            ctk.CTkLabel(header, text='🤖', font=('Segoe UI', 32)).grid(row=0, column=0, padx=(0, 12))

        title_frame = ctk.CTkFrame(header, fg_color='transparent')
        title_frame.grid(row=0, column=1, sticky='w')
        ctk.CTkLabel(
            title_frame, text='MCLauncher 小助手',
            font=('Segoe UI', 18, 'bold'), text_color='#ffffff'
        ).pack(anchor='w')
        ctk.CTkLabel(
            title_frame, text='在线 · 随时为你服务',
            font=('Segoe UI', 10), text_color='#00e676'
        ).pack(anchor='w')

        status = ctk.CTkFrame(header, fg_color='#1a2a1e', corner_radius=12)
        status.grid(row=0, column=2, padx=10)
        ctk.CTkLabel(
            status, text='  ●  运行中  ',
            font=('Segoe UI', 11), text_color='#00e676'
        ).pack(padx=8, pady=4)

    def _setup_chat(self):
        container = ctk.CTkFrame(self, fg_color=self.CARD, corner_radius=16)
        container.grid(row=1, column=0, sticky='nsew', padx=20, pady=5)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.chat_display = ctk.CTkScrollableFrame(
            container, fg_color=self.BG, corner_radius=12,
            border_width=0
        )
        self.chat_display.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
        self.chat_display.grid_columnconfigure(0, weight=1)

        input_frame = ctk.CTkFrame(container, fg_color='transparent', height=60)
        input_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(
            input_frame, placeholder_text='给小助手发消息...',
            font=('Segoe UI', 13), height=40,
            fg_color=self.BG, border_width=0,
        )
        self.input_entry.grid(row=0, column=0, sticky='ew', padx=(0, 8))
        self.input_entry.bind('<Return>', lambda e: self._send_message())

        self.send_btn = ctk.CTkButton(
            input_frame, text='发送', width=80, height=40,
            font=('Segoe UI', 13, 'bold'),
            fg_color=self.ACCENT, hover_color='#0097a7',
            corner_radius=10, command=self._send_message
        )
        self.send_btn.grid(row=0, column=1)

        quick_frame = ctk.CTkFrame(container, fg_color='transparent', height=40)
        quick_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=(0, 8))

        quick_btns = ['帮助', '启动游戏', '讲个笑话', '小技巧']
        for text in quick_btns:
            btn = ctk.CTkButton(
                quick_frame, text=text,
                font=('Segoe UI', 11), height=28,
                fg_color='#0d1117', hover_color='#1a2a3e',
                corner_radius=14, border_width=1,
                border_color='#2a2a3e',
                command=lambda t=text: self._quick_msg(t)
            )
            btn.pack(side='left', padx=3)

    def _bot_greeting(self):
        hour = datetime.now().hour
        if hour < 12:
            greeting = '早上好！'
        elif hour < 18:
            greeting = '下午好！'
        else:
            greeting = '晚上好！'

        msg = f'{greeting} 我是MCLauncher小助手🤖\n我可以帮你管理Minecraft、查找模组、获取技巧。试试问我"帮助"吧！'
        self._add_message(msg, 'bot')

    def _send_message(self):
        text = self.input_entry.get().strip()
        if not text:
            return
        self.input_entry.delete(0, 'end')
        self._add_message(text, 'user')
        self.input_entry.configure(state='disabled')
        self.send_btn.configure(state='disabled', text='思考中...')

        def _process():
            time.sleep(0.5)
            response = self.bot.process_message(text)
            self.after(0, lambda: self._add_message(response, 'bot'))
            self.after(0, lambda: self.input_entry.configure(state='normal'))
            self.after(0, lambda: self.send_btn.configure(state='normal', text='发送'))

        threading.Thread(target=_process, daemon=True).start()

    def _quick_msg(self, text):
        self.input_entry.delete(0, 'end')
        self.input_entry.insert(0, text)
        self._send_message()

    def _add_message(self, text, sender):
        frame = ctk.CTkFrame(self.chat_display, fg_color='transparent')
        frame.pack(fill='x', padx=5, pady=4)
        frame.grid_columnconfigure(0, weight=1)

        is_user = sender == 'user'
        align = 'e' if is_user else 'w'
        bg = self.MSG_USER if is_user else self.MSG_BOT
        name = '你' if is_user else '🤖 小助手'
        color = self.ACCENT if is_user else '#00e676'

        info_frame = ctk.CTkFrame(frame, fg_color='transparent')
        info_frame.pack(anchor=align)

        ctk.CTkLabel(info_frame, text=name, font=('Segoe UI', 10, 'bold'),
                      text_color=color).pack(anchor=align)

        bubble = ctk.CTkTextbox(
            frame, fg_color=bg, text_color='#e0e0e0',
            font=('Segoe UI', 12), wrap='word',
            corner_radius=12, border_width=0,
            width=450,
        )
        bubble.pack(anchor=align, pady=(2, 0))
        bubble.insert('1.0', text)
        bubble.configure(state='disabled')

        self.chat_display._parent_canvas.yview_moveto(1.0)
        self.chat_display.update_idletasks()

    def refresh(self):
        pass
