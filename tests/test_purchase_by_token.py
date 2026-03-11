import pytest
import time
from helpers.token_storage import load_token, save_token

def test_purchase_by_token(client, test_card, callback_server_fixture):
    # Пытаемся загрузить сохранённый токен
    token = load_token()
    need_new_token = False

    if token is None:
        print("Сохранённый токен не найден, будет получен новый.")
        need_new_token = True
    else:
        print(f"Используем сохранённый токен: {token}")

    # Функция для получения нового токена (аналогично test_get_token)
    def get_new_token():
        nonlocal token
        order = client.register(
            amount=1000,
            currency=643,
            description="Get token for purchase by token",
            email="test@example.com",
            notify_url=callback_server_fixture.url,
            reference=f"newtoken_{int(time.time())}"
        )
        if 'id' not in order:
            pytest.fail(f"Регистрация заказа для получения токена не удалась: {order}")

        order_id = int(order['id'])

        resp = client.gateway_payment(
            order_id=order_id,
            pan=test_card['pan'],
            month=test_card['month'],
            year=test_card['year'],
            cvc=test_card['cvc'],
            preauth='N',
            name="Cardholder Name",
            get_token=1
        )

        if 'state' not in resp:
            pytest.fail(f"Оплата для получения токена не удалась: {resp}")
        assert resp['state'] == 'APPROVED'
        assert resp['reason_code'] == '1'

        token = resp.get('token')
        if not token:
            pytest.fail(f"Токен не получен в ответе: {resp}")
        save_token(token)
        print(f"Новый токен получен и сохранён: {token}")
        return token

    # Если нужно получить новый токен
    if need_new_token:
        token = get_new_token()

    # Теперь пробуем оплатить по токену
    # Регистрируем новый заказ для оплаты по токену
    order = client.register(
        amount=1500,
        currency=643,
        description="Purchase by token",
        email="test@example.com",
        notify_url=callback_server_fixture.url,
        reference=f"purchbytoken_{int(time.time())}"
    )
    if 'id' not in order:
        pytest.fail(f"Регистрация заказа для оплаты по токену не удалась: {order}")

    order_id = int(order['id'])

    resp = client.purchase_by_token(
        order_id=order_id,
        token=token
    )

    # Проверяем результат
    if 'state' in resp and resp['state'] == 'APPROVED':
        assert resp['reason_code'] == '1'
        print("Оплата по токену успешна.")
        return

    # Если ошибка и это не последняя попытка, пробуем получить новый токен и повторить
    if resp.get('code') in ('299', '167', '130'):  # возможные коды: invalid token, operation not supported, internal error
        print(f"Оплата по токену не удалась (код {resp.get('code')}), пробуем получить новый токен...")
        token = get_new_token()

        # Повторяем оплату с новым токеном
        order = client.register(
            amount=1500,
            currency=643,
            description="Purchase by token (retry)",
            email="test@example.com",
            notify_url=callback_server_fixture.url,
            reference=f"purchbytoken_retry_{int(time.time())}"
        )
        if 'id' not in order:
            pytest.fail(f"Регистрация заказа повторно не удалась: {order}")

        order_id = int(order['id'])

        resp = client.purchase_by_token(
            order_id=order_id,
            token=token
        )

        if 'state' not in resp or resp['state'] != 'APPROVED':
            pytest.fail(f"Оплата по токену после повторного получения не удалась: {resp}")
        assert resp['reason_code'] == '1'
        print("Оплата по токену после повторного получения успешна.")
    else:
        pytest.fail(f"Оплата по токену не удалась: {resp}")