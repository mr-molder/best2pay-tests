import os
import json

TOKEN_FILE = os.path.join(os.path.dirname(__file__), '..', 'token.json')

def save_token(token: str):
    """Сохраняет токен в файл."""
    with open(TOKEN_FILE, 'w') as f:
        json.dump({'token': token}, f)

def load_token():
    """Загружает токен из файла. Возвращает None, если файла нет."""
    try:
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            return data.get('token')
    except (FileNotFoundError, json.JSONDecodeError):
        return None