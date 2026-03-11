import pytest
import time
from helpers.sbp_token_storage import load_sbp_token

def test_sbp_purchase_by_token(client, callback_server_fixture):
    token = load_sbp_token()
    if token is None:
        pytest.fail("SBP-токен не найден. Сначала выполните тест 'Получение SBP-токена'")

    print(f"Используем сохранённый SBP-токен: {token}")

    # 1. Регистрируем заказ
    order = client.register(
        amount=1500,
        currency=643,
        description="Purchase by SBP token",
        email="test@example.com",
        notify_url=callback_server_fixture.url,
        reference=f"sbppurch_{int(time.time())}",
        ps=11
    )
    if 'id' not in order:
        pytest.fail(f"Регистрация заказа не удалась: {order}")

    order_id = int(order['id'])
    print(f"Заказ создан, order_id: {order_id}")

    # 2. Отправляем PurchaseSBPByToken асинхронно (не ждём ответа)
    client.purchase_sbp_by_token_async(order_id=order_id, token=token)

    # 3. Сразу вызываем SBPTestCase для имитации оплаты
    client.sbp_test_case(case_id=150, order_id=order_id)

    # 4. Ждём 5 секунд, чтобы сервер обработал запросы
    time.sleep(5)

    # 5. Проверяем статус операции через Order
    order_info = client.order(order_id=order_id, get_token=0)
    print(f"Статус операции: {order_info.get('state')}")

    if 'error' in order_info:
        pytest.fail(f"Запрос заказа вернул ошибку: {order_info}")

    # Принимаем как успех статусы COMPLETED или APPROVED
    if order_info.get('state') not in ('COMPLETED', 'APPROVED'):
        pytest.fail(f"Заказ не завершён. Статус: {order_info.get('state')}")

    print("Оплата по SBP-токену успешна.")