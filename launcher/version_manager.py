import asyncio
import json
import os
import re
import shutil
from pathlib import Path
from typing import Optional

from .config import Config
from .downloader import Downloader, DownloadProgress
from .utils import get_os_name, get_arch


class VersionManager:
    MANIFEST_URL = 'https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'
    FORGE_MANIFEST = 'https://bmclapi2.bangbang93.com/forge/minecraft'
    FABRIC_META = 'https://meta.fabricmc.net/v2'
    QUILT_META = 'https://meta.quiltmc.org/v3'
    NEOFORGE_MANIFEST = 'https://bmclapi2.bangbang93.com/neoforge'

    def __init__(self):
        self.config = Config()
        self.downloader = Downloader(max_workers=self.config.get('download_threads', 8))
        self.versions_dir = self.config.versions_dir
        self._manifest = None
        self._vanilla_versions = []
        self._forge_versions = {}
        self._fabric_versions = []
        self._quilt_versions = []
        self._neoforge_versions = {}

    async def close(self):
        await self.downloader.close()

    # ─── Vanilla Versions ────────────────────────────────────────

    async def fetch_manifest(self, force=False):
        if self._manifest and not force:
            return self._manifest
        self._manifest = Downloader.fetch_json(self.MANIFEST_URL)
        if self._manifest:
            self._vanilla_versions = self._manifest.get('versions', [])
        return self._manifest

    def get_vanilla_versions(self, version_type=None):
        versions = self._vanilla_versions
        if version_type:
            versions = [v for v in versions if v.get('type') == version_type]
        return versions

    def get_latest_release(self):
        if self._manifest:
            latest = self._manifest.get('latest', {})
            return latest.get('release', '')
        return ''

    def get_latest_snapshot(self):
        if self._manifest:
            latest = self._manifest.get('latest', {})
            return latest.get('snapshot', '')
        return ''

    def get_installed_versions(self):
        installed = []
        if self.versions_dir.exists():
            for vdir in self.versions_dir.iterdir():
                if vdir.is_dir():
                    json_file = vdir / f'{vdir.name}.json'
                    jar_file = vdir / f'{vdir.name}.jar'
                    if json_file.exists():
                        try:
                            with open(json_file) as f:
                                data = json.load(f)
                            installed.append({
                                'id': vdir.name,
                                'type': data.get('type', 'unknown'),
                                'release_time': data.get('releaseTime', ''),
                                'has_jar': jar_file.exists(),
                                'inherits_from': data.get('inheritsFrom', ''),
                            })
                        except:
                            installed.append({'id': vdir.name, 'type': 'unknown', 'has_jar': False})
        return installed

    def is_version_installed(self, version_id):
        return (self.versions_dir / version_id / f'{version_id}.json').exists()

    async def download_version(self, version_id: str, progress: DownloadProgress = None) -> bool:
        if self.is_version_installed(version_id):
            return True

        await self.fetch_manifest()
        version_info = None
        for v in self._vanilla_versions:
            if v['id'] == version_id:
                version_info = v
                break

        if not version_info:
            return False

        pkg_url = version_info['url']
        pkg_data = Downloader.fetch_json(pkg_url)
        if not pkg_data:
            return False

        vdir = self.versions_dir / version_id
        vdir.mkdir(parents=True, exist_ok=True)

        with open(vdir / f'{version_id}.json', 'w', encoding='utf-8') as f:
            json.dump(pkg_data, f, indent=2)

        client_info = pkg_data.get('downloads', {}).get('client', {})
        if client_info.get('url'):
            jar_path = vdir / f'{version_id}.jar'
            await self.downloader.download_file(
                client_info['url'], jar_path, progress,
                client_info.get('size', 0), client_info.get('sha1', '')
            )

        return True

    # ─── Fabric Loader ───────────────────────────────────────────

    async def fetch_fabric_versions(self, force=False):
        if self._fabric_versions and not force:
            return self._fabric_versions

        loader = Downloader.fetch_json(f'{self.FABRIC_META}/versions/loader')
        installer = Downloader.fetch_json(f'{self.FABRIC_META}/versions/installer')
        game = Downloader.fetch_json(f'{self.FABRIC_META}/versions/game')

        if loader and installer:
            self._fabric_versions = {
                'loader': loader,
                'installer': installer,
                'game': game or [],
            }
        return self._fabric_versions

    def get_fabric_compatible_versions(self):
        if isinstance(self._fabric_versions, list):
            return []
        return [v['version'] for v in self._fabric_versions.get('game', [])] if self._fabric_versions else []

    async def install_fabric(self, mc_version: str, loader_version: str = None,
                             progress: DownloadProgress = None) -> bool:
        await self.fetch_fabric_versions()
        await self.download_version(mc_version, progress)

        if not loader_version:
            loaders = self._fabric_versions.get('loader', [])
            if loaders:
                loader_version = loaders[0]['version']

        version_id = f'fabric-loader-{loader_version}-{mc_version}'
        profile_dir = self.versions_dir / version_id
        profile_dir.mkdir(parents=True, exist_ok=True)

        url = f'{self.FABRIC_META}/versions/loader/{mc_version}/{loader_version}/profile/json'
        profile = Downloader.fetch_json(url)
        if not profile:
            return False

        with open(profile_dir / f'{version_id}.json', 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2)

        return True

    # ─── Quilt Loader ────────────────────────────────────────────

    async def fetch_quilt_versions(self, force=False):
        if self._quilt_versions and not force:
            return self._quilt_versions

        loader = Downloader.fetch_json(f'{self.QUILT_META}/versions/loader')
        installer = Downloader.fetch_json(f'{self.QUILT_META}/versions/installer')
        game = Downloader.fetch_json(f'{self.QUILT_META}/versions/game')

        if loader:
            self._quilt_versions = {
                'loader': loader,
                'installer': installer or [],
                'game': game or [],
            }
        return self._quilt_versions

    async def install_quilt(self, mc_version: str, loader_version: str = None,
                            progress: DownloadProgress = None) -> bool:
        await self.fetch_quilt_versions()
        await self.download_version(mc_version, progress)

        if not loader_version:
            loaders = self._quilt_versions.get('loader', [])
            if loaders:
                loader_version = loaders[0]['version']

        version_id = f'quilt-loader-{loader_version}-{mc_version}'
        profile_dir = self.versions_dir / version_id
        profile_dir.mkdir(parents=True, exist_ok=True)

        url = f'{self.QUILT_META}/versions/loader/{mc_version}/{loader_version}/profile/json'
        profile = Downloader.fetch_json(url)
        if not profile:
            return False

        with open(profile_dir / f'{version_id}.json', 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2)

        return True

    # ─── Forge ───────────────────────────────────────────────────

    async def fetch_forge_versions(self, force=False):
        if self._forge_versions and not force:
            return self._forge_versions

        data = Downloader.fetch_json(self.FORGE_MANIFEST)
        if data:
            self._forge_versions = {}
            for entry in data:
                mc_ver = entry.get('mcversion', '')
                if mc_ver not in self._forge_versions:
                    self._forge_versions[mc_ver] = []
                self._forge_versions[mc_ver].append({
                    'version': entry.get('version', ''),
                    'build': entry.get('build', 0),
                    'branch': entry.get('branch', ''),
                    'mcversion': mc_ver,
                })
        return self._forge_versions

    def get_forge_versions_for(self, mc_version: str) -> list:
        return self._forge_versions.get(mc_version, [])

    async def install_forge(self, mc_version: str, forge_version: str,
                            progress: DownloadProgress = None) -> bool:
        await self.fetch_forge_versions()
        await self.download_version(mc_version, progress)

        version_id = f'{mc_version}-forge-{forge_version}'
        profile_dir = self.versions_dir / version_id
        profile_dir.mkdir(parents=True, exist_ok=True)

        url = f'https://bmclapi2.bangbang93.com/forge/minecraft/{mc_version}/{forge_version}/json'
        profile = Downloader.fetch_json(url)
        if not profile:
            return False

        with open(profile_dir / f'{version_id}.json', 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2)

        installer_url = f'https://bmclapi2.bangbang93.com/forge/minecraft/{mc_version}/{forge_version}/download'
        installer_path = profile_dir / f'forge-{forge_version}-installer.jar'
        await self.downloader.download_file(installer_url, installer_path, progress)

        return True

    # ─── NeoForge ────────────────────────────────────────────────

    async def fetch_neoforge_versions(self, force=False):
        if self._neoforge_versions and not force:
            return self._neoforge_versions

        data = Downloader.fetch_json(self.NEOFORGE_MANIFEST)
        if data:
            self._neoforge_versions = {}
            for entry in data:
                mc_ver = entry.get('mcversion', '')
                if mc_ver not in self._neoforge_versions:
                    self._neoforge_versions[mc_ver] = []
                self._neoforge_versions[mc_ver].append({
                    'version': entry.get('version', ''),
                    'build': entry.get('build', 0),
                    'mcversion': mc_ver,
                })
        return self._neoforge_versions

    async def install_neoforge(self, mc_version: str, neoforge_version: str,
                               progress: DownloadProgress = None) -> bool:
        await self.fetch_neoforge_versions()
        await self.download_version(mc_version, progress)

        version_id = f'{mc_version}-neoforge-{neoforge_version}'
        profile_dir = self.versions_dir / version_id
        profile_dir.mkdir(parents=True, exist_ok=True)

        url = f'https://bmclapi2.bangbang93.com/neoforge/{mc_version}/{neoforge_version}/json'
        profile = Downloader.fetch_json(url)
        if profile:
            with open(profile_dir / f'{version_id}.json', 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)

        return True

    # ─── OptiFine ────────────────────────────────────────────────

    async def download_optifine(self, mc_version: str, optifine_type: str = 'HD_U',
                                progress: DownloadProgress = None) -> Optional[str]:
        lib_dir = self.config.mcdir / 'libraries' / 'optifine'
        lib_dir.mkdir(parents=True, exist_ok=True)

        optifine_path = lib_dir / f'OptiFine_{mc_version}_{optifine_type}.jar'
        if optifine_path.exists():
            return str(optifine_path)

        mirror = f'https://bmclapi2.bangbang93.com/optifine/{mc_version}/{optifine_type}'
        data = Downloader.fetch_json(mirror)
        if data and isinstance(data, list) and len(data) > 0:
            patch = data[0]
            dl = patch.get('download', '')
            if dl:
                url = f'https://bmclapi2.bangbang93.com{dl}'
                await self.downloader.download_file(url, optifine_path, progress)
                return str(optifine_path) if optifine_path.exists() else None
        return None

    # ─── Version JSON Loading ────────────────────────────────────

    def load_version_json(self, version_id: str) -> Optional[dict]:
        path = self.versions_dir / version_id / f'{version_id}.json'
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                while 'inheritsFrom' in data:
                    parent_path = self.versions_dir / data['inheritsFrom'] / f'{data["inheritsFrom"]}.json'
                    if parent_path.exists():
                        with open(parent_path, 'r', encoding='utf-8') as pf:
                            parent_data = json.load(f)
                        data = {**parent_data, **data}
                        break
                    else:
                        break
                return data
            except:
                pass
        return None

    def get_assets_index(self, version_data: dict) -> Optional[dict]:
        assets = version_data.get('assetIndex', {})
        if assets.get('url'):
            return Downloader.fetch_json(assets['url'])
        return None

    def get_libraries(self, version_data: dict) -> list:
        libraries = []
        all_libs = version_data.get('libraries', [])
        for lib in all_libs:
            rules = lib.get('rules', [])
            if rules and not self._check_rules(rules):
                continue
            downloads = lib.get('downloads', {})
            artifact = downloads.get('artifact', {})
            if artifact.get('url'):
                libraries.append({
                    'path': str(self.config.mcdir / 'libraries' / artifact['path']),
                    'url': artifact['url'],
                    'size': artifact.get('size', 0),
                    'sha1': artifact.get('sha1', ''),
                })
            elif lib.get('natives'):
                natives = lib.get('natives', {})
                native_key = natives.get(get_os_name(), '')
                classifiers = downloads.get('classifiers', {})
                for key, cls_data in classifiers.items():
                    if native_key and native_key in key:
                        if cls_data.get('url'):
                            libraries.append({
                                'path': str(self.config.mcdir / 'libraries' / cls_data['path']),
                                'url': cls_data['url'],
                                'size': cls_data.get('size', 0),
                                'sha1': cls_data.get('sha1', ''),
                            })
        return libraries

    def get_assets(self, assets_data: dict) -> list:
        assets = []
        objects = assets_data.get('objects', {})
        for name, obj in objects.items():
            hash_val = obj.get('hash', '')
            if hash_val:
                prefix = hash_val[:2]
                assets.append({
                    'path': str(self.config.mcdir / 'assets' / 'objects' / prefix / hash_val),
                    'url': f'https://resources.download.minecraft.net/{prefix}/{hash_val}',
                    'size': obj.get('size', 0),
                    'sha1': hash_val,
                })
        return assets

    def get_main_class(self, version_data: dict) -> str:
        return version_data.get('mainClass', 'net.minecraft.client.main.Main')

    def get_minecraft_arguments(self, version_data: dict) -> str:
        args = version_data.get('minecraftArguments', '')
        if not args:
            log4j = version_data.get('arguments', {})
            game_args = log4j.get('game', [])
            args_list = []
            for arg in game_args:
                if isinstance(arg, str):
                    args_list.append(arg)
            args = ' '.join(args_list)
        return args

    def get_jvm_arguments(self, version_data: dict) -> list:
        args = version_data.get('arguments', {})
        jvm = args.get('jvm', [])
        result = []
        for arg in jvm:
            if isinstance(arg, str):
                result.append(arg)
        return result

    def _check_rules(self, rules: list) -> bool:
        result = True
        for rule in rules:
            action = rule.get('action', 'allow')
            os_info = rule.get('os', {})
            if os_info:
                name = os_info.get('name', '')
                if name and name != get_os_name():
                    continue
                arch_info = os_info.get('arch', '')
                if arch_info and arch_info != get_arch():
                    continue
                version_re = os_info.get('version', '')
                if version_re:
                    import platform
                    os_ver = platform.version()
                    if not re.match(version_re, os_ver):
                        continue
            if action == 'allow':
                result = True
            elif action == 'disallow':
                result = False
        return result

    def get_logging_config(self, version_data: dict) -> Optional[dict]:
        logging = version_data.get('logging', {})
        client = logging.get('client', {})
        file_info = client.get('file', {})
        if file_info.get('url'):
            return {
                'path': str(self.config.mcdir / 'assets' / 'log_configs' / file_info.get('id', 'log4j.xml')),
                'url': file_info['url'],
                'size': file_info.get('size', 0),
                'sha1': file_info.get('sha1', ''),
            }
        return None
