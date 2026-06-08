import customtkinter as ctk
from pathlib import Path


class DownloadProgressBar(ctk.CTkFrame):
    CARD = '#1a1f2e'
    BG = '#0d1117'
    ACCENT = '#00bcd4'

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color='transparent', **kwargs)
        self.grid_columnconfigure(1, weight=1)

        self.label = ctk.CTkLabel(
            self, text='准备下载...', anchor='w',
            font=('Segoe UI', 11), text_color='#b0b0b0'
        )
        self.label.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 4))

        self.progress = ctk.CTkProgressBar(
            self, height=16, corner_radius=8,
            fg_color=self.BG, progress_color=self.ACCENT
        )
        self.progress.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 4))
        self.progress.set(0)

        self.info_label = ctk.CTkLabel(
            self, text='', anchor='w', font=('Segoe UI', 10),
            text_color='#888888'
        )
        self.info_label.grid(row=2, column=0, sticky='ew')

        self.speed_label = ctk.CTkLabel(
            self, text='', anchor='e', font=('Segoe UI', 10),
            text_color='#00bcd4'
        )
        self.speed_label.grid(row=2, column=1, sticky='e')

    def set_progress(self, progress):
        if progress:
            self.progress.set(progress.progress)
            total_mb = progress.total_size / (1024*1024)
            done_mb = progress.downloaded_size / (1024*1024)
            self.info_label.configure(
                text=f'{progress.downloaded_files}/{progress.total_files} 文件 ({done_mb:.1f}/{total_mb:.1f} MB)'
            )
            if progress.current_speed > 0:
                speed = progress.current_speed / (1024*1024)
                self.speed_label.configure(text=f'{speed:.1f} MB/s')


class SearchBar(ctk.CTkFrame):
    BG = '#0d1117'
    ACCENT = '#00bcd4'

    def __init__(self, master, placeholder='搜索...', on_search=None, **kwargs):
        super().__init__(master, fg_color='transparent', **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self, placeholder_text=placeholder,
            font=('Segoe UI', 12), height=36,
            fg_color=self.BG, border_width=0
        )
        self.entry.grid(row=0, column=0, sticky='ew', padx=(0, 8))

        self.search_btn = ctk.CTkButton(
            self, text='🔍 搜索', width=80, height=36,
            font=('Segoe UI', 12, 'bold'),
            fg_color=self.ACCENT, hover_color='#0097a7',
            corner_radius=8, command=self._do_search
        )
        self.search_btn.grid(row=0, column=1)

        self.on_search = on_search
        self.entry.bind('<Return>', lambda e: self._do_search())

    def _do_search(self):
        if self.on_search:
            self.on_search(self.entry.get())

    def get_text(self):
        return self.entry.get()

    def set_text(self, text):
        self.entry.delete(0, 'end')
        self.entry.insert(0, text)
