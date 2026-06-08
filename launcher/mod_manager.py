import json
import os
import zipfile
from pathlib import Path
from typing import Optional

import requests

from .config import Config
from .downloader import Downloader, DownloadProgress


class ModrinthAPI:
    BASE = 'https://api.modrinth.com/v2'
    HEADERS = {'User-Agent': 'MCLauncher/1.0', 'Content-Type': 'application/json'}

    @staticmethod
    def search(query: str, limit: int = 20, offset: int = 0, facets: list = None) -> Optional[dict]:
        params = {
            'query': query,
            'limit': min(limit, 100),
            'offset': offset,
        }
        if facets:
            params['facets'] = json.dumps(facets)
        try:
            resp = requests.get(f'{ModrinthAPI.BASE}/search', params=params, headers=ModrinthAPI.HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except:
            return None

    @staticmethod
    def get_project(slug_or_id: str) -> Optional[dict]:
        try:
            resp = requests.get(f'{ModrinthAPI.BASE}/project/{slug_or_id}', headers=ModrinthAPI.HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except:
            return None

    @staticmethod
    def get_versions(project_id: str, loaders: list = None, game_versions: list = None) -> Optional[list]:
        params = {}
        if loaders:
            params['loaders'] = json.dumps(loaders)
        if game_versions:
            params['game_versions'] = json.dumps(game_versions)
        try:
            resp = requests.get(
                f'{ModrinthAPI.BASE}/project/{project_id}/version',
                params=params, headers=ModrinthAPI.HEADERS, timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except:
            return None

    @staticmethod
    def get_dependencies(project_id: str) -> Optional[list]:
        try:
            resp = requests.get(
                f'{ModrinthAPI.BASE}/project/{project_id}/dependencies',
                headers=ModrinthAPI.HEADERS, timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except:
            return None

    @staticmethod
    def get_categories() -> Optional[list]:
        try:
            resp = requests.get(f'{ModrinthAPI.BASE}/tag/category', headers=ModrinthAPI.HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except:
            return None

    @staticmethod
    def get_loaders() -> Optional[list]:
        try:
            resp = requests.get(f'{ModrinthAPI.BASE}/tag/loader', headers=ModrinthAPI.HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except:
            return None


class CurseForgeAPI:
    BASE = 'https://api.curseforge.com/v1'
    API_KEY = ''  # User must provide their own API key

    def __init__(self, api_key: str = ''):
        self.api_key = api_key or os.environ.get('CURSEFORGE_API_KEY', '')
        self.headers = {
            'User-Agent': 'MCLauncher/1.0',
            'x-api-key': self.api_key,
            'Accept': 'application/json',
        }

    def search(self, query: str, game_version: str = '', mod_loader: int = 0,
               limit: int = 20, index: int = 0) -> Optional[dict]:
        if not self.api_key:
            return None
        params = {
            'gameId': 432,
            'searchFilter': query,
            'pageSize': min(limit, 50),
            'index': index,
        }
        if game_version:
            params['gameVersion'] = game_version
        if mod_loader:
            params['modLoaderType'] = mod_loader
        try:
            resp = requests.get(f'{self.BASE}/mods/search', params=params, headers=self.headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except:
            return None

    def get_mod(self, mod_id: int) -> Optional[dict]:
        try:
            resp = requests.get(f'{self.BASE}/mods/{mod_id}', headers=self.headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except:
            return None

    def get_files(self, mod_id: int, game_version: str = '', mod_loader: int = 0) -> Optional[list]:
        params = {'pageSize': 50}
        if game_version:
            params['gameVersion'] = game_version
        if mod_loader:
            params['modLoaderType'] = mod_loader
        try:
            resp = requests.get(
                f'{self.BASE}/mods/{mod_id}/files',
                params=params, headers=self.headers, timeout=30
            )
            resp.raise_for_status()
            return resp.json()
        except:
            return None


class ModManager:
    LOADER_TYPES = {0: 'vanilla', 1: 'forge', 2: 'fabric', 3: 'quilt', 4: 'neoforge'}

    def __init__(self):
        self.config = Config()
        self.mods_dir = self.config.mcdir / 'mods'
        self.mods_dir.mkdir(parents=True, exist_ok=True)
        self.downloader = Downloader(max_workers=4)
        self.curseforge = CurseForgeAPI()

    def get_installed_mods(self, instance_name: str = '') -> list:
        mods_dir = self.config.mcdir / 'instances' / instance_name / 'mods' if instance_name else self.mods_dir
        if not mods_dir.exists():
            return []

        mods = []
        for f in mods_dir.iterdir():
            if f.suffix in ('.jar', '.disabled'):
                mod_info = self._read_mod_metadata(f)
                mod_info['file'] = str(f)
                mod_info['enabled'] = f.suffix != '.disabled'
                mod_info['filename'] = f.name.replace('.disabled', '')
                mods.append(mod_info)
        return mods

    def _read_mod_metadata(self, path: Path) -> dict:
        info = {
            'name': path.stem,
            'description': '',
            'version': '',
            'mc_version': [],
            'loaders': [],
            'authors': [],
            'side': 'both',
        }
        try:
            with zipfile.ZipFile(path, 'r') as zf:
                if 'fabric.mod.json' in zf.namelist():
                    with zf.open('fabric.mod.json') as f:
                        data = json.load(f)
                        info['name'] = data.get('name', info['name'])
                        info['description'] = data.get('description', '')
                        info['version'] = data.get('version', '')
                        info['authors'] = data.get('authors', [])
                        if isinstance(info['authors'], list):
                            info['authors'] = [a.get('name', str(a)) if isinstance(a, dict) else str(a) for a in info['authors']]
                        if 'depends' in data:
                            info['mc_version'] = data['depends'].get('minecraft', '').split(',')
                            loaders = [k for k in data['depends'] if k in ('fabricloader', 'fabric-api', 'quilt')]
                            if loaders:
                                info['loaders'] = ['Fabric' if 'fabric' in loaders[0] else 'Quilt']
                        info['side'] = data.get('environment', data.get('side', 'both'))

                elif 'META-INF/mods.toml' in zf.namelist():
                    with zf.open('META-INF/mods.toml') as f:
                        content = f.read().decode('utf-8', errors='ignore')
                        import re
                        m = re.search(r'modId\s*=\s*"(.+?)"', content)
                        if m:
                            info['name'] = m.group(1)
                        m = re.search(r'displayName\s*=\s*"(.+?)"', content)
                        if m:
                            info['name'] = m.group(1)
                        m = re.search(r'version\s*=\s*"(.+?)"', content)
                        if m:
                            info['version'] = m.group(1)
                        if 'forge' in content.lower():
                            info['loaders'] = ['Forge']
                        info['side'] = 'both'

                elif 'META-INF/neoforge.mods.toml' in zf.namelist():
                    info['loaders'] = ['NeoForge']

                if 'pack.mcmeta' in zf.namelist():
                    with zf.open('pack.mcmeta') as f:
                        pdata = json.load(f)
                        pack = pdata.get('pack', {})
                        desc = pack.get('description', '')
                        if desc and not info['description']:
                            info['description'] = desc
        except:
            pass
        return info

    async def download_mod_from_modrinth(self, version_data: dict, instance_name: str = '',
                                          progress: DownloadProgress = None) -> bool:
        files = version_data.get('files', [])
        if not files:
            return False

        primary = files[0]
        mods_dir = self.config.mcdir / 'instances' / instance_name / 'mods' if instance_name else self.mods_dir
        mods_dir.mkdir(parents=True, exist_ok=True)
        dest = mods_dir / primary['filename']

        return await self.downloader.download_file(
            primary['url'], dest, progress,
            primary.get('size', 0), primary.get('hashes', {}).get('sha1', '')
        )

    def enable_mod(self, file_path: str):
        p = Path(file_path)
        if p.suffix == '.disabled':
            new_path = p.with_suffix('.jar')
            if new_path.exists():
                new_path.unlink()
            p.rename(new_path)

    def disable_mod(self, file_path: str):
        p = Path(file_path)
        if p.suffix == '.jar':
            new_path = p.with_suffix('.jar.disabled')
            p.rename(new_path)

    def delete_mod(self, file_path: str):
        Path(file_path).unlink(missing_ok=True)
