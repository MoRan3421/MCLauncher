import asyncio
import hashlib
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Optional

import aiohttp
import requests


class DownloadProgress:
    def __init__(self, total_files=0, total_size=0):
        self.total_files = total_files
        self.total_size = total_size
        self.downloaded_files = 0
        self.downloaded_size = 0
        self.current_file = ''
        self.current_speed = 0
        self.errors = []
        self._start_time = time.time()

    @property
    def progress(self):
        if self.total_size == 0:
            return 0.0
        return min(1.0, self.downloaded_size / self.total_size)

    @property
    def elapsed(self):
        return time.time() - self._start_time

    @property
    def eta(self):
        if self.progress == 0 or self.current_speed == 0:
            return -1
        remaining = self.total_size - self.downloaded_size
        return remaining / self.current_speed


class Downloader:
    META_AGENT = 'MCLauncher/1.0'
    CHUNK_SIZE = 8192

    def __init__(self, max_workers=8):
        self.max_workers = max_workers
        self._session = None
        self._progress_callbacks = []

    async def _get_session(self):
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=self.max_workers, limit_per_host=6)
            self._session = aiohttp.ClientSession(
                connector=connector,
                headers={'User-Agent': self.META_AGENT}
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def on_progress(self, callback: Callable):
        self._progress_callbacks.append(callback)

    def _emit_progress(self, progress: DownloadProgress):
        for cb in self._progress_callbacks:
            try:
                cb(progress)
            except:
                pass

    async def download_file(self, url: str, dest: Path, progress: DownloadProgress = None,
                            expected_size: int = 0, expected_sha1: str = '',
                            force: bool = False) -> bool:
        if not force and dest.exists():
            if expected_size and dest.stat().st_size == expected_size:
                if expected_sha1 and self._verify_sha1(dest, expected_sha1):
                    if progress:
                        progress.downloaded_files += 1
                        progress.downloaded_size += expected_size
                    return True
                if not expected_sha1:
                    if progress:
                        progress.downloaded_files += 1
                        progress.downloaded_size += dest.stat().st_size
                    return True

        temp = dest.with_suffix(dest.suffix + '.tmp')
        temp.parent.mkdir(parents=True, exist_ok=True)

        try:
            session = await self._get_session()
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get('content-length', 0))

                sha1_hash = hashlib.sha1()
                downloaded = 0
                last_update = time.time()
                last_bytes = 0

                with open(temp, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(self.CHUNK_SIZE):
                        if not chunk:
                            break
                        f.write(chunk)
                        sha1_hash.update(chunk)
                        downloaded += len(chunk)

                        now = time.time()
                        if now - last_update > 0.2:
                            if progress:
                                progress.current_speed = (downloaded - last_bytes) / (now - last_update)
                                progress.downloaded_size += (downloaded - last_bytes)
                                self._emit_progress(progress)
                            last_bytes = downloaded
                            last_update = now

                if progress:
                    progress.downloaded_size += (downloaded - last_bytes)
                    progress.downloaded_files += 1
                    self._emit_progress(progress)

                if expected_sha1 and sha1_hash.hexdigest() != expected_sha1:
                    temp.unlink(missing_ok=True)
                    return False

                temp.rename(dest)
                return True

        except Exception as e:
            temp.unlink(missing_ok=True)
            if progress:
                progress.errors.append(f'{url}: {e}')
            return False

    def _verify_sha1(self, path: Path, expected: str) -> bool:
        try:
            h = hashlib.sha1()
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest() == expected
        except:
            return False

    async def download_files(self, files: list, progress: DownloadProgress = None) -> int:
        if progress is None:
            progress = DownloadProgress(len(files), sum(f.get('size', 0) for f in files))
        tasks = []
        for f in files:
            tasks.append(self.download_file(
                f['url'], Path(f['path']),
                progress, f.get('size', 0), f.get('sha1', '')
            ))
        results = await asyncio.gather(*tasks)
        return sum(1 for r in results if r)

    @staticmethod
    def fetch_json(url: str, **kwargs) -> Optional[dict]:
        try:
            headers = {'User-Agent': Downloader.META_AGENT}
            resp = requests.get(url, headers=headers, timeout=30, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except:
            return None

    @staticmethod
    def fetch_text(url: str) -> Optional[str]:
        try:
            headers = {'User-Agent': Downloader.META_AGENT}
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.text
        except:
            return None
