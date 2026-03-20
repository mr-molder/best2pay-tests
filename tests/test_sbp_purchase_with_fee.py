import pytest
import time

def test_sbp_purchase_with_fee(client, callback_server_fixture):
    amount = 1000
    currency = 643

    # Рассчитываем комиссию для СБП
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

    # Формируем параметры регистрации
    register_params = {
        'amount': amount,
        'currency': currency,
        'description': "SBP purchase with fee",
        'email': "test@example.com",
        'notify_url': callback_server_fixture.url,
        'reference': f"sbpfee_{int(time.time())}",
        'ps': 11
    }
    # Передаём fee только если она ненулевая
    if fee_value != 0:
        register_params['fee'] = fee_value
        print(f"Передаём комиссию: {fee_value}")
    else:
        print("Комиссия равна 0, не передаём параметр fee")

    # Регистрация заказа
    order = client.register(**register_params)
    if 'id' not in order:
        pytest.fail(f"Регистрация заказа не удалась: {order}")

    order_id = int(order['id'])
    print(f"Заказ создан, order_id: {order_id}")

    # Вызов PurchaseSBP (редирект, ответ не проверяем)
    client.purchase_sbp(order_id=order_id)

    # Имитация успешной оплаты через SBPTestCase
    client.sbp_test_case(case_id=150, order_id=order_id)

    # Ожидание обработки
    time.sleep(5)

    # Проверка статуса заказа
    order_info = client.order(order_id=order_id, get_token=0)
    print(f"Статус заказа: {order_info.get('state')}")

    if 'error' in order_info:
        pytest.fail(f"Запрос заказа вернул ошибку: {order_info}")

    if order_info.get('state') not in ('COMPLETED', 'APPROVED'):
        pytest.fail(f"Заказ не завершён. Статус: {order_info.get('state')}")

    print(f"Оплата по СБП с комиссией успешна, заказ {order_id}")