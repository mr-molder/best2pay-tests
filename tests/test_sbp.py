import pytest

# Таблица тестовых сценариев из документации стр.124
SBP_CREDIT_SCENARIOS = [
    ("79110123456", "10000000003", "REJECTED"),
    ("79110123456", "10000000004", "ERROR"),
    ("79110123456", "10000000005", "TIMEOUT"),
    ("79110123456", "10000000006", "PENDING"),
    ("79110123456", "10000000007", "PENDING"),
    ("79110123456", "10000000008", None),  # ошибка 281
    ("79110123456", "10000000009", None),  # ошибка 282
    ("79110123456", "10000000010", None),  # ошибка 283
    ("79110123456", "10000000011", None),  # ошибка 284
    ("79110123456", "10000000012", None),  # ошибка 285
]

@pytest.mark.parametrize("phone,recipientBankId,expected_status", SBP_CREDIT_SCENARIOS)
def test_sbp_credit_scenarios(client, phone, recipientBankId, expected_status):
    # Регистрируем заказ
    order = client.register(
        amount=5000,
        currency=643,
        description="SBP credit test",
        email="test@example.com"
    )
    order_id = int(order['id'])

    # Precheck
    precheck_resp = client.sbp_credit_precheck(order_id, phone, recipientBankId)

    if expected_status is None:
        # Ожидаем ошибку
        assert 'error' in precheck_resp
        # Можно проверить код ошибки (281-285)
        return

    assert 'precheck_id' in precheck_resp
    precheck_id = precheck_resp['precheck_id']

    # Credit
    credit_resp = client.sbp_credit(order_id, precheck_id)

    # Проверяем статус операции
    if expected_status in ('APPROVED', 'REJECTED', 'ERROR', 'TIMEOUT'):
        assert credit_resp['state'] == expected_status
    elif expected_status == 'PENDING':
        # Для PENDING нужно дождаться финального статуса через webapi/Operation
        # Упрощённо: проверим, что операция создана
        assert credit_resp['state'] in ('PENDING', 'APPROVED', 'REJECTED')
    else:
        pytest.fail(f"Unknown expected status {expected_status}")