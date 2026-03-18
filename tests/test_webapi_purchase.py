import pytest
import time

def test_webapi_purchase_success(client, test_card, callback_server_fixture):
    # Регистрируем заказ
    order = client.register(
        amount=1000,
        currency=643,
        description="Test webapi Purchase",
        email="test@example.com",
        notify_url=callback_server_fixture.url,
        reference=f"webapipurch_{int(time.time())}"
    )
    if 'id' not in order:
        pytest.fail(f"Регистрация заказа не удалась: {order}")
    order_id = int(order['id'])
    print(f"Заказ создан, order_id: {order_id}")

    # Выполняем оплату через webapi/Purchase с action=pay
    resp = client.webapi_purchase(
        order_id=order_id,
        pan=test_card['pan'],
        month=test_card['month'],
        year=test_card['year'],
        cvc=test_card['cvc'],
        action='pay'
    )

    print("webapi_purchase ответ:", resp)

    # Если ответ содержит state, проверяем APPROVED
    if isinstance(resp, dict) and 'state' in resp:
        assert resp['state'] == 'APPROVED'
        assert resp['reason_code'] == '1'
        print("Оплата через webapi/Purchase успешна")
    elif isinstance(resp, dict) and 'error' in resp:
        pytest.fail(f"Ошибка: {resp}")
    else:
        # Если редирект – извлекаем operation_id и проверяем статус
        if 'operation' in resp:
            print(f"Операция создана, operation_id={resp['operation']}, проверяем статус...")
            time.sleep(2)
            op_info = client.operation(order_id=order_id, operation_id=int(resp['operation']), get_token=0)
            if 'error' in op_info:
                pytest.fail(f"Ошибка при проверке операции: {op_info}")
            assert op_info.get('state') == 'APPROVED'
            print("Оплата через webapi/Purchase (с редиректом) успешна")
        else:
            pytest.fail(f"Неожиданный ответ: {resp}")