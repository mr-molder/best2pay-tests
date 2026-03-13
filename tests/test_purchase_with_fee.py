import pytest
import time

def test_purchase_with_fee(client, test_card, callback_server_fixture):
    amount = 1000
    currency = 643

    # Рассчитываем комиссию, передаём только pan (без ps)
    fee_resp = client.payment_fee(
        amount=amount,
        currency=currency,
        # pan=test_card['pan'],
        ps=1,          # явно указываем платёжную систему (1 - Visa)
        mode=0
    )

    # Проверяем наличие ошибки
    if 'error' in fee_resp:
        pytest.fail(f"Ошибка расчёта комиссии: {fee_resp}")

    # Извлекаем значение комиссии
    fee_value = fee_resp.get('fee_value')
    if fee_value is None:
        pytest.fail(f"Ответ не содержит fee_value: {fee_resp}")
    fee_value = int(fee_value)
    print(f"Рассчитанная комиссия: {fee_value} копеек")

    # Регистрируем заказ с комиссией (fee не участвует в подписи)
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

    # Оплата
    resp = client.gateway_payment(
        order_id=order_id,
        pan=test_card['pan'],
        month=test_card['month'],
        year=test_card['year'],
        cvc=test_card['cvc'],
        preauth='N',
        name="Cardholder Name"
    )

    if 'state' not in resp:
        pytest.fail(f"Оплата не удалась: {resp}")
    assert resp['state'] == 'APPROVED'
    assert resp['reason_code'] == '1'

    print(f"Оплата успешна, заказ {order_id}, комиссия {fee_value}")