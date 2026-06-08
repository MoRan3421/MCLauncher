import json
import uuid
import webbrowser
from typing import Optional

import requests

from .config import Config


class AccountManager:
    MS_CLIENT_ID = 'YOUR_MICROSOFT_CLIENT_ID'
    MS_REDIRECT_URI = 'https://login.microsoftonline.com/common/oauth2/nativeclient'
    MS_AUTHORIZE = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize'
    MS_TOKEN = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
    XBL_AUTH = 'https://user.auth.xboxlive.com/user/authenticate'
    XSTS_AUTH = 'https://xsts.auth.xboxlive.com/xsts/authorize'
    MC_LOGIN = 'https://api.minecraftservices.com/authentication/login_with_xbox'
    MC_PROFILE = 'https://api.minecraftservices.com/minecraft/profile'
    MC_STORE = 'https://api.minecraftservices.com/entitlements/mcstore'

    def __init__(self):
        self.config = Config()
        self._current_account = None

    def get_accounts(self) -> list:
        return self.config.get_accounts()

    def get_current_account(self) -> Optional[dict]:
        if self._current_account:
            return self._current_account
        accounts = self.get_accounts()
        default = self.config.get('default_account', '')
        for acc in accounts:
            if acc.get('uuid') == default or (not default and acc.get('active')):
                self._current_account = acc
                return acc
        if accounts:
            self._current_account = accounts[0]
            return accounts[0]
        return None

    def set_current_account(self, account: dict):
        self._current_account = account
        self.config.set('default_account', account.get('uuid', ''))

    def add_offline_account(self, username: str) -> dict:
        accounts = self.get_accounts()
        acc_uuid = str(uuid.uuid3(uuid.NAMESPACE_DNS, f'offline:{username}'))

        for a in accounts:
            if a.get('uuid') == acc_uuid:
                a['active'] = True
                self.config.save_accounts(accounts)
                self.set_current_account(a)
                return a

        account = {
            'type': 'offline',
            'username': username,
            'uuid': acc_uuid,
            'access_token': '0',
            'active': True,
            'skin_url': '',
        }
        for a in accounts:
            a['active'] = False
        accounts.append(account)
        self.config.save_accounts(accounts)
        self.set_current_account(account)
        return account

    def microsoft_login_url(self) -> str:
        return (
            f'{self.MS_AUTHORIZE}?client_id={self.MS_CLIENT_ID}'
            f'&response_type=code&redirect_uri={self.MS_REDIRECT_URI}'
            f'&scope=XboxLive.signin%20offline_access%20openid'
        )

    def complete_microsoft_login(self, code: str) -> Optional[dict]:
        try:
            token_resp = requests.post(self.MS_TOKEN, data={
                'client_id': self.MS_CLIENT_ID,
                'code': code,
                'redirect_uri': self.MS_REDIRECT_URI,
                'grant_type': 'authorization_code',
            }, timeout=30)
            token_resp.raise_for_status()
            token_data = token_resp.json()
            ms_token = token_data.get('access_token', '')
            if not ms_token:
                return None

            xbl_resp = requests.post(self.XBL_AUTH, json={
                'Properties': {
                    'AuthMethod': 'RPS',
                    'SiteName': 'user.auth.xboxlive.com',
                    'RpsTicket': f'd={ms_token}',
                },
                'RelyingParty': 'http://auth.xboxlive.com',
                'TokenType': 'JWT',
            }, headers={'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=30)
            xbl_resp.raise_for_status()
            xbl_data = xbl_resp.json()
            xbl_token = xbl_data.get('Token', '')

            xsts_resp = requests.post(self.XSTS_AUTH, json={
                'Properties': {
                    'SandboxId': 'RETAIL',
                    'UserTokens': [xbl_token],
                },
                'RelyingParty': 'rp://api.minecraftservices.com/',
                'TokenType': 'JWT',
            }, headers={'Content-Type': 'application/json', 'Accept': 'application/json'}, timeout=30)
            xsts_resp.raise_for_status()
            xsts_data = xsts_resp.json()
            xsts_token = xsts_data.get('Token', '')
            uhs = xsts_data.get('DisplayClaims', {}).get('xui', [{}])[0].get('uhs', '')

            mc_resp = requests.post(self.MC_LOGIN, json={
                'identityToken': f'XBL3.0 x={uhs};{xsts_token}',
            }, headers={'Content-Type': 'application/json'}, timeout=30)
            mc_resp.raise_for_status()
            mc_data = mc_resp.json()
            mc_access_token = mc_data.get('access_token', '')

            profile_resp = requests.get(self.MC_PROFILE, headers={
                'Authorization': f'Bearer {mc_access_token}',
            }, timeout=30)
            profile_resp.raise_for_status()
            profile_data = profile_resp.json()

            account = {
                'type': 'microsoft',
                'username': profile_data.get('name', 'Player'),
                'uuid': profile_data.get('id', ''),
                'access_token': mc_access_token,
                'refresh_token': token_data.get('refresh_token', ''),
                'ms_token': ms_token,
                'active': True,
                'skin_url': '',
            }
            skins = profile_data.get('skins', [])
            if skins:
                account['skin_url'] = skins[0].get('url', '')

            accounts = self.get_accounts()
            for a in accounts:
                a['active'] = False
            accounts.append(account)
            self.config.save_accounts(accounts)
            self.set_current_account(account)
            return account

        except Exception as e:
            return None

    def remove_account(self, uuid_str: str):
        accounts = self.get_accounts()
        accounts = [a for a in accounts if a.get('uuid') != uuid_str]
        self.config.save_accounts(accounts)
        if self._current_account and self._current_account.get('uuid') == uuid_str:
            self._current_account = None
