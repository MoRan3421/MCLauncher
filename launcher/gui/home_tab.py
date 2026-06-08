import customtkinter as ctk
from pathlib import Path
from PIL import Image

from ..config import Config
from ..account_manager import AccountManager
from ..version_manager import VersionManager


class HomeTab(ctk.CTkFrame):
    def __init__(self, master, on_launch=None, **kwargs):
        super().__init__(master, fg_color='transparent', **kwargs)
        self.config = Config()
        self.account_mgr = AccountManager()
        self.vm = VersionManager()
        self.on_launch = on_launch

        self.GRADIENT = '#0d1117'
        self.CARD = '#1a1f2e'
        self.ACCENT = '#00bcd4'

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._setup_header()
        self._setup_content()

    def _setup_header(self):
        header = ctk.CTkFrame(self, fg_color='transparent', height=180)
        header.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        try:
            splash_path = Path('D:\\minecraft cllent\\assets\\splash_bg_thumb.png')
            if splash_path.exists():
                splash_img = ctk.CTkImage(Image.open(splash_path), size=(900, 180))
                splash_label = ctk.CTkLabel(header, image=splash_img, text='')
                splash_label.place(relx=0.5, rely=0.5, anchor='center')
        except:
            pass

        overlay = ctk.CTkFrame(header, fg_color='transparent')
        overlay.place(relx=0.5, rely=0.5, anchor='center')

        ctk.CTkLabel(
            overlay, text='⛏ 欢迎使用 MCLauncher Pro',
            font=('Segoe UI', 28, 'bold'), text_color='#ffffff'
        ).pack()

        ctk.CTkLabel(
            overlay, text='强大的 Minecraft 启动器 · 支持多版本 · 模组管理 · 整合包',
            font=('Segoe UI', 12), text_color='#00bcd4'
        ).pack()

    def _setup_content(self):
        content = ctk.CTkScrollableFrame(self, fg_color='transparent')
        content.grid(row=1, column=0, sticky='nsew', padx=20, pady=(0, 20))
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)

        # Quick Launch Card
        quick_card = self._make_card(content, '🚀 快速启动')
        quick_card.grid(row=0, column=0, sticky='nsew', padx=(0, 10), pady=5)
        quick_card.grid_columnconfigure(0, weight=1)

        self.account_btn = self._make_btn(
            quick_card, '👤  选择账户', self._switch_account,
            icon='#00bcd4'
        )
        self.account_btn.pack(fill='x', padx=15, pady=4)

        self.instance_btn = self._make_btn(
            quick_card, '📦  选择实例', self._switch_instance,
            icon='#7c4dff'
        )
        self.instance_btn.pack(fill='x', padx=15, pady=4)

        self.launch_btn = ctk.CTkButton(
            quick_card, text='▶   启动游戏',
            font=('Segoe UI', 16, 'bold'), height=52,
            corner_radius=12,
            fg_color='#00c853', hover_color='#00e676',
            text_color='#000000',
            command=self._launch
        )
        self.launch_btn.pack(fill='x', padx=15, pady=(12, 18))

        # Info Card
        info_card = self._make_card(content, '📊 启动信息')
        info_card.grid(row=0, column=1, sticky='nsew', padx=(10, 0), pady=5)
        info_card.grid_columnconfigure(0, weight=1)

        self.info_text = ctk.CTkTextbox(
            info_card, height=200, font=('Segoe UI', 11),
            fg_color='#0d1117', text_color='#c0c0c0',
            border_width=0, corner_radius=8
        )
        self.info_text.grid(row=1, column=0, padx=15, pady=(0, 15), sticky='ew')
        self.info_text.insert('1.0', '')
        self.info_text.configure(state='disabled')

        # Stats Card
        stats_card = self._make_card(content, '📈 状态概览')
        stats_card.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=5)
        stats_card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        stats = [
            ('已安装版本', '0', '#00bcd4'),
            ('模组数量', '0', '#7c4dff'),
            ('账户', '无', '#00e676'),
            ('实例', '0', '#ffc107'),
        ]
        self.stat_labels = []
        for i, (label, _, color) in enumerate(stats):
            stat_frame = ctk.CTkFrame(stats_card, fg_color='#0d1117', corner_radius=10)
            stat_frame.grid(row=0, column=i, sticky='nsew', padx=8, pady=12)
            stat_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                stat_frame, text=label,
                font=('Segoe UI', 11), text_color='#888888'
            ).pack(pady=(10, 2))
            val_label = ctk.CTkLabel(
                stat_frame, text='加载中...',
                font=('Segoe UI', 22, 'bold'), text_color=color
            )
            val_label.pack(pady=(0, 10))
            self.stat_labels.append(val_label)

        # Installed versions card
        versions_card = self._make_card(content, '📋 最近版本')
        versions_card.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=5)
        versions_card.grid_columnconfigure(0, weight=1)

        self.versions_frame = ctk.CTkScrollableFrame(
            versions_card, height=140, fg_color='#0d1117',
            corner_radius=8, border_width=0
        )
        self.versions_frame.grid(row=0, column=0, sticky='nsew', padx=15, pady=10)

        self._update_stats()
        self._refresh_versions_list()

    def _make_card(self, parent, title):
        card = ctk.CTkFrame(parent, fg_color=self.CARD, corner_radius=16, border_width=0)
        header = ctk.CTkLabel(
            card, text=title,
            font=('Segoe UI', 15, 'bold'), text_color='#e0e0e0'
        )
        header.grid(row=0, column=0, sticky='w', padx=18, pady=(14, 6))
        card.grid_columnconfigure(0, weight=1)
        return card

    def _make_btn(self, parent, text, command, icon='#00bcd4'):
        return ctk.CTkButton(
            parent, text=text,
            font=('Segoe UI', 13), height=40,
            corner_radius=10,
            fg_color='#0d1117', hover_color='#1a2a3e',
            anchor='w', command=command
        )

    def _update_stats(self):
        accounts = self.account_mgr.get_accounts()
        current = self.account_mgr.get_current_account()
        instances = self.config.get_instances()
        installed = self.vm.get_installed_versions()

        mod_count = 0
        from ..mod_manager import ModManager
        try:
            mod_count = len(ModManager().get_installed_mods())
        except:
            pass

        stats_values = [
            str(len(installed)),
            str(mod_count),
            current.get('username', '无') if current else '无',
            str(len(instances)),
        ]
        for label, val in zip(self.stat_labels, stats_values):
            label.configure(text=val)

    def _refresh_versions_list(self):
        for w in self.versions_frame.winfo_children():
            w.destroy()

        installed = self.vm.get_installed_versions()
        if not installed:
            ctk.CTkLabel(
                self.versions_frame,
                text='还没有安装任何版本，去"版本管理"页面安装吧！',
                font=('Segoe UI', 11), text_color='#666666'
            ).pack(pady=30)
            return

        for v in installed[:8]:
            row = ctk.CTkFrame(self.versions_frame, fg_color='transparent')
            row.pack(fill='x', padx=5, pady=2)

            dot_color = '#2e7d32' if v['type'] == 'release' else '#e65100'
            ctk.CTkLabel(row, text='●', font=('Segoe UI', 8), text_color=dot_color).pack(side='left', padx=(5, 8))
            ctk.CTkLabel(
                row, text=v['id'],
                font=('Segoe UI', 12, 'bold'), text_color='#c0c0c0'
            ).pack(side='left')
            ctk.CTkLabel(
                row, text=v['type'],
                font=('Segoe UI', 10), text_color='#666666'
            ).pack(side='right', padx=5)

    def _update_info_panel(self):
        account = self.account_mgr.get_current_account()
        instances = self.config.get_instances()

        lines = []
        lines.append(f'👤 当前账户:  {account.get("username", "无") if account else "无"}')
        lines.append(f'🔑 账户类型:  {"微软账户" if account and account.get("type")=="microsoft" else "离线账户" if account else "-"}')
        lines.append(f'📦 实例数量:  {len(instances)}')
        lines.append(f'☕ Java路径:  {self.config.get("java_path") or "自动检测"}')
        lines.append(f'💾 内存分配:  {self.config.get("min_memory")}MB - {self.config.get("max_memory")}MB')
        lines.append(f'🎮 窗口尺寸:  {self.config.get("window_width")}x{self.config.get("window_height")}')

        self.info_text.configure(state='normal')
        self.info_text.delete('1.0', 'end')
        self.info_text.insert('1.0', '\n'.join(lines))
        self.info_text.configure(state='disabled')

    def _switch_account(self):
        from .accounts_tab import AccountDialog
        AccountDialog(self.winfo_toplevel(), self._on_account_selected)

    def _on_account_selected(self, account):
        self._update_stats()
        self._update_info_panel()

    def _switch_instance(self):
        instances = self.config.get_instances()
        if not instances:
            return
        names = list(instances.keys())
        menu = ctk.CTkOptionMenu(self, values=names, command=self._on_instance_selected)
        menu.place(x=0, y=0)
        menu.focus()

    def _on_instance_selected(self, name):
        for w in self.winfo_children():
            if isinstance(w, ctk.CTkOptionMenu):
                w.destroy()
        self.instance_btn.configure(text=f'📦  {name}')

    def _launch(self):
        if self.on_launch:
            self.on_launch()

    def refresh(self):
        self._update_stats()
        self._update_info_panel()
        self._refresh_versions_list()
