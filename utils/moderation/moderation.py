from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict

class ModerationSystem:
    def __init__(self, ban_time: int = 300):
        self.ban_time = ban_time
        self.banned_users = {}
        self.ban_reasons = {}
        self.user_warnings = defaultdict(list)
        self.ban_messages = {}  # ← НОВОЕ: {user_id: (chat_id, message_id)}
    
    def ban_user(self, user_id: int, reason: str) -> None:
        now = datetime.now()
        self.banned_users[user_id] = now + timedelta(seconds=self.ban_time)
        self.ban_reasons[user_id] = reason
        self.user_warnings[user_id].append({
            'time': now,
            'reason': reason
        })
    
    def unban_user(self, user_id: int) -> bool:
        """Разблокирует пользователя и удаляет сообщение с кнопками"""
        if user_id in self.banned_users:
            del self.banned_users[user_id]
            if user_id in self.ban_reasons:
                del self.ban_reasons[user_id]
            
            self.user_warnings[user_id] = []  # Сбрасываем предупреждения
            return True
        return False
    
    def set_ban_message(self, user_id: int, chat_id: int, message_id: int):
        """Сохраняем ID сообщения с кнопками"""
        self.ban_messages[user_id] = (chat_id, message_id)
    
    async def delete_ban_message(self, user_id: int, bot):
        """Удаляет сообщение с кнопками"""
        if user_id in self.ban_messages:
            chat_id, message_id = self.ban_messages[user_id]
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                print(f"Ошибка удаления сообщения: {e}")
            del self.ban_messages[user_id]
    
    def is_banned(self, user_id: int) -> tuple[bool, int]:
        """
        Проверяет, заблокирован ли пользователь.
        Возвращает: (заблокирован, секунд_до_разблокировки)
        """
        if user_id not in self.banned_users:
            return False, 0
        
        now = datetime.now()
        unban_time = self.banned_users[user_id]
        
        # Если время блокировки прошло - автоматически разблокируем
        if now >= unban_time:
            self.unban_user(user_id)
            return False, 0
        
        time_left = int((unban_time - now).total_seconds())
        return True, time_left
    
    def get_ban_reason(self, user_id: int) -> str:
        """Возвращает причину блокировки"""
        return self.ban_reasons.get(user_id, "Неизвестная причина")
    
    def get_warnings_count(self, user_id: int) -> int:
        """Возвращает количество предупреждений"""
        return len(self.user_warnings[user_id])