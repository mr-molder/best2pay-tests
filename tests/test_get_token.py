import pytest
import time
from helpers.token_storage import save_token

def test_get_token(client, test_card, callback_server_fixture):
    order = client.register(
        amount=1000,
        currency=643,
        description="Get token payment",
        email="test@example.com",
        notify_url=callback_server_fixture.url,
        reference=f"gettoken_{int(time.time())}"
    )
    if 'id' not in order:
        pytest.fail(f"Регистрация заказа не удалась: {order}")

    order_id = int(order['id'])

    resp = client.webapi_purchase(
        order_id=order_id,
        pan=test_card['pan'],
        month=test_card['month'],
        year=test_card['year'],
        cvc=test_card['cvc'],
        action='pay',
        name="Cardholder Name",
        get_token=1
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
            # Получаем токен через operation
            time.sleep(1)
            # Нужно получить operation_id из заказа
            # Для этого можно использовать order_info, но там может не быть операции
            # Попробуем получить через order с get_token=1
            order_with_token = client.order(order_id=order_id, get_token=1)
            token = order_with_token.get('token')
            if token:
                save_token(token)
                print(f"Токен успешно получен: {token}")
                return
            else:
                # Если не получили, пробуем найти operation_id в заказе
                # Упростим: падаем с сообщением
                pytest.fail(f"Токен не найден в заказе: {order_with_token}")
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
            order_with_token = client.order(order_id=order_id, get_token=1)
            token = order_with_token.get('token')
            if token:
                save_token(token)
                print(f"Токен успешно получен: {token}")
                return
            else:
                pytest.fail(f"Токен не найден в заказе: {order_with_token}")
        else:
            pytest.fail(f"Заказ не завершён. Статус: {state}")

    # Если ответ содержит state и token сразу
    if isinstance(resp, dict) and 'state' in resp:
        assert resp['state'] == 'APPROVED'
        token = resp.get('token')
        if token:
            save_token(token)
            print(f"Токен успешно получен: {token}")
        else:
            # Если токена нет в ответе, пробуем получить через order
            order_with_token = client.order(order_id=order_id, get_token=1)
            token = order_with_token.get('token')
            if token:
                save_token(token)
                print(f"Токен успешно получен через order: {token}")
            else:
                pytest.fail(f"Токен не найден в ответе и в заказе")
        return

    # Если ответ содержит operation (редирект)
    if isinstance(resp, dict) and 'operation' in resp:
        print(f"Операция создана, operation_id={resp['operation']}, получаем токен...")
        time.sleep(2)
        op_info = client.operation(order_id=order_id, operation_id=int(resp['operation']), get_token=1)
        if 'error' in op_info:
            pytest.fail(f"Ошибка при получении операции: {op_info}")
        token = op_info.get('token')
        if token:
            save_token(token)
            print(f"Токен успешно получен через operation: {token}")
            return
        else:
            pytest.fail(f"Токен не найден в операции: {op_info}")

    # Если есть ошибка
    if isinstance(resp, dict) and 'error' in resp:
        pytest.fail(f"Ошибка: {resp}")

    # Если ничего не подошло
    pytest.fail(f"Неожиданный ответ: {resp}")