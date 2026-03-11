import pytest

def test_gateway_payment_success(client, test_card, callback_server_fixture):
    order = client.register(
        amount=1000,
        currency=643,
        description="Test purchase",
        email="test@example.com",
        notify_url=callback_server_fixture.url,
        reference="test_ref_123"
    )
    if 'id' not in order:
        pytest.fail(f"Регистрация заказа не удалась. Ответ сервера: {order}")

    order_id = int(order['id'])

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
        pytest.fail(f"Ошибка операции: {resp.get('description', 'неизвестно')} (код {resp.get('code', '?')})")

    assert resp['state'] == 'APPROVED'
    assert resp['reason_code'] == '1'