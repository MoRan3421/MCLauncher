import asyncio
import threading
import customtkinter as ctk

from ..config import Config
from ..mod_manager import ModManager, ModrinthAPI
from .widgets import SearchBar


class ModsTab(ctk.CTkFrame):
    CARD = '#1a1f2e'
    BG = '#0d1117'
    ACCENT = '#7c4dff'

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color='transparent', **kwargs)
        self.config = Config()
        self.mod_mgr = ModManager()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._setup_header()
        self._setup_content()

    def _setup_header(self):
        header = ctk.CTkFrame(self, fg_color='transparent', height=60)
        header.grid(row=0, column=0, sticky='ew', padx=20, pady=(15, 5))
        ctk.CTkLabel(
            header, text='🔧 模组管理', font=('Segoe UI', 22, 'bold'),
            text_color='#ffffff'
        ).pack(side='left')

    def _setup_content(self):
        tab_view = ctk.CTkTabview(
            self, fg_color=self.CARD, corner_radius=16,
            segmented_button_fg_color=self.BG,
            segmented_button_selected_color=self.ACCENT,
            segmented_button_selected_hover_color=self.ACCENT,
            text_color='#e0e0e0',
        )
        tab_view.grid(row=1, column=0, sticky='nsew', padx=20, pady=5)

        self.browser_tab = tab_view.add('🌐 浏览模组')
        self.installed_tab = tab_view.add('📦 已安装')

        self._setup_browser(self.browser_tab)
        self._setup_installed(self.installed_tab)

    def _setup_browser(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        search_frame = ctk.CTkFrame(parent, fg_color='transparent')
        search_frame.grid(row=0, column=0, sticky='ew', pady=(10, 5))
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_bar = SearchBar(search_frame, '搜索模组 (Modrinth)...', on_search=self._search_mods)
        self.search_bar.grid(row=0, column=0, sticky='ew', padx=(0, 8))

        filter_frame = ctk.CTkFrame(search_frame, fg_color='transparent')
        filter_frame.grid(row=0, column=1)

        ctk.CTkLabel(filter_frame, text='加载器:', font=('Segoe UI', 11), text_color='#888888').pack(side='left', padx=(0, 4))
        self.loader_filter = ctk.CTkOptionMenu(
            filter_frame, values=['全部', 'fabric', 'forge', 'quilt', 'neoforge'],
            width=100, font=('Segoe UI', 11),
            fg_color=self.BG, button_color=self.ACCENT,
            dropdown_fg_color=self.BG,
        )
        self.loader_filter.pack(side='left', padx=(0, 8))

        ctk.CTkLabel(filter_frame, text='版本:', font=('Segoe UI', 11), text_color='#888888').pack(side='left', padx=(0, 4))
        self.version_filter = ctk.CTkEntry(
            filter_frame, placeholder_text='1.20.1', width=80,
            font=('Segoe UI', 11), fg_color=self.BG, border_width=0,
        )
        self.version_filter.pack(side='left')

        self.results_frame = ctk.CTkScrollableFrame(
            parent, fg_color=self.BG, corner_radius=12,
        )
        self.results_frame.grid(row=2, column=0, sticky='nsew', pady=5)
        self.results_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.results_frame, text='在上方搜索模组，从Modrinth获取',
            font=('Segoe UI', 13), text_color='#666666'
        ).pack(pady=60)

    def _setup_installed(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            parent, text='已安装的模组 (启用/禁用/删除)',
            font=('Segoe UI', 12), text_color='#888888'
        ).grid(row=0, column=0, pady=(10, 5), sticky='w')

        self.installed_frame = ctk.CTkScrollableFrame(
            parent, fg_color=self.BG, corner_radius=12,
        )
        self.installed_frame.grid(row=1, column=0, sticky='nsew', pady=(0, 10))
        self.installed_frame.grid_columnconfigure(0, weight=1)

        self._refresh_installed()

    def _search_mods(self, query):
        if not query.strip():
            return
        for w in self.results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.results_frame, text='搜索中...', font=('Segoe UI', 13), text_color=self.ACCENT).pack(pady=50)

        def _search():
            loader = self.loader_filter.get()
            mc_version = self.version_filter.get().strip()
            facets = []
            if loader != '全部':
                facets.append([f'categories:{loader}'])
            if mc_version:
                facets.append([f'versions:{mc_version}'])
            result = ModrinthAPI.search(query, limit=30, facets=facets if facets else None)
            self.after(0, lambda: self._display_results(result))

        threading.Thread(target=_search, daemon=True).start()

    def _display_results(self, result):
        for w in self.results_frame.winfo_children():
            w.destroy()
        if not result or 'hits' not in result:
            ctk.CTkLabel(self.results_frame, text='未找到结果', font=('Segoe UI', 13), text_color='#666666').pack(pady=50)
            return

        for mod in result['hits']:
            frame = ctk.CTkFrame(self.results_frame, fg_color=self.CARD, corner_radius=12, border_width=0)
            frame.pack(fill='x', padx=5, pady=4)
            frame.grid_columnconfigure(1, weight=1)

            title = mod.get('title', 'Unknown')
            desc = mod.get('description', '')[:80]
            author = mod.get('author', '')
            downloads = f"{mod.get('downloads', 0):,}"
            loaders = ', '.join(mod.get('loaders', []))

            ctk.CTkLabel(
                frame, text=title, font=('Segoe UI', 14, 'bold'),
                text_color='#e0e0e0'
            ).grid(row=0, column=0, columnspan=2, sticky='w', padx=14, pady=(10, 2))

            if desc:
                ctk.CTkLabel(
                    frame, text=desc, font=('Segoe UI', 10),
                    text_color='#888888'
                ).grid(row=1, column=0, columnspan=2, sticky='w', padx=14)

            ctk.CTkLabel(
                frame, text=f'👤 {author}  ⬇ {downloads}',
                font=('Segoe UI', 10), text_color='#666666'
            ).grid(row=2, column=0, sticky='w', padx=14, pady=(0, 10))
            if loaders:
                ctk.CTkLabel(
                    frame, text=f'🏷 {loaders}', font=('Segoe UI', 10),
                    text_color=self.ACCENT
                ).grid(row=2, column=1, sticky='w')

            pid = mod.get('project_id', '')
            ctk.CTkButton(
                frame, text='安装', width=70, height=30,
                font=('Segoe UI', 12, 'bold'),
                fg_color=self.ACCENT, hover_color='#651fff',
                corner_radius=8,
                command=lambda p=pid: self._install_mod(p)
            ).grid(row=0, column=2, rowspan=3, padx=(0, 14), sticky='e')

    def _install_mod(self, project_id):
        def _install():
            try:
                versions = ModrinthAPI.get_versions(project_id)
                if not versions:
                    return
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.mod_mgr.download_mod_from_modrinth(versions[0]))
                loop.close()
                self.after(0, self._refresh_installed)
            except:
                pass
        threading.Thread(target=_install, daemon=True).start()

    def _refresh_installed(self):
        for w in self.installed_frame.winfo_children():
            w.destroy()
        mods = self.mod_mgr.get_installed_mods()
        if not mods:
            ctk.CTkLabel(self.installed_frame, text='还没有安装模组', font=('Segoe UI', 13), text_color='#666666').pack(pady=50)
            return

        for mod in mods:
            frame = ctk.CTkFrame(self.installed_frame, fg_color=self.CARD, corner_radius=10)
            frame.pack(fill='x', padx=5, pady=3)
            frame.grid_columnconfigure(1, weight=1)

            enabled = mod.get('enabled', True)
            name = mod.get('name', mod.get('filename', 'Unknown'))
            version = mod.get('version', '')
            loaders = ', '.join(mod.get('loaders', []))

            ctk.CTkLabel(
                frame, text=name, font=('Segoe UI', 13, 'bold'),
                text_color='#e0e0e0' if enabled else '#666666'
            ).grid(row=0, column=0, columnspan=2, sticky='w', padx=12, pady=(8, 0))

            meta = []
            if version:
                meta.append(f'v{version}')
            if loaders:
                meta.append(loaders)
            if meta:
                ctk.CTkLabel(
                    frame, text=' | '.join(meta), font=('Segoe UI', 10),
                    text_color='#888888'
                ).grid(row=1, column=0, columnspan=2, sticky='w', padx=12, pady=(0, 8))

            btn_frame = ctk.CTkFrame(frame, fg_color='transparent')
            btn_frame.grid(row=0, column=2, rowspan=2, padx=(0, 8), sticky='e')

            toggle_text = '禁用' if enabled else '启用'
            toggle_color = '#666666' if enabled else self.ACCENT
            ctk.CTkButton(
                btn_frame, text=toggle_text, width=60, height=28,
                font=('Segoe UI', 11),
                fg_color='#0d1117', hover_color='#1a2a3e',
                command=lambda m=mod: self._toggle_mod(m)
            ).pack(side='left', padx=2)

            ctk.CTkButton(
                btn_frame, text='✕', width=36, height=28,
                font=('Segoe UI', 12),
                fg_color='#c62828', hover_color='#e53935',
                command=lambda m=mod: self._delete_mod(m)
            ).pack(side='left', padx=2)

    def _toggle_mod(self, mod_info):
        if mod_info.get('enabled', True):
            self.mod_mgr.disable_mod(mod_info['file'])
        else:
            self.mod_mgr.enable_mod(mod_info['file'])
        self._refresh_installed()

    def _delete_mod(self, mod_info):
        self.mod_mgr.delete_mod(mod_info['file'])
        self._refresh_installed()

    def refresh(self):
        self._refresh_installed()
