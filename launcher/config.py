import json
import os
from pathlib import Path


class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, data_dir=None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        if data_dir is None:
            data_dir = os.path.join(os.getenv('LOCALAPPDATA', '.'), 'MCLauncher')
        self.data_dir = Path(data_dir)
        self.config_path = self.data_dir / 'data' / 'config.json'
        self.accounts_path = self.data_dir / 'data' / 'accounts.json'
        self.instances_path = self.data_dir / 'data' / 'instances.json'
        self.mods_db_path = self.data_dir / 'data' / 'mods_cache.json'
        self.mcdir = self.data_dir / 'minecraft'
        self.versions_dir = self.mcdir / 'versions'
        self.mods_dir = self.mcdir / 'mods'
        self.resourcepacks_dir = self.mcdir / 'resourcepacks'
        self.shaderpacks_dir = self.mcdir / 'shaderpacks'

        self._ensure_dirs()

        self._defaults = {
            'java_path': '',
            'java_args': '-Xmx4G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=30 -XX:G1MaxNewSizePercent=40 -XX:G1HeapRegionSize=8M -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapWastePercent=5',
            'min_memory': 1024,
            'max_memory': 4096,
            'window_width': 854,
            'window_height': 480,
            'fullscreen': False,
            'theme': 'dark-blue',
            'language': 'zh_CN',
            'default_account': '',
            'default_instance': '',
            'download_threads': 8,
            'close_launcher_after_launch': False,
            'keep_launcher_open': True,
            'show_console': False,
        }
        self._config = self._load()

    def _ensure_dirs(self):
        for d in [self.data_dir, self.data_dir / 'data', self.mcdir, self.versions_dir,
                  self.mods_dir, self.resourcepacks_dir, self.shaderpacks_dir,
                  self.data_dir / 'cache' / 'icons', self.data_dir / 'runtimes']:
            d.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return {**self._defaults, **json.load(f)}
            except:
                pass
        return dict(self._defaults)

    def save(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        return self._config.get(key, default)

    def set(self, key, value):
        self._config[key] = value
        self.save()

    def update(self, d):
        self._config.update(d)
        self.save()

    def get_accounts(self):
        if self.accounts_path.exists():
            try:
                with open(self.accounts_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []

    def save_accounts(self, accounts):
        with open(self.accounts_path, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)

    def get_instances(self):
        if self.instances_path.exists():
            try:
                with open(self.instances_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_instances(self, instances):
        with open(self.instances_path, 'w', encoding='utf-8') as f:
            json.dump(instances, f, indent=2, ensure_ascii=False)

    def get_instance(self, name):
        instances = self.get_instances()
        return instances.get(name)

    def create_instance(self, name, version_id, loader_type='vanilla', loader_version=None):
        instances = self.get_instances()
        instances[name] = {
            'name': name,
            'version_id': version_id,
            'loader_type': loader_type,
            'loader_version': loader_version,
            'java_args': '',
            'max_memory': self.get('max_memory'),
            'min_memory': self.get('min_memory'),
            'resolution_width': self.get('window_width'),
            'resolution_height': self.get('window_height'),
            'mods': [],
            'resourcepacks': [],
            'shaderpacks': [],
            'created': __import__('time').time(),
            'last_played': 0,
            'icon': '',
        }
        self.save_instances(instances)
        return instances[name]

    def delete_instance(self, name):
        instances = self.get_instances()
        instances.pop(name, None)
        self.save_instances(instances)

    def update_instance(self, name, data):
        instances = self.get_instances()
        if name in instances:
            instances[name].update(data)
            self.save_instances(instances)
