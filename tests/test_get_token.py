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

    if isinstance(resp, dict) and 'state' in resp:
        assert resp['state'] == 'APPROVED'
        token = resp.get('token')
        if not token:
            pytest.fail(f"Токен не получен в ответе: {resp}")
        save_token(token)
        print(f"Токен успешно получен: {token}")
    else:
        if 'operation' in resp:
            op_id = int(resp['operation'])
            time.sleep(2)
            op_info = client.operation(order_id=order_id, operation_id=op_id, get_token=1)
            if 'error' in op_info:
                pytest.fail(f"Ошибка получения операции: {op_info}")
            token = op_info.get('token')
            if not token:
                pytest.fail(f"Токен не найден в операции: {op_info}")
            save_token(token)
            print(f"Токен успешно получен через operation: {token}")
        else:
            pytest.fail(f"Неожиданный ответ: {resp}")