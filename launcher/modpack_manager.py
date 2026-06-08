import json
import os
import zipfile
from pathlib import Path
from typing import Optional

from .config import Config
from .downloader import Downloader, DownloadProgress
from .mod_manager import ModrinthAPI


class ModpackManager:
    def __init__(self):
        self.config = Config()
        self.downloader = Downloader(max_workers=4)
        self.modpacks_dir = self.config.mcdir / 'modpacks'

    def get_installed_modpacks(self) -> list:
        if not self.modpacks_dir.exists():
            return []
        packs = []
        for d in self.modpacks_dir.iterdir():
            manifest = d / 'manifest.json'
            if manifest.exists():
                try:
                    with open(manifest) as f:
                        data = json.load(f)
                    packs.append({
                        'name': data.get('name', d.name),
                        'version': data.get('version', ''),
                        'mc_version': data.get('mc_version', ''),
                        'loader': data.get('loader', ''),
                        'mods_count': data.get('mods_count', 0),
                        'path': str(d),
                        'icon': data.get('icon', ''),
                        'description': data.get('description', ''),
                    })
                except:
                    pass
        return packs

    async def install_from_modrinth(self, project_id: str, version_id: str = None,
                                    progress: DownloadProgress = None) -> Optional[str]:
        project = ModrinthAPI.get_project(project_id)
        if not project:
            return None

        versions = ModrinthAPI.get_versions(project_id)
        if not versions:
            return None

        target_version = None
        for v in versions:
            if version_id and v['id'] == version_id:
                target_version = v
                break
            if v.get('version_type') == 'release':
                target_version = v
                break
        if not target_version:
            target_version = versions[0]

        pack_name = project.get('slug', project_id)
        pack_dir = self.modpacks_dir / pack_name
        pack_dir.mkdir(parents=True, exist_ok=True)

        mods_dir = pack_dir / 'mods'
        mods_dir.mkdir(exist_ok=True)

        pack_data = {
            'name': project.get('title', pack_name),
            'version': target_version.get('version_number', ''),
            'mc_version': target_version.get('game_versions', [''])[0],
            'loader': target_version.get('loaders', [''])[0],
            'mods_count': len(target_version.get('files', [])),
            'icon': project.get('icon_url', ''),
            'description': project.get('description', ''),
        }

        installed = 0
        for file_info in target_version.get('files', []):
            dest = mods_dir / file_info['filename']
            ok = await self.downloader.download_file(
                file_info['url'], dest, progress,
                file_info.get('size', 0),
                file_info.get('hashes', {}).get('sha1', '')
            )
            if ok:
                installed += 1

        pack_data['mods_count'] = installed
        with open(pack_dir / 'manifest.json', 'w', encoding='utf-8') as f:
            json.dump(pack_data, f, indent=2, ensure_ascii=False)

        return pack_name

    async def install_from_curseforge(self, modpack_id: int, file_id: int = None,
                                      progress: DownloadProgress = None) -> Optional[str]:
        return None  # Requires CurseForge API key

    def export_modpack(self, instance_name: str, output_path: str) -> bool:
        instance_dir = self.config.mcdir / 'instances' / instance_name
        if not instance_dir.exists():
            return False

        manifest = self.config.get_instance(instance_name)
        if not manifest:
            return False

        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                manifest_data = {
                    'name': instance_name,
                    'version': '1.0.0',
                    'mc_version': manifest.get('version_id', ''),
                    'loader': manifest.get('loader_type', 'vanilla'),
                    'loader_version': manifest.get('loader_version', ''),
                    'mods': manifest.get('mods', []),
                }
                zf.writestr('manifest.json', json.dumps(manifest_data, indent=2))

                mods_dir = instance_dir / 'mods'
                if mods_dir.exists():
                    for mod_file in mods_dir.glob('*.jar'):
                        zf.write(mod_file, f'mods/{mod_file.name}')

                options_dir = instance_dir / 'config'
                if options_dir.exists():
                    for cfg_file in options_dir.rglob('*'):
                        if cfg_file.is_file():
                            zf.write(cfg_file, f'config/{cfg_file.relative_to(options_dir)}')

            return True
        except:
            return False

    def delete_modpack(self, name: str):
        pack_dir = self.modpacks_dir / name
        if pack_dir.exists():
            import shutil
            shutil.rmtree(pack_dir, ignore_errors=True)
