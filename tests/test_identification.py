import pytest

def test_identification_success(client):
    first_name = "Дмитрий"
    patronymic = "Александрович"
    last_name = "Кузьмин"
    birth_date = "1996.02.23"
    persondoc_number = "4523681953"

    resp = client.identification_status(
        first_name=first_name,
        patronymic=patronymic,
        last_name=last_name,
        birth_date=birth_date,
        persondoc_number=persondoc_number
    )

    # Если есть поле error или identification_state отсутствует, выводим ответ
    if 'error' in resp or 'identification_state' not in resp:
        pytest.fail(f"Ошибка идентификации. Ответ сервера: {resp}")

    state = resp['identification_state']
    if state not in ('SENT', 'APPROVED'):
        pytest.fail(f"Неожиданный статус идентификации: {state}")