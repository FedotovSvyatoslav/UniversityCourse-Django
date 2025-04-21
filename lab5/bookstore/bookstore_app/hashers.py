import hashlib
import base64
import os
from django.contrib.auth.hashers import BasePasswordHasher, mask_hash
from django.utils.crypto import constant_time_compare


class CustomSHA256PasswordHasher(BasePasswordHasher):
    """
    Кастомный хэшер, использующий SHA256 с солью и итерациями.
    Формат: custom_sha256$iterations$salt$hash
    """
    algorithm = "custom_sha256"
    iterations = 100000  # Количество итераций
    digest = hashlib.sha256

    def salt(self):
        """Генерирует случайную соль."""
        return base64.b64encode(os.urandom(12)).decode('ascii')

    def encode(self, password, salt, iterations=None):
        """Кодирует пароль в формате: algorithm$iterations$salt$hash"""
        if not iterations:
            iterations = self.iterations
        # Хэшируем пароль с солью
        hash_value = self._hash(password, salt, iterations)
        return f"{self.algorithm}${iterations}${salt}${hash_value}"

    def _hash(self, password, salt, iterations):
        """Выполняет хэширование с солью и итерациями."""
        # Конкатенируем пароль и соль
        value = (password + salt).encode('utf-8')
        for _ in range(iterations):
            value = self.digest(value).digest()
        # Кодируем результат в base64
        return base64.b64encode(value).decode('ascii').strip()

    def verify(self, password, encoded):
        """Проверяет, соответствует ли введённый пароль захэшированному."""
        try:
            algorithm, iterations, salt, hash_value = encoded.split('$', 3)
            if algorithm != self.algorithm:
                return False
            iterations = int(iterations)
            # Хэшируем введённый пароль
            computed_hash = self._hash(password, salt, iterations)
            # Сравниваем в константном времени
            return constant_time_compare(hash_value, computed_hash)
        except (ValueError, TypeError):
            return False

    def safe_summary(self, encoded):
        """Возвращает безопасное описание хэша для отображения в админке."""
        algorithm, iterations, salt, hash_value = encoded.split('$', 3)
        return {
            'algorithm': algorithm,
            'iterations': iterations,
            'salt': mask_hash(salt),
            'hash': mask_hash(hash_value),
        }

    def must_update(self, encoded):
        """Проверяет, нужно ли обновить хэш (например, если изменились
        итерации). """
        algorithm, iterations, salt, hash_value = encoded.split('$', 3)
        return int(iterations) != self.iterations
