import pytest
import time

def test_sbp_purchase_with_fee(client, callback_server_fixture):
    amount = 1000
    currency = 643

    # Расчёт комиссии для СБП
    fee_resp = client.payment_fee(
        amount=amount,
        currency=currency,
        ps=11,
        mode=2
    )

    if 'error' in fee_resp:
        pytest.fail(f"Ошибка расчёта комиссии: {fee_resp}")
    fee_value = int(fee_resp.get('fee_value', 0))
    print(f"Рассчитанная комиссия для СБП: {fee_value} копеек")

    # Регистрация заказа с комиссией
    order = client.register(
        amount=amount,
        currency=currency,
        description="SBP purchase with fee",
        email="test@example.com",
        notify_url=callback_server_fixture.url,
        reference=f"sbpfee_{int(time.time())}",
        ps=11,
        fee=fee_value
    )
    if 'id' not in order:
        pytest.fail(f"Регистрация заказа не удалась: {order}")

    order_id = int(order['id'])
    print(f"Заказ создан, order_id: {order_id}")

    # Отправка PurchaseSBP
    client.purchase_sbp(order_id=order_id)

    # Имитация успешной оплаты через SBPTestCase
    client.sbp_test_case(case_id=150, order_id=order_id)

    # Ждём обработки
    time.sleep(5)

    # Проверка статуса заказа
    order_info = client.order(order_id=order_id, get_token=0)
    print(f"Статус заказа: {order_info.get('state')}")

    if 'error' in order_info:
        pytest.fail(f"Запрос заказа вернул ошибку: {order_info}")

    # Успех, если статус COMPLETED или APPROVED
    if order_info.get('state') not in ('COMPLETED', 'APPROVED'):
        pytest.fail(f"Заказ не завершён. Статус: {order_info.get('state')}")

    print(f"Оплата по СБП с комиссией успешна, заказ {order_id}, комиссия {fee_value}")