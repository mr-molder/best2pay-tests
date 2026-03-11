import os
import json

SBP_TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', 'sbp_token.json')

def save_sbp_token(token: str):
    """Сохраняет SBP-токен в файл."""
    with open(SBP_TOKEN_FILE, 'w') as f:
        json.dump({'token': token}, f)

def load_sbp_token():
    """Загружает SBP-токен из файла. Возвращает None, если файла нет."""
    try:
        with open(SBP_TOKEN_FILE, 'r') as f:
            data = json.load(f)
            return data.get('token')
    except (FileNotFoundError, json.JSONDecodeError):
        return None