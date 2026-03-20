import pytest
import time

def test_p2p_credit(client, test_card):
    """
    Тест выплаты на карту (P2PCredit) и проверки баланса.
    """
    # Шаг 1: Получаем текущий баланс счета сектора
    nonce = int(time.time() * 1000)  # уникальный номер
    balance_resp = client.p2p_credit_balance(nonce)
    print("P2PCreditBalance ответ:", balance_resp)

    # Проверяем, что нет ошибки
    if 'error' in balance_resp:
        pytest.fail(f"Ошибка получения баланса: {balance_resp}")
    initial_amount = int(balance_resp.get('amount', 0))
    print(f"Начальный баланс: {initial_amount} копеек")

    # Шаг 2: Регистрируем заказ для выплаты
    amount = 10000  # 100 рублей
    currency = 643
    reference = f"p2pcred_{int(time.time())}"
    order = client.register(
        amount=amount,
        currency=currency,
        description="P2P Credit test",
        email="test@example.com",
        reference=reference
    )
    if 'id' not in order:
        pytest.fail(f"Регистрация заказа не удалась: {order}")
    order_id = int(order['id'])
    print(f"Заказ создан, order_id: {order_id}")

    # Шаг 3: Выполняем выплату на карту получателя (используем ту же тестовую карту)
    # В реальности карта получателя может быть другой, но в тесте подойдёт.
    credit_resp = client.p2p_credit(
        order_id=order_id,
        pan=test_card['pan'],
        # Можно также передать month/year/cvc? По документации для выплаты не требуются.
        # Для перевода на иностранную карту нужны дополнительные поля (address, city...), но мы их опустим.
    )
    print("P2PCredit ответ:", credit_resp)

    # Проверяем успешность выплаты
    if 'error' in credit_resp:
        pytest.fail(f"Ошибка выплаты: {credit_resp}")
    if 'state' in credit_resp:
        assert credit_resp['state'] == 'APPROVED'
    elif 'order_state' in credit_resp:
        assert credit_resp['order_state'] == 'COMPLETED'
    else:
        # Если ответ не содержит state, возможно, это XML с operation
        if 'id' in credit_resp:
            print(f"Операция создана, operation_id={credit_resp['id']}")
        else:
            pytest.fail(f"Неожиданный ответ выплаты: {credit_resp}")

    # Шаг 4: Проверяем обновлённый баланс
    time.sleep(2)  # небольшая задержка для обработки
    new_nonce = nonce + 1
    new_balance_resp = client.p2p_credit_balance(new_nonce)
    print("Новый баланс:", new_balance_resp)
    if 'error' in new_balance_resp:
        pytest.fail(f"Ошибка получения нового баланса: {new_balance_resp}")
    new_amount = int(new_balance_resp.get('amount', 0))

    # Проверяем, что баланс уменьшился на сумму выплаты (или примерно)
    # Может быть комиссия, поэтому допускаем уменьшение не строго на amount
    if new_amount >= initial_amount:
        pytest.fail(f"Баланс не уменьшился: было {initial_amount}, стало {new_amount}")
    print(f"Баланс уменьшился на {initial_amount - new_amount} копеек")
    print("Тест выплаты успешно пройден")