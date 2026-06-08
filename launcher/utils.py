import os
import platform
import re
import subprocess
from pathlib import Path


SYSTEM = platform.system().lower()
IS_WINDOWS = SYSTEM == 'windows'
IS_MAC = SYSTEM == 'darwin'
IS_LINUX = SYSTEM == 'linux'


def get_os_name():
    if IS_WINDOWS: return 'windows'
    if IS_MAC: return 'osx'
    return 'linux'


def get_arch():
    machine = platform.machine().lower()
    if machine in ('amd64', 'x86_64'): return 'x64'
    if machine in ('aarch64', 'arm64'): return 'arm64'
    if machine in ('i386', 'i686', 'x86'): return 'x86'
    return 'x64'


def find_java_installs() -> list:
    """Auto-detect Java installations on the system"""
    found = []
    java_home = os.environ.get('JAVA_HOME', '')
    if java_home:
        javapath = Path(java_home) / 'bin' / ('java.exe' if IS_WINDOWS else 'java')
        if javapath.exists():
            ver = get_java_version(str(javapath))
            if ver:
                found.append({'path': str(javapath), 'version': ver, 'source': 'JAVA_HOME'})

    path_env = os.environ.get('PATH', '')
    for p in path_env.split(os.pathsep):
        javapath = Path(p.strip()) / ('java.exe' if IS_WINDOWS else 'java')
        if javapath.exists() and javapath not in [f['path'] for f in found]:
            ver = get_java_version(str(javapath))
            if ver:
                found.append({'path': str(javapath), 'version': ver, 'source': 'PATH'})

    import glob as glob_module
    common_paths = [
        r'C:\Program Files\Java\*',
        r'C:\Program Files (x86)\Java\*',
        r'C:\Program Files\Eclipse Adoptium\*',
        r'C:\Program Files\Microsoft\jdk-*',
    ]
    for pattern in common_paths:
        for p_str in glob_module.glob(pattern):
            p = Path(p_str)
            bin_dir = p / 'bin' / ('java.exe' if IS_WINDOWS else 'java')
            if bin_dir.exists() and str(bin_dir) not in [f['path'] for f in found]:
                ver = get_java_version(str(bin_dir))
                if ver:
                    found.append({'path': str(bin_dir), 'version': ver, 'source': 'Common'})

    found.sort(key=lambda x: x['version'], reverse=True)
    return found


def get_java_version(java_path: str) -> str:
    try:
        result = subprocess.run(
            [java_path, '-version'],
            capture_output=True, text=True, timeout=10
        )
        output = result.stderr or result.stdout
        match = re.search(r'(?:openjdk|java)\s+version\s+"(.+?)"', output, re.IGNORECASE)
        if match:
            ver = match.group(1)
            match2 = re.search(r'(\d+)', ver)
            if match2:
                return match2.group(1)
        return ''
    except:
        return ''


def is_version_compatible(java_version_str: str, mc_version: str) -> bool:
    try:
        java_ver = int(java_version_str.split('.')[0]) if '.' in java_version_str else int(java_version_str)
        mc_parts = mc_version.split('.')
        mc_major = int(mc_parts[0]) if mc_parts else 0
        mc_minor = int(mc_parts[1]) if len(mc_parts) > 1 else 0

        if mc_major >= 1 and mc_minor >= 18:
            return java_ver >= 17
        elif mc_major >= 1 and mc_minor >= 17:
            return java_ver >= 16
        elif mc_major >= 1 and mc_minor >= 16:
            return java_ver >= 8
        else:
            return java_ver >= 8
    except:
        return True


def format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return '0 B'
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    size = float(size_bytes)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f'{size:.1f} {units[i]}'


def format_speed(bytes_per_sec: float) -> str:
    return format_size(int(bytes_per_sec)) + '/s'


def format_time(seconds: float) -> str:
    if seconds < 0: return '--'
    if seconds < 60: return f'{int(seconds)}s'
    if seconds < 3600: return f'{int(seconds // 60)}m {int(seconds % 60)}s'
    return f'{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m'


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def class_path_separator():
    return ';' if IS_WINDOWS else ':'
