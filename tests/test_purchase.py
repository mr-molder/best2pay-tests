import pytest
import time

def test_purchase_success(client, test_card, callback_server_fixture):
    order = client.register(
        amount=1000,
        currency=643,
        description="Test purchase",
        email="test@example.com",
        notify_url=callback_server_fixture.url,
        reference=f"purch_{int(time.time())}"
    )
    if 'id' not in order:
        pytest.fail(f"Регистрация заказа не удалась: {order}")

    order_id = int(order['id'])
    print(f"Заказ создан, order_id: {order_id}")

    resp = client.webapi_purchase(
        order_id=order_id,
        pan=test_card['pan'],
        month=test_card['month'],
        year=test_card['year'],
        cvc=test_card['cvc'],
        action='pay',
        name="Cardholder Name"
    )

    print("webapi_purchase ответ:", resp)

    # Если ответ содержит raw_response (HTML страница)
    if isinstance(resp, dict) and 'raw_response' in resp:
        print("Получен HTML ответ, проверяем статус заказа...")
        time.sleep(2)
        order_info = client.order(order_id=order_id, get_token=0)
        if 'error' in order_info:
            pytest.fail(f"Ошибка при проверке заказа: {order_info}")
        state = order_info.get('state')
        if state in ('COMPLETED', 'APPROVED'):
            print(f"Заказ успешно завершён, статус: {state}")
            return
        else:
            pytest.fail(f"Заказ не завершён. Статус: {state}")

    # Если ответ пустой
    if not resp or (isinstance(resp, dict) and not resp):
        print("Ответ от purchase пустой, проверяем статус заказа...")
        time.sleep(2)
        order_info = client.order(order_id=order_id, get_token=0)
        if 'error' in order_info:
            pytest.fail(f"Ошибка при проверке заказа: {order_info}")
        state = order_info.get('state')
        if state in ('COMPLETED', 'APPROVED'):
            print(f"Заказ успешно завершён, статус: {state}")
            return
        else:
            pytest.fail(f"Заказ не завершён. Статус: {state}")

    # Если ответ содержит state
    if isinstance(resp, dict) and 'state' in resp:
        assert resp['state'] == 'APPROVED'
        assert resp['reason_code'] == '1'
        print("Оплата через webapi/Purchase успешна")
        return

    # Если ответ содержит operation (редирект)
    if isinstance(resp, dict) and 'operation' in resp:
        print(f"Операция создана, operation_id={resp['operation']}, проверяем статус...")
        time.sleep(2)
        op_info = client.operation(order_id=order_id, operation_id=int(resp['operation']), get_token=0)
        if 'error' in op_info:
            pytest.fail(f"Ошибка при проверке операции: {op_info}")
        if op_info.get('state') == 'APPROVED':
            print("Оплата через webapi/Purchase (с редиректом) успешна")
            return
        else:
            pytest.fail(f"Операция не одобрена. Статус: {op_info.get('state')}")

    # Если есть ошибка
    if isinstance(resp, dict) and 'error' in resp:
        pytest.fail(f"Ошибка: {resp}")

    # Если ничего не подошло
    pytest.fail(f"Неожиданный ответ: {resp}")