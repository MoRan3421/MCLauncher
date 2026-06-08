import json
import os
import random
import threading
import time
from pathlib import Path
from datetime import datetime

from .config import Config


class BotBrain:
    responses = {
        'greeting': [
            '你好！我是MCLauncher小助手，有什么可以帮你的吗？',
            '嗨~ 欢迎使用MCLauncher！我可以帮你管理Minecraft。',
            '你好呀！需要我帮你启动游戏还是管理模组呢？',
        ],
        'help': [
            '我可以帮你：\n• 启动Minecraft游戏\n• 管理模组和整合包\n• 切换账户\n• 安装新版本\n• 提供游戏技巧',
            '试试对我说"启动游戏"、"安装模组"、"切换账户"！',
        ],
        'launch': [
            '正在准备启动游戏...请确保已选择实例和账户！',
            '好的！已经准备好启动参数，点击启动按钮即可~',
        ],
        'mod': [
            '模组管理在"模组管理"页面哦，可以在Modrinth上搜索安装！',
            '需要安装什么模组？可以试试搜索"JEI"、"OptiFine"等关键词！',
        ],
        'version': [
            '版本管理页面可以安装各种Minecraft版本，支持Forge/Fabric等。',
            '最新的稳定版和快照版都可以在版本页面找到并一键安装！',
        ],
        'joke': [
            '为什么苦力怕不玩扑克？因为每次拿到Creeper(炸弹)都会爆炸！',
            '你知道末影人最害怕什么吗？是水…还有雨伞！',
            'Steve去餐厅点了一份牛排，服务员问他要几分熟，他说："要钻石级！"',
        ],
        'tip': [
            '💡 小技巧：使用F3 + T可以快速重载材质包。',
            '💡 小技巧：潜行时放置方块可以精确放置在指定位置。',
            '💡 小技巧：按F3 + B可以显示实体的碰撞箱。',
            '💡 小技巧：使用§符号可以在命名牌上使用彩色文字。',
            '💡 小技巧：在聊天框中按上箭头可以重复上一条指令。',
        ],
        'greeting_morning': ['早上好！今天是探索Minecraft的好日子！'],
        'greeting_evening': ['晚上好~ 在Minecraft的世界里，夜晚更需要小心哦！'],
        'unknown': [
            '嗯...我不太明白你的意思，试试说"帮助"看看？',
            '抱歉，我还不太理解这个命令。需要我帮忙的话就说"帮助"吧！',
            '我还需要学习更多！不过你可以试试"帮助"来了解我的功能。',
        ],
    }

    def __init__(self):
        self.config = Config()
        self.context = []
        self.user_name = ''

    def process_message(self, message: str) -> str:
        msg = message.lower().strip()
        self.context.append({'role': 'user', 'message': message, 'time': time.time()})

        if len(self.context) > 10:
            self.context = self.context[-10:]

        hour = datetime.now().hour

        greetings = ['你好', 'hi', 'hello', '嗨', '早上好', '晚上好', '在吗', 'hey', '您好']
        helps = ['帮助', 'help', '功能', '你会什么', '你能做什么', '怎么用']
        launches = ['启动', '开始游戏', '开始玩', '进入游戏', 'play']
        mods = ['模组', 'mod', '安装模组', '找模组', '模组管理']
        versions = ['版本', '安装版本', '更新', 'forge', 'fabric']
        jokes = ['笑话', 'joke', '搞笑', '哈哈哈', '讲个笑话', '段子']
        tips = ['技巧', 'tip', '提示', '小技巧', '教程', '攻略']
        names = ['叫我', '我叫', '我的名字', '我是']
        thank = ['谢谢', '感谢', 'thank', 'thx', '谢谢啦']
        goodbye = ['再见', '拜拜', 'bye', '退出', '告辞']

        if any(k in msg for k in thank):
            return '不客气！有什么需要随时找我~ 😊'

        if any(k in msg for k in goodbye):
            return '拜拜~ 下次见！祝你在Minecraft玩得开心！⛏️'

        if hour < 12 and ('早上' in msg or '早' in msg):
            return random.choice(self.responses['greeting_morning'])
        if hour >= 18 and ('晚上' in msg or '晚安' in msg):
            return random.choice(self.responses['greeting_evening'])

        for name_k in names:
            if name_k in msg:
                parts = msg.split(name_k)
                if len(parts) > 1 and parts[1].strip():
                    self.user_name = parts[1].strip()
                    return f'好的{self.user_name}！以后我就叫你{self.user_name}啦~'

        if any(k in msg for k in greetings):
            name_part = f' {self.user_name}' if self.user_name else ''
            return random.choice(self.responses['greeting']) + name_part

        if any(k in msg for k in helps):
            return random.choice(self.responses['help'])

        if any(k in msg for k in launches):
            return random.choice(self.responses['launch'])

        if any(k in msg for k in mods):
            return random.choice(self.responses['mod'])

        if any(k in msg for k in versions):
            return random.choice(self.responses['version'])

        if any(k in msg for k in jokes):
            return random.choice(self.responses['joke'])

        if any(k in msg for k in tips):
            return random.choice(self.responses['tip'])

        return random.choice(self.responses['unknown'])


class BotScheduler:
    def __init__(self):
        self.config = Config()
        self.tasks = []
        self._running = False
        self._thread = None

    def add_task(self, name, task_type, cron_expr, action):
        self.tasks.append({
            'name': name,
            'type': task_type,
            'cron': cron_expr,
            'action': action,
            'enabled': True,
            'last_run': 0,
        })

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            for task in self.tasks:
                if not task.get('enabled'):
                    continue
                now = time.time()
                if now - task.get('last_run', 0) >= 3600:
                    try:
                        task['action']()
                        task['last_run'] = now
                    except:
                        pass
            time.sleep(60)
