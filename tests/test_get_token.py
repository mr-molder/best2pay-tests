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
        pytest.fail(f"Оплата не удалась: {resp}")
    assert resp['state'] == 'APPROVED'
    assert resp['reason_code'] == '1'

    token = resp.get('token')
    if not token:
        pytest.fail(f"Токен не получен в ответе: {resp}")

    save_token(token)
    print(f"\nТокен успешно получен: {token}\n")