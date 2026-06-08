import asyncio
import os
import subprocess
import threading
import time
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFilter

from ..config import Config
from ..account_manager import AccountManager
from ..version_manager import VersionManager
from ..utils import find_java_installs, is_version_compatible, class_path_separator, get_os_name, get_arch
from ..bot_manager import BotBrain

from .home_tab import HomeTab
from .versions_tab import VersionsTab
from .mods_tab import ModsTab
from .modpacks_tab import ModpacksTab
from .accounts_tab import AccountsTab
from .settings_tab import SettingsTab
from .bot_tab import BotTab


ctk.set_appearance_mode('dark')


class App(ctk.CTk):
    ACCENT = '#00bcd4'
    ACCENT_DARK = '#0097a7'
    GRADIENT_START = '#0d1117'
    GRADIENT_END = '#161b22'
    SIDEBAR_BG = '#0d1117'
    CARD_BG = '#1a1f2e'
    SUCCESS = '#00e676'
    WARNING = '#ffc107'
    ERROR = '#ff5252'

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.account_mgr = AccountManager()
        self.version_mgr = VersionManager()
        self.bot = BotBrain()
        self._loading = False
        self._launch_progress = 0

        self._setup_window()
        self._load_assets()
        self._setup_sidebar()
        self._setup_tabs()

        self.protocol('WM_DELETE_WINDOW', self._on_close)

    def _load_assets(self):
        asset_dir = Path('D:\\minecraft cllent\\assets')
        self.assets = {}
        try:
            logo_path = asset_dir / 'logo_64.png'
            if logo_path.exists():
                self.assets['logo'] = ctk.CTkImage(Image.open(logo_path), size=(48, 48))
            robot_path = asset_dir / 'robot_64.png'
            if robot_path.exists():
                self.assets['robot'] = ctk.CTkImage(Image.open(robot_path), size=(32, 32))
            splash_path = asset_dir / 'splash_bg_thumb.png'
            if splash_path.exists():
                self.assets['splash'] = ctk.CTkImage(Image.open(splash_path), size=(600, 200))
        except:
            pass

    def _setup_window(self):
        w = int(self.config.get('window_width', 1280))
        h = int(self.config.get('window_height', 800))
        self.title('MCLauncher Pro - Minecraft 全能启动器')
        self.geometry(f'{w}x{h}')
        self.minsize(1000, 650)
        ctk.set_default_color_theme(self.config.get('theme', 'dark-blue'))

        self.configure(fg_color=self.GRADIENT_START)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=240, corner_radius=0,
            fg_color=self.SIDEBAR_BG,
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.sidebar.grid_propagate(False)

        top_frame = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        top_frame.pack(fill='x', pady=(25, 20), padx=15)

        logo_frame = ctk.CTkFrame(top_frame, fg_color='transparent')
        logo_frame.pack(anchor='center')

        if 'logo' in self.assets:
            ctk.CTkLabel(logo_frame, image=self.assets['logo'], text='').pack(side='left', padx=(0, 10))
        else:
            ctk.CTkLabel(logo_frame, text='⛏', font=('Segoe UI', 36)).pack(side='left', padx=(0, 8))

        title_frame = ctk.CTkFrame(logo_frame, fg_color='transparent')
        title_frame.pack(side='left')
        ctk.CTkLabel(
            title_frame, text='MCLauncher',
            font=('Segoe UI', 20, 'bold'), text_color='#ffffff'
        ).pack(anchor='w')
        ctk.CTkLabel(
            title_frame, text='全能启动器 Pro v2.0',
            font=('Segoe UI', 10), text_color='#00bcd4'
        ).pack(anchor='w')

        sep = ctk.CTkFrame(top_frame, height=1, fg_color='#1a1f2e')
        sep.pack(fill='x', pady=(15, 5))

        nav_container = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        nav_container.pack(fill='both', expand=True, padx=10)

        nav_items = [
            ('🏠', '首页', 'home'),
            ('📦', '版本管理', 'versions'),
            ('🔧', '模组管理', 'mods'),
            ('📦', '整合包', 'modpacks'),
            ('🤖', '小助手', 'bot'),
            ('👤', '账户', 'accounts'),
            ('⚙', '设置', 'settings'),
        ]

        self.nav_buttons = {}
        for icon, label, key in nav_items:
            btn_frame = ctk.CTkFrame(nav_container, fg_color='transparent', height=42)
            btn_frame.pack(fill='x', pady=1)
            btn_frame.pack_propagate(False)

            btn = ctk.CTkButton(
                btn_frame, text=f'  {icon}   {label}',
                anchor='w', font=('Segoe UI', 13),
                height=40, corner_radius=10,
                fg_color='transparent',
                text_color='#b0b0b0',
                hover_color='#1a1f2e',
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(fill='both', expand=True)
            self.nav_buttons[key] = btn

        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color='transparent')
        bottom_frame.pack(side='bottom', fill='x', padx=12, pady=12)

        self.instance_selector = ctk.CTkOptionMenu(
            bottom_frame, values=['选择实例...'],
            font=('Segoe UI', 11), height=32,
            fg_color='#1a1f2e', button_color='#00bcd4',
            dropdown_fg_color='#1a1f2e',
        )
        self.instance_selector.pack(fill='x', pady=(0, 6))
        self._refresh_instance_selector()
        self.instance_selector.configure(command=self._on_instance_selected)
        self._selected_instance = None

        self.launch_btn = ctk.CTkButton(
            bottom_frame, text='▶   启动游戏',
            font=('Segoe UI', 14, 'bold'), height=46,
            corner_radius=12,
            fg_color='#00c853', hover_color='#00e676',
            text_color='#000000',
            command=self._launch_game
        )
        self.launch_btn.pack(fill='x')

        status_frame = ctk.CTkFrame(bottom_frame, fg_color='transparent', height=30)
        status_frame.pack(fill='x', pady=(6, 0))

        self.status_dot = ctk.CTkLabel(status_frame, text='●', font=('Segoe UI', 8), text_color='#00e676')
        self.status_dot.pack(side='left', padx=(0, 4))
        self.status_label = ctk.CTkLabel(
            status_frame, text='就绪', font=('Segoe UI', 10),
            text_color='#888888', anchor='w'
        )
        self.status_label.pack(side='left')

    def _refresh_instance_selector(self):
        instances = self.config.get_instances()
        names = list(instances.keys()) if instances else ['无实例']
        self.instance_selector.configure(values=names)
        if names and names[0] != '无实例':
            if self._selected_instance and self._selected_instance in names:
                self.instance_selector.set(self._selected_instance)
            else:
                self.instance_selector.set(names[0])
                self._selected_instance = names[0]
        else:
            self.instance_selector.set('无实例')
            self._selected_instance = None

    def _on_instance_selected(self, name):
        self._selected_instance = name

    def _setup_tabs(self):
        self.tab_container = ctk.CTkFrame(self, fg_color='transparent')
        self.tab_container.grid(row=0, column=1, sticky='nsew')
        self.tab_container.grid_columnconfigure(0, weight=1)
        self.tab_container.grid_rowconfigure(0, weight=1)

        self.tabs = {}
        tab_defs = {
            'home': lambda: HomeTab(self.tab_container, on_launch=self._launch_game),
            'versions': lambda: VersionsTab(self.tab_container),
            'mods': lambda: ModsTab(self.tab_container),
            'modpacks': lambda: ModpacksTab(self.tab_container),
            'bot': lambda: BotTab(self.tab_container),
            'accounts': lambda: AccountsTab(self.tab_container),
            'settings': lambda: SettingsTab(self.tab_container),
        }

        for key, factory in tab_defs.items():
            tab = factory()
            tab.grid(row=0, column=0, sticky='nsew')
            self.tabs[key] = tab
            tab.grid_remove()

        self.current_tab = 'home'
        self.tabs['home'].grid()

    def _switch_tab(self, key):
        if self.current_tab == key:
            return
        self.tabs[self.current_tab].grid_remove()
        self.tabs[key].grid()
        self.current_tab = key

        if hasattr(self.tabs[key], 'refresh'):
            try:
                self.tabs[key].refresh()
            except:
                pass

        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color='#1a1f2e', text_color='#00bcd4')
            else:
                btn.configure(fg_color='transparent', text_color='#b0b0b0')

    def set_status(self, text, status='info'):
        colors = {'info': '#888888', 'success': '#00e676', 'warning': '#ffc107', 'error': '#ff5252', 'loading': '#00bcd4'}
        color = colors.get(status, '#888888')
        self.status_label.configure(text=text, text_color=color)
        if status == 'loading':
            self.status_dot.configure(text_color='#00bcd4')
        elif status == 'success':
            self.status_dot.configure(text_color='#00e676')
        elif status == 'error':
            self.status_dot.configure(text_color='#ff5252')
        else:
            self.status_dot.configure(text_color=color)

    def _launch_game(self):
        if self._loading:
            return

        account = self.account_mgr.get_current_account()
        if not account:
            self.set_status('请先添加账户！', 'warning')
            return

        instance_name = self._selected_instance
        if not instance_name or instance_name == '无实例':
            self.set_status('请先创建实例！', 'warning')
            return

        instance = self.config.get_instance(instance_name)
        if not instance:
            self.set_status(f'实例 "{instance_name}" 不存在', 'error')
            return

        version_id = instance.get('version_id', '')
        if not version_id:
            self.set_status('实例未关联版本', 'error')
            return

        self._loading = True
        self.launch_btn.configure(state='disabled', text='⏳ 启动中...', fg_color='#0097a7')
        self.set_status(f'正在启动 {version_id}...', 'loading')

        threading.Thread(
            target=self._do_launch,
            args=(account, instance, version_id),
            daemon=True
        ).start()

    def _do_launch(self, account, instance, version_id):
        try:
            version_data = self.version_mgr.load_version_json(version_id)
            if not version_data:
                self.after(0, lambda: self.set_status(f'版本 {version_id} 数据加载失败', 'error'))
                self.after(0, self._reset_launch_btn)
                return

            java_path = self.config.get('java_path', '')
            if not java_path:
                found = find_java_installs()
                if found:
                    java_path = found[0]['path']
                else:
                    java_path = 'java'

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            max_mem = instance.get('max_memory', self.config.get('max_memory', 4096))
            min_mem = instance.get('min_memory', self.config.get('min_memory', 1024))
            java_args = instance.get('java_args', '') or self.config.get('java_args', '')

            main_class = self.version_mgr.get_main_class(version_data)
            mc_args = self.version_mgr.get_minecraft_arguments(version_data)

            self.after(0, lambda: self.set_status('正在下载依赖库...', 'loading'))
            libraries = self.version_mgr.get_libraries(version_data)
            libs_to_download = [l for l in libraries if not Path(l['path']).exists()]
            if libs_to_download:
                loop.run_until_complete(
                    self.version_mgr.downloader.download_files(libs_to_download)
                )

            self.after(0, lambda: self.set_status('正在检查资源文件...', 'loading'))
            assets_index = self.version_mgr.get_assets_index(version_data)
            if assets_index:
                assets = self.version_mgr.get_assets(assets_index)
                assets_to_dl = [a for a in assets if not Path(a['path']).exists()]
                if assets_to_dl:
                    loop.run_until_complete(
                        self.version_mgr.downloader.download_files(assets_to_dl[:200])
                    )

            loop.close()

            classpath = []
            for lib in libraries:
                p = Path(lib['path'])
                if p.exists():
                    classpath.append(str(p))

            jar_path = self.config.versions_dir / version_id / f'{version_id}.jar'
            if jar_path.exists():
                classpath.append(str(jar_path))

            cp_sep = class_path_separator()
            cp = cp_sep.join(classpath)

            game_dir = str(self.config.mcdir)
            assets_dir = str(self.config.mcdir / 'assets')
            assets_index_name = version_data.get('assetIndex', {}).get('id', version_id)
            user_type = account.get('type', 'mojang')
            uuid = account.get('uuid', '00000000-0000-0000-0000-000000000000')
            access_token = account.get('access_token', '0')
            username = account.get('username', 'Player')

            jvm_args = [
                f'-Xms{min_mem}M', f'-Xmx{max_mem}M',
                f'-Dminecraft.client.jar={jar_path}',
                f'-Djava.library.path={self.config.mcdir / "versions" / version_id / "natives"}',
                '-Dminecraft.launcher.brand=MCLauncher',
                '-Dminecraft.launcher.version=2.0',
            ]

            jvm_defaults = java_args.split() if java_args else []
            cmd = [java_path]
            cmd.extend(jvm_args)
            if jvm_defaults:
                cmd.extend(jvm_defaults)

            cmd.append('-cp')
            cmd.append(cp)
            cmd.append(main_class)

            template_vars = {
                '${auth_player_name}': username,
                '${auth_session}': access_token,
                '${auth_access_token}': access_token,
                '${auth_uuid}': uuid.replace('-', ''),
                '${version_name}': version_id,
                '${assets_root}': assets_dir,
                '${assets_index_name}': assets_index_name,
                '${game_directory}': game_dir,
                '${user_properties}': '{}',
                '${user_type}': user_type,
                '${version_type}': version_data.get('type', 'release'),
                '${resolution_width}': str(instance.get('resolution_width', self.config.get('window_width', 854))),
                '${resolution_height}': str(instance.get('resolution_height', self.config.get('window_height', 480))),
            }

            mc_arg_str = mc_args
            for var, val in template_vars.items():
                mc_arg_str = mc_arg_str.replace(var, val)
            cmd.extend(mc_arg_str.split())

            self.after(0, lambda: self.set_status(f'正在启动 Minecraft {version_id}...', 'success'))

            subprocess.Popen(cmd, cwd=game_dir)

            instance['last_played'] = time.time()
            self.config.update_instance(instance_name, instance)

            self.after(0, lambda: self.set_status(f'{version_id} 已启动！', 'success'))
            self.after(0, self._reset_launch_btn)

            if self.config.get('close_launcher_after_launch', False):
                self.after(2000, self._on_close)
            elif not self.config.get('keep_launcher_open', True):
                self.after(1000, lambda: self.withdraw())

        except Exception as e:
            self.after(0, lambda: self.set_status(f'启动失败: {str(e)[:50]}', 'error'))
            self.after(0, self._reset_launch_btn)

    def _reset_launch_btn(self):
        self._loading = False
        self.launch_btn.configure(
            state='normal', text='▶   启动游戏',
            fg_color='#00c853', hover_color='#00e676'
        )

    def _on_close(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.version_mgr.close())
            loop.close()
        except:
            pass
        self.destroy()
