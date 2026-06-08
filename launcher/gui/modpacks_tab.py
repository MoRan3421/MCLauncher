import asyncio
import threading
import customtkinter as ctk

from ..config import Config
from ..modpack_manager import ModpackManager
from ..mod_manager import ModrinthAPI
from .widgets import SearchBar


class ModpacksTab(ctk.CTkFrame):
    CARD = '#1a1f2e'
    BG = '#0d1117'
    ACCENT = '#ffc107'

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color='transparent', **kwargs)
        self.config = Config()
        self.modpack_mgr = ModpackManager()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._setup_header()
        self._setup_content()
        self._load_installed()

    def _setup_header(self):
        header = ctk.CTkFrame(self, fg_color='transparent', height=60)
        header.grid(row=0, column=0, sticky='ew', padx=20, pady=(15, 5))
        ctk.CTkLabel(
            header, text='📦 整合包管理', font=('Segoe UI', 22, 'bold'),
            text_color='#ffffff'
        ).pack(side='left')

    def _setup_content(self):
        tab_view = ctk.CTkTabview(
            self, fg_color=self.CARD, corner_radius=16,
            segmented_button_fg_color=self.BG,
            segmented_button_selected_color=self.ACCENT,
            segmented_button_selected_hover_color='#ffb300',
            text_color='#e0e0e0',
        )
        tab_view.grid(row=1, column=0, sticky='nsew', padx=20, pady=5)

        browse_tab = tab_view.add('🌐 浏览整合包')
        installed_tab = tab_view.add('📦 已安装')

        self._setup_browse(browse_tab)
        self._setup_installed(installed_tab)

    def _setup_browse(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        self.search_bar = SearchBar(parent, '搜索整合包 (Modrinth)...', on_search=self._search)
        self.search_bar.grid(row=0, column=0, sticky='ew', pady=(10, 5))

        self.results_frame = ctk.CTkScrollableFrame(
            parent, fg_color=self.BG, corner_radius=12,
        )
        self.results_frame.grid(row=1, column=0, sticky='nsew', pady=5)
        self.results_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.results_frame, text='在上方搜索整合包', font=('Segoe UI', 13),
            text_color='#666666'
        ).pack(pady=60)

    def _setup_installed(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        self.installed_frame = ctk.CTkScrollableFrame(
            parent, fg_color=self.BG, corner_radius=12,
        )
        self.installed_frame.grid(row=0, column=0, sticky='nsew', pady=5)
        self.installed_frame.grid_columnconfigure(0, weight=1)

    def _load_installed(self):
        for w in self.installed_frame.winfo_children():
            w.destroy()
        modpacks = self.modpack_mgr.get_installed_modpacks()
        if not modpacks:
            ctk.CTkLabel(
                self.installed_frame, text='还没有安装整合包',
                font=('Segoe UI', 13), text_color='#666666'
            ).pack(pady=50)
        else:
            for pack in modpacks:
                frame = ctk.CTkFrame(self.installed_frame, fg_color=self.CARD, corner_radius=12)
                frame.pack(fill='x', padx=5, pady=4)
                frame.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(
                    frame, text=pack.get('name', 'Unknown'),
                    font=('Segoe UI', 14, 'bold'), text_color='#e0e0e0'
                ).grid(row=0, column=0, sticky='w', padx=14, pady=(10, 2))

                info = f'📌 {pack.get("mc_version", "?")}  🔧 {pack.get("loader", "?")}  📦 {pack.get("mods_count", 0)} mods'
                ctk.CTkLabel(
                    frame, text=info, font=('Segoe UI', 10),
                    text_color='#888888'
                ).grid(row=1, column=0, sticky='w', padx=14, pady=(0, 10))

                ctk.CTkButton(
                    frame, text='删除', width=60, height=30,
                    fg_color='#c62828', hover_color='#e53935',
                    corner_radius=8, font=('Segoe UI', 11),
                    command=lambda n=pack.get('name', ''): self._delete_pack(n)
                ).grid(row=0, column=1, rowspan=2, padx=(0, 14), sticky='e')

    def _search(self, query):
        if not query.strip():
            return
        for w in self.results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.results_frame, text='搜索中...', font=('Segoe UI', 13),
            text_color=self.ACCENT
        ).pack(pady=50)

        def _do_search():
            result = ModrinthAPI.search(query, limit=20, facets=[['project_type:modpack']])
            self.after(0, lambda: self._display_results(result))

        threading.Thread(target=_do_search, daemon=True).start()

    def _display_results(self, result):
        for w in self.results_frame.winfo_children():
            w.destroy()
        if not result or 'hits' not in result:
            ctk.CTkLabel(self.results_frame, text='未找到结果', font=('Segoe UI', 13), text_color='#666666').pack(pady=50)
            return

        for mod in result['hits']:
            frame = ctk.CTkFrame(self.results_frame, fg_color=self.CARD, corner_radius=12)
            frame.pack(fill='x', padx=5, pady=4)
            frame.grid_columnconfigure(1, weight=1)

            title = mod.get('title', 'Unknown')
            desc = mod.get('description', '')[:80]
            downloads = f"{mod.get('downloads', 0):,}"

            ctk.CTkLabel(
                frame, text=title, font=('Segoe UI', 14, 'bold'),
                text_color='#e0e0e0'
            ).grid(row=0, column=0, columnspan=2, sticky='w', padx=14, pady=(10, 2))
            ctk.CTkLabel(
                frame, text=desc, font=('Segoe UI', 10),
                text_color='#888888'
            ).grid(row=1, column=0, columnspan=2, sticky='w', padx=14)
            ctk.CTkLabel(
                frame, text=f'⬇ {downloads} 下载', font=('Segoe UI', 10),
                text_color='#666666'
            ).grid(row=2, column=0, sticky='w', padx=14, pady=(0, 10))

            pid = mod.get('project_id', '')
            ctk.CTkButton(
                frame, text='安装', width=70, height=30,
                font=('Segoe UI', 12, 'bold'),
                fg_color=self.ACCENT, hover_color='#ffb300',
                text_color='#000000', corner_radius=8,
                command=lambda p=pid: self._install_modpack(p)
            ).grid(row=0, column=2, rowspan=3, padx=(0, 14), sticky='e')

    def _install_modpack(self, project_id):
        def _install():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.modpack_mgr.install_from_modrinth(project_id))
                loop.close()
                self.after(0, self._load_installed)
            except:
                pass
        threading.Thread(target=_install, daemon=True).start()

    def _delete_pack(self, name):
        self.modpack_mgr.delete_modpack(name)
        self._load_installed()

    def refresh(self):
        self._load_installed()
