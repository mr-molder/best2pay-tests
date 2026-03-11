import pytest
import time
from helpers.client import Best2PayClient
from helpers.sbp_token_storage import save_sbp_token

def test_get_sbp_token(client, callback_server_fixture):
    """
    Получение активированного SBP-токена:
    1. Вызов GetSBPSubscription на секторе 9053 для получения qrcId и токена.
    2. Активация токена через SBPTestCase с case_id=154 и qrcId.
    3. Сохранение токена.
    """
    # Создаём клиента для сектора 9053 (используем тот же пароль и алгоритм, что и основной)
    client_9053 = Best2PayClient(
        sector=9053,
        password=client.password,
        base_url=client.base_url,
        algorithm=client.algorithm
    )

    description = f"Test subscription {int(time.time())}"
    
    # Шаг 1: получаем qrcId и токен
    resp = client_9053.get_sbp_subscription(
        description=description,
        url="https://example.com/callback",
        get_qr_img=0
    )

    if isinstance(resp, dict) and 'error' in resp:
        pytest.fail(f"GetSBPSubscription вернул ошибку: {resp}")

    print("GetSBPSubscription ответ:", resp)

    qrc_id = resp.get('qrcId')
    token = resp.get('token')

    if not qrc_id:
        pytest.fail("qrcId не получен в ответе GetSBPSubscription")
    if not token:
        pytest.fail("Токен не получен в ответе GetSBPSubscription")

    print(f"Получен qrcId: {qrc_id}, токен: {token}")

    # Шаг 2: активируем токен через SBPTestCase (case_id=154)
    activate_resp = client_9053.sbp_test_case(
        case_id=154,
        qrc_id=qrc_id
    )

    if isinstance(activate_resp, dict) and 'error' in activate_resp:
        pytest.fail(f"SBPTestCase вернул ошибку при активации: {activate_resp}")

    print("Активация выполнена, ответ:", activate_resp)

    # Шаг 3: сохраняем токен
    save_sbp_token(token)
    print(f"\nSBP-токен успешно получен и активирован: {token}\n")