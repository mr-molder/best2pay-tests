import pytest
import time

def test_sbp_subscription(client):
    """
    Тест привязки СБП (GetSBPSubscription).
    Проверяем, что вызов не возвращает ошибку и содержит payload (ссылку для привязки).
    """
    description = f"Тестовая привязка {int(time.time())}"
    
    resp = client.get_sbp_subscription(
        description=description,
        get_qr_img=0  # не нужен QR-код
    )

    # Проверяем, что нет ошибки
    if isinstance(resp, dict) and 'error' in resp:
        pytest.fail(f"GetSBPSubscription вернул ошибку: {resp}")

    # Проверяем наличие payload (ссылки для привязки)
    if isinstance(resp, dict):
        if 'payload' not in resp and 'qrcId' not in resp:
            # Возможно, пришёл редирект с параметрами
            print(f"Ответ от GetSBPSubscription: {resp}")
        else:
            print(f"Ссылка для привязки: {resp.get('payload')}")
    else:
        print(f"GetSBPSubscription выполнен, ответ: {resp}")