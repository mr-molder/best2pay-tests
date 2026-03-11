import hashlib
import base64

def generate_signature(params: list, algorithm: str = 'sha256') -> str:
    """
    Генерирует подпись для запроса/ответа Best2Pay.
    :param params: Список значений параметров в порядке, указанном в документации, включая пароль.
    :param algorithm: 'sha256' или 'md5'.
    :return: Подпись в формате Base64 от hex-строки хеша.
    """
    raw_string = ''.join(str(p) for p in params)

    if algorithm.lower() == 'sha256':
        hash_bytes = hashlib.sha256(raw_string.encode('utf-8')).digest()
    elif algorithm.lower() == 'md5':
        hash_bytes = hashlib.md5(raw_string.encode('utf-8')).digest()
    else:
        raise ValueError("Unsupported algorithm, use 'sha256' or 'md5'")

    hex_hash = hash_bytes.hex()
    signature = base64.b64encode(hex_hash.encode()).decode()
    return signature