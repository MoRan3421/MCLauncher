import asyncio
import threading
import customtkinter as ctk

from ..config import Config
from ..version_manager import VersionManager
from .widgets import SearchBar


class VersionsTab(ctk.CTkFrame):
    CARD = '#1a1f2e'
    BG = '#0d1117'
    ACCENT = '#00bcd4'

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color='transparent', **kwargs)
        self.config = Config()
        self.vm = VersionManager()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._setup_header()
        self._setup_content()
        self._load_versions()

    def _setup_header(self):
        header = ctk.CTkFrame(self, fg_color='transparent', height=70)
        header.grid(row=0, column=0, columnspan=3, sticky='ew', padx=20, pady=(15, 5))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text='📦 版本管理',
            font=('Segoe UI', 22, 'bold'), text_color='#ffffff'
        ).pack(side='left')

        self.status_label = ctk.CTkLabel(
            header, text='加载中...', font=('Segoe UI', 11), text_color='#00bcd4'
        )
        self.status_label.pack(side='right', padx=10)

    def _setup_content(self):
        left_frame = ctk.CTkFrame(self, fg_color=self.CARD, corner_radius=16)
        left_frame.grid(row=1, column=0, sticky='ns', padx=(20, 8), pady=5)
        left_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_frame, text='筛选', font=('Segoe UI', 14, 'bold'),
            text_color='#e0e0e0'
        ).grid(row=0, column=0, padx=15, pady=(12, 8), sticky='w')

        self.filter_var = ctk.StringVar(value='all')
        filters = [('全部版本', 'all'), ('正式版', 'release'), ('快照', 'snapshot'),
                   ('已安装', 'installed')]
        for i, (text, val) in enumerate(filters):
            btn = ctk.CTkButton(
                left_frame, text=text, font=('Segoe UI', 12),
                height=34, corner_radius=8,
                fg_color='#0d1117', hover_color='#1a2a3e',
                anchor='w',
                command=lambda v=val: self._filter_by(v)
            )
            btn.grid(row=i+1, column=0, padx=10, pady=3, sticky='ew')
            if val == 'all':
                btn.configure(fg_color='#1a2a3e', text_color=self.ACCENT)

        self.filter_buttons = {}

        main_frame = ctk.CTkFrame(self, fg_color=self.CARD, corner_radius=16)
        main_frame.grid(row=1, column=1, columnspan=2, sticky='nsew', padx=(8, 20), pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(main_frame, fg_color='transparent')
        top_bar.grid(row=0, column=0, sticky='ew', padx=15, pady=(12, 5))

        self.search_bar = SearchBar(top_bar, '搜索版本...', on_search=self._on_search)
        self.search_bar.pack(side='left', fill='x', expand=True, padx=(0, 10))

        self.install_btn = ctk.CTkButton(
            top_bar, text='⬇ 安装', font=('Segoe UI', 13, 'bold'),
            height=36, corner_radius=10,
            fg_color=self.ACCENT, hover_color='#0097a7',
            command=self._install_selected
        )
        self.install_btn.pack(side='right')

        self.scroll_frame = ctk.CTkScrollableFrame(
            main_frame, fg_color='#0d1117', corner_radius=12,
            border_width=0
        )
        self.scroll_frame.grid(row=1, column=0, sticky='nsew', padx=15, pady=10)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        self.selected_version = None
        self._versions_cache = []
        self._filtered_versions = []
        self._current_filter = 'all'

    def _filter_by(self, val):
        self._current_filter = val
        self._filter_versions()

    def _load_versions(self):
        def _load():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.vm.fetch_manifest(force=True))
                loop.run_until_complete(self.vm.fetch_fabric_versions(force=True))
                loop.run_until_complete(self.vm.fetch_forge_versions(force=True))
                loop.run_until_complete(self.vm.fetch_quilt_versions(force=True))
                loop.run_until_complete(self.vm.fetch_neoforge_versions(force=True))
                loop.close()
                self._versions_cache = self.vm.get_vanilla_versions()
                self.after(0, self._filter_versions)
                self.after(0, lambda: self.status_label.configure(text=f'共 {len(self._versions_cache)} 个版本'))
            except Exception as e:
                self.after(0, lambda: self.status_label.configure(text=f'加载失败', text_color='#ff5252'))

        threading.Thread(target=_load, daemon=True).start()

    def _filter_versions(self, query=''):
        q = query or self.search_bar.get_text()
        if self._current_filter == 'installed':
            installed = self.vm.get_installed_versions()
            self._filtered_versions = [{'id': v['id'], 'type': v['type']} for v in installed]
        else:
            versions = self._versions_cache
            if self._current_filter != 'all':
                versions = [v for v in versions if v.get('type') == self._current_filter]
            self._filtered_versions = list(versions)

        if q:
            self._filtered_versions = [v for v in self._filtered_versions if q.lower() in v.get('id', '').lower()]

        self._display_versions()

    def _on_search(self, query):
        self._filter_versions(query)

    def _display_versions(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        versions = self._filtered_versions[:200]
        if not versions:
            ctk.CTkLabel(
                self.scroll_frame, text='没有找到匹配的版本',
                font=('Segoe UI', 13), text_color='#666666'
            ).pack(pady=50)
            return

        for v in versions:
            vid = v.get('id', '')
            vtype = v.get('type', 'unknown')
            installed = self.vm.is_version_installed(vid)
            released = v.get('releaseTime', '')[:10] if v.get('releaseTime') else ''
            is_selected = vid == self.selected_version

            colors = {'release': '#2e7d32', 'snapshot': '#e65100',
                      'old_beta': '#6a1b9a', 'old_alpha': '#4a148c'}
            dot_color = colors.get(vtype, '#757575')

            frame = ctk.CTkFrame(self.scroll_frame, corner_radius=10, border_width=0)
            frame.pack(fill='x', padx=5, pady=2)
            if is_selected:
                frame.configure(fg_color='#1a2a3e', border_width=1, border_color=self.ACCENT)
            else:
                frame.configure(fg_color='#1a1f2e')
            frame.grid_columnconfigure(1, weight=1)

            frame.bind('<Button-1>', lambda e, v=vid: self._select_version(v))

            ctk.CTkLabel(frame, text='●', font=('Segoe UI', 10), text_color=dot_color).grid(
                row=0, column=0, padx=(12, 6), pady=10)

            ctk.CTkLabel(
                frame, text=vid,
                font=('Segoe UI', 13, 'bold'), text_color='#e0e0e0'
            ).grid(row=0, column=1, sticky='w')

            ctk.CTkLabel(
                frame, text=f'{vtype}',
                font=('Segoe UI', 10), text_color='#888888'
            ).grid(row=0, column=2, padx=5)

            if installed:
                ctk.CTkLabel(
                    frame, text='✓', font=('Segoe UI', 12, 'bold'),
                    text_color='#4caf50'
                ).grid(row=0, column=3, padx=(0, 12))

    def _select_version(self, version_id):
        self.selected_version = version_id
        self.install_btn.configure(text=f'⬇ 安装 {version_id}')
        self._display_versions()

    def _install_selected(self):
        if not self.selected_version:
            return
        version = self.selected_version
        instance_name = f'{version}-vanilla'

        self.install_btn.configure(state='disabled', text='安装中...')

        def _install():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.vm.download_version(version))
                loop.close()
                self.config.create_instance(instance_name, version)
                self.after(0, lambda: self._install_done(True, instance_name))
            except Exception as e:
                self.after(0, lambda: self._install_done(False, str(e)))

        threading.Thread(target=_install, daemon=True).start()

    def _install_done(self, success, msg):
        self.install_btn.configure(state='normal', text='⬇ 安装')
        if success:
            self.install_btn.configure(text=f'✅ 完成', fg_color='#2e7d32')
            self._display_versions()
            self.after(2000, lambda: self.install_btn.configure(text='⬇ 安装', fg_color=self.ACCENT))
        else:
            self.install_btn.configure(text='❌ 失败', fg_color='#c62828')

    def refresh(self):
        pass
