import customtkinter as ctk
import webbrowser
import threading

from ..config import Config
from ..account_manager import AccountManager


class AccountsTab(ctk.CTkFrame):
    CARD = '#1a1f2e'
    BG = '#0d1117'
    ACCENT = '#00e676'

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color='transparent', **kwargs)
        self.config = Config()
        self.account_mgr = AccountManager()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._setup_header()
        self._setup_content()
        self._refresh_accounts()

    def _setup_header(self):
        header = ctk.CTkFrame(self, fg_color='transparent', height=60)
        header.grid(row=0, column=0, sticky='ew', padx=20, pady=(15, 5))
        ctk.CTkLabel(
            header, text='👤 账户管理', font=('Segoe UI', 22, 'bold'),
            text_color='#ffffff'
        ).pack(side='left')

    def _setup_content(self):
        btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        btn_frame.grid(row=1, column=0, pady=5, padx=20)

        self.ms_btn = ctk.CTkButton(
            btn_frame, text='🌐 添加微软账户', font=('Segoe UI', 13, 'bold'),
            height=38, corner_radius=10,
            fg_color='#1565c0', hover_color='#1976d2',
            command=self._add_microsoft
        )
        self.ms_btn.pack(side='left', padx=5)

        self.offline_btn = ctk.CTkButton(
            btn_frame, text='👤 添加离线账户', font=('Segoe UI', 13, 'bold'),
            height=38, corner_radius=10,
            fg_color='#0d47a1', hover_color='#1565c0',
            command=self._add_offline
        )
        self.offline_btn.pack(side='left', padx=5)

        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color='transparent'
        )
        self.scroll_frame.grid(row=2, column=0, sticky='nsew', padx=20, pady=10)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

    def _refresh_accounts(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        accounts = self.account_mgr.get_accounts()
        current = self.account_mgr.get_current_account()

        if not accounts:
            ctk.CTkLabel(
                self.scroll_frame, text='还没有添加任何账户',
                font=('Segoe UI', 14), text_color='#666666'
            ).pack(pady=60)
            return

        for acc in accounts:
            is_active = current and acc.get('uuid') == current.get('uuid')
            frame = ctk.CTkFrame(
                self.scroll_frame, fg_color=self.CARD,
                corner_radius=16, border_width=2,
                border_color=self.ACCENT if is_active else 'transparent'
            )
            frame.pack(fill='x', padx=5, pady=6)
            frame.grid_columnconfigure(1, weight=1)

            acc_type = acc.get('type', 'offline')
            type_icon = '🌐' if acc_type == 'microsoft' else '👤'
            type_name = '微软账户' if acc_type == 'microsoft' else '离线账户'

            ctk.CTkLabel(
                frame, text=f'{type_icon}  {acc.get("username", "Unknown")}',
                font=('Segoe UI', 18, 'bold'), text_color='#e0e0e0'
            ).grid(row=0, column=0, columnspan=2, sticky='w', padx=20, pady=(14, 4))

            ctk.CTkLabel(
                frame, text=f'类型: {type_name}',
                font=('Segoe UI', 11), text_color='#888888'
            ).grid(row=1, column=0, sticky='w', padx=20, pady=(0, 14))

            if is_active:
                ctk.CTkLabel(
                    frame, text='✅ 当前使用', font=('Segoe UI', 11, 'bold'),
                    text_color=self.ACCENT
                ).grid(row=1, column=1, sticky='e', padx=20)

            btn_frame = ctk.CTkFrame(frame, fg_color='transparent')
            btn_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 14), sticky='ew')

            btn_frame.grid_columnconfigure(0, weight=1)

            if not is_active:
                ctk.CTkButton(
                    btn_frame, text='切换到此账户', font=('Segoe UI', 12, 'bold'),
                    height=32, corner_radius=8,
                    fg_color=self.ACCENT, hover_color='#00c853',
                    text_color='#000000',
                    command=lambda a=acc: self._switch_account(a)
                ).grid(row=0, column=0, sticky='w')

            ctk.CTkButton(
                btn_frame, text='删除', font=('Segoe UI', 12),
                height=32, corner_radius=8,
                fg_color='#c62828', hover_color='#e53935',
                command=lambda u=acc.get('uuid', ''): self._delete_account(u)
            ).grid(row=0, column=1, sticky='e')

    def _switch_account(self, account):
        self.account_mgr.set_current_account(account)
        self._refresh_accounts()

    def _add_microsoft(self):
        url = self.account_mgr.microsoft_login_url()
        if url.startswith('https://login.microsoftonline.com/'):
            webbrowser.open(url)
            dialog = ctk.CTkInputDialog(
                text='在浏览器登录后，粘贴重定向URL中的code参数:',
                title='微软登录', font=('Segoe UI', 12)
            )
            code = dialog.get_input()
            if code:
                self._complete_ms_login(code)
        else:
            ctk.CTkLabel(
                self, text='⚠ 需要配置 Microsoft Client ID',
                font=('Segoe UI', 13), text_color='#ffc107'
            ).place(relx=0.5, rely=0.5, anchor='center')

    def _complete_ms_login(self, code):
        def _login():
            account = self.account_mgr.complete_microsoft_login(code)
            self.after(0, self._refresh_accounts)
        threading.Thread(target=_login, daemon=True).start()

    def _add_offline(self):
        dialog = ctk.CTkInputDialog(text='输入玩家名称:', title='离线账户')
        username = dialog.get_input()
        if username and username.strip():
            self.account_mgr.add_offline_account(username.strip())
            self._refresh_accounts()

    def _delete_account(self, uuid_str):
        self.account_mgr.remove_account(uuid_str)
        self._refresh_accounts()

    def refresh(self):
        self._refresh_accounts()


class AccountDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback=None):
        super().__init__(parent)
        self.callback = callback
        self.title('选择账户')
        self.geometry('400x350')
        self.configure(fg_color='#0d1117')

        self.config = Config()
        self.account_mgr = AccountManager()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text='选择要使用的账户',
            font=('Segoe UI', 16, 'bold'), text_color='#e0e0e0'
        ).grid(row=0, column=0, pady=(15, 5))

        scroll = ctk.CTkScrollableFrame(self, fg_color='#1a1f2e', corner_radius=12)
        scroll.grid(row=1, column=0, sticky='nsew', padx=15, pady=5)
        scroll.grid_columnconfigure(0, weight=1)

        accounts = self.account_mgr.get_accounts()
        if not accounts:
            ctk.CTkLabel(scroll, text='没有可用账户', text_color='#666666').pack(pady=30)
        else:
            for acc in accounts:
                text = f'{"🌐" if acc.get("type")=="microsoft" else "👤"} {acc["username"]}'
                btn = ctk.CTkButton(
                    scroll, text=text, font=('Segoe UI', 13),
                    fg_color='#0d1117', hover_color='#1a2a3e',
                    corner_radius=10, anchor='w',
                    command=lambda a=acc: self._select(a)
                )
                btn.pack(fill='x', pady=3)

        ctk.CTkButton(
            self, text='取消', font=('Segoe UI', 12),
            fg_color='#333333', hover_color='#444444',
            corner_radius=10,
            command=self.destroy
        ).grid(row=2, column=0, pady=12)

    def _select(self, account):
        if self.callback:
            self.callback(account)
        self.destroy()
