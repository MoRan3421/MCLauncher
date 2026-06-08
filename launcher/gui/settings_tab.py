import customtkinter as ctk
from tkinter import filedialog

from ..config import Config
from ..utils import find_java_installs


class SettingsTab(ctk.CTkFrame):
    CARD = '#1a1f2e'
    BG = '#0d1117'
    ACCENT = '#00bcd4'

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color='transparent', **kwargs)
        self.config = Config()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._setup_header()
        self._setup_content()
        self._load_settings()

    def _setup_header(self):
        header = ctk.CTkFrame(self, fg_color='transparent', height=60)
        header.grid(row=0, column=0, sticky='ew', padx=20, pady=(15, 5))
        ctk.CTkLabel(
            header, text='⚙ 设置', font=('Segoe UI', 22, 'bold'),
            text_color='#ffffff'
        ).pack(side='left')

    def _setup_content(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color='transparent')
        scroll.grid(row=1, column=0, sticky='nsew', padx=20, pady=5)
        scroll.grid_columnconfigure(0, weight=1)

        self._setup_java_section(scroll)
        self._setup_display_section(scroll)
        self._setup_instance_section(scroll)

        save_btn = ctk.CTkButton(
            scroll, text='💾 保存设置', font=('Segoe UI', 15, 'bold'),
            height=48, corner_radius=12,
            fg_color=self.ACCENT, hover_color='#0097a7',
            command=self._save_settings
        )
        save_btn.pack(fill='x', padx=5, pady=(20, 30))

    def _make_card(self, parent, title):
        card = ctk.CTkFrame(parent, fg_color=self.CARD, corner_radius=16)
        card.pack(fill='x', padx=5, pady=8)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text=title, font=('Segoe UI', 15, 'bold'),
            text_color='#e0e0e0'
        ).grid(row=0, column=0, columnspan=4, padx=18, pady=(14, 10), sticky='w')

        return card

    def _make_row(self, card, row, label, widget):
        ctk.CTkLabel(
            card, text=label, font=('Segoe UI', 12),
            text_color='#b0b0b0'
        ).grid(row=row, column=0, padx=18, pady=6, sticky='w')
        widget.grid(row=row, column=1, columnspan=3, sticky='ew', padx=(0, 18), pady=6)

    def _setup_java_section(self, scroll):
        card = self._make_card(scroll, '☕ Java 设置')
        row = [1]

        self.java_path = ctk.CTkEntry(
            card, font=('Segoe UI', 12),
            fg_color=self.BG, border_width=0
        )
        self._make_row(card, row[0], 'Java 路径:', self.java_path)
        ctk.CTkButton(
            card, text='浏览', width=70, height=30,
            font=('Segoe UI', 11), corner_radius=8,
            fg_color='#333333', hover_color='#444444',
            command=self._browse_java
        ).grid(row=row[0], column=2, padx=(0, 6))
        ctk.CTkButton(
            card, text='自动检测', width=80, height=30,
            font=('Segoe UI', 11), corner_radius=8,
            fg_color=self.ACCENT, hover_color='#0097a7',
            command=self._detect_java
        ).grid(row=row[0], column=3, padx=(0, 18))
        row[0] += 1

        self.max_memory = ctk.CTkEntry(
            card, font=('Segoe UI', 12), width=120,
            fg_color=self.BG, border_width=0
        )
        self._make_row(card, row[0], '最大内存 (MB):', self.max_memory)
        row[0] += 1

        self.min_memory = ctk.CTkEntry(
            card, font=('Segoe UI', 12), width=120,
            fg_color=self.BG, border_width=0
        )
        self._make_row(card, row[0], '最小内存 (MB):', self.min_memory)
        row[0] += 1

        self.java_args = ctk.CTkEntry(
            card, font=('Segoe UI', 12),
            fg_color=self.BG, border_width=0
        )
        self._make_row(card, row[0], 'JVM 参数:', self.java_args)

    def _setup_display_section(self, scroll):
        card = self._make_card(scroll, '🖥 显示设置')
        row = [1]

        self.window_width = ctk.CTkEntry(
            card, font=('Segoe UI', 12), width=100,
            fg_color=self.BG, border_width=0
        )
        self._make_row(card, row[0], '窗口宽度:', self.window_width)
        row[0] += 1

        self.window_height = ctk.CTkEntry(
            card, font=('Segoe UI', 12), width=100,
            fg_color=self.BG, border_width=0
        )
        self._make_row(card, row[0], '窗口高度:', self.window_height)
        row[0] += 1

        self.fullscreen = ctk.CTkCheckBox(
            card, text='全屏模式', font=('Segoe UI', 12),
            fg_color=self.ACCENT, text_color='#b0b0b0'
        )
        self.fullscreen.grid(row=row[0], column=0, columnspan=2, padx=18, pady=6, sticky='w')
        row[0] += 1

        self.close_after_launch = ctk.CTkCheckBox(
            card, text='启动后关闭启动器', font=('Segoe UI', 12),
            fg_color=self.ACCENT, text_color='#b0b0b0'
        )
        self.close_after_launch.grid(row=row[0], column=0, columnspan=2, padx=18, pady=6, sticky='w')
        row[0] += 1

        ctk.CTkLabel(card, text='主题:', font=('Segoe UI', 12), text_color='#b0b0b0').grid(
            row=row[0], column=0, padx=18, pady=6, sticky='w')
        self.theme_var = ctk.StringVar(value='dark-blue')
        theme_menu = ctk.CTkOptionMenu(
            card, values=['dark-blue', 'green', 'dark', 'blue'],
            variable=self.theme_var, font=('Segoe UI', 12),
            fg_color=self.BG, button_color=self.ACCENT,
            dropdown_fg_color=self.BG,
            command=self._change_theme
        )
        theme_menu.grid(row=row[0], column=1, sticky='w')

    def _setup_instance_section(self, scroll):
        card = self._make_card(scroll, '📦 实例管理')
        row = [1]

        self.instances_list = ctk.CTkScrollableFrame(
            card, height=160, fg_color=self.BG, corner_radius=10
        )
        self.instances_list.grid(row=row[0], column=0, columnspan=4, sticky='ew', padx=18, pady=10)
        self.instances_list.grid_columnconfigure(0, weight=1)

    def _load_settings(self):
        self.java_path.insert(0, self.config.get('java_path', ''))
        self.max_memory.insert(0, str(self.config.get('max_memory', 4096)))
        self.min_memory.insert(0, str(self.config.get('min_memory', 1024)))
        self.java_args.insert(0, self.config.get('java_args', ''))
        self.window_width.insert(0, str(self.config.get('window_width', 854)))
        self.window_height.insert(0, str(self.config.get('window_height', 480)))
        if self.config.get('fullscreen'):
            self.fullscreen.select()
        if self.config.get('close_launcher_after_launch'):
            self.close_after_launch.select()
        self.theme_var.set(self.config.get('theme', 'dark-blue'))
        self._refresh_instance_list()

    def _browse_java(self):
        path = filedialog.askopenfilename(
            title='选择 Java 可执行文件',
            filetypes=[('Java', 'java.exe'), ('All Files', '*.*')]
        )
        if path:
            self.java_path.delete(0, 'end')
            self.java_path.insert(0, path)

    def _detect_java(self):
        found = find_java_installs()
        if found:
            best = found[0]
            self.java_path.delete(0, 'end')
            self.java_path.insert(0, best['path'])
            self.status_msg(f'检测到 Java {best["version"]}')

    def _change_theme(self, choice):
        ctk.set_default_color_theme(choice)

    def _save_settings(self):
        self.config.update({
            'java_path': self.java_path.get().strip(),
            'max_memory': int(self.max_memory.get() or 4096),
            'min_memory': int(self.min_memory.get() or 1024),
            'java_args': self.java_args.get().strip(),
            'window_width': int(self.window_width.get() or 854),
            'window_height': int(self.window_height.get() or 480),
            'fullscreen': bool(self.fullscreen.get()),
            'close_launcher_after_launch': bool(self.close_after_launch.get()),
            'theme': self.theme_var.get(),
        })
        self.status_msg('✅ 设置已保存')

    def status_msg(self, text):
        label = ctk.CTkLabel(
            self, text=text, font=('Segoe UI', 12),
            text_color=self.ACCENT, fg_color=self.CARD,
            corner_radius=10
        )
        label.place(relx=0.5, rely=0.95, anchor='center')
        self.after(2500, label.destroy)

    def _refresh_instance_list(self):
        for w in self.instances_list.winfo_children():
            w.destroy()

        instances = self.config.get_instances()
        if not instances:
            ctk.CTkLabel(
                self.instances_list, text='暂无实例',
                font=('Segoe UI', 11), text_color='#666666'
            ).pack(pady=20)
            return

        for name, info in instances.items():
            frame = ctk.CTkFrame(self.instances_list, fg_color=self.CARD, corner_radius=8)
            frame.pack(fill='x', pady=3)
            frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                frame, text=name, font=('Segoe UI', 12, 'bold'),
                text_color='#e0e0e0'
            ).grid(row=0, column=0, padx=12, pady=8, sticky='w')
            ctk.CTkLabel(
                frame, text=f'{info.get("version_id", "?")} ({info.get("loader_type", "vanilla")})',
                font=('Segoe UI', 10), text_color='#888888'
            ).grid(row=0, column=1, sticky='w')

            ctk.CTkButton(
                frame, text='✕', width=32, height=28,
                font=('Segoe UI', 11),
                fg_color='#c62828', hover_color='#e53935',
                corner_radius=6,
                command=lambda n=name: self._delete_instance(n)
            ).grid(row=0, column=2, padx=(0, 8))

    def _delete_instance(self, name):
        self.config.delete_instance(name)
        self._refresh_instance_list()

    def refresh(self):
        self._refresh_instance_list()
