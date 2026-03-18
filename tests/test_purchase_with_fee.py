import pytest
import time

def test_purchase_with_fee(client, test_card, callback_server_fixture):
    amount = 1000
    currency = 643

    fee_resp = client.payment_fee(
        amount=amount,
        currency=currency,
        pan=test_card['pan'],
        ps=1,
        mode=2
    )

    if 'error' in fee_resp:
        pytest.fail(f"Ошибка расчёта комиссии: {fee_resp}")
    fee_value = int(fee_resp.get('fee_value', 0))
    print(f"Рассчитанная комиссия: {fee_value} копеек")

    order = client.register(
        amount=amount,
        currency=currency,
        description="Purchase with fee",
        email="test@example.com",
        notify_url=callback_server_fixture.url,
        reference=f"purchfee_{int(time.time())}",
        fee=fee_value
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

    if isinstance(resp, dict) and 'state' in resp:
        assert resp['state'] == 'APPROVED'
        assert resp['reason_code'] == '1'
    elif isinstance(resp, dict) and 'error' in resp:
        pytest.fail(f"Ошибка: {resp}")
    else:
        if 'operation' in resp:
            print(f"Операция создана, проверяем статус...")
            time.sleep(2)
            op_info = client.operation(order_id=order_id, operation_id=int(resp['operation']), get_token=0)
            if 'error' in op_info:
                pytest.fail(f"Ошибка при проверке операции: {op_info}")
            assert op_info.get('state') == 'APPROVED'
        else:
            pytest.fail(f"Неожиданный ответ: {resp}")

    print(f"Оплата успешна, заказ {order_id}, комиссия {fee_value}")