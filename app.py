from flask import Flask, request, render_template, jsonify
import subprocess
import tempfile
import os
import sys
import traceback

app = Flask(__name__)

# Словарь с описанием доступных сценариев
SCENARIOS = {
    'purchase_success': {
        'name': 'Успешная оплата (PURCHASE)',
        'test_path': 'tests/test_purchase.py::test_gateway_payment_success'
    },
    'sbp_credit_success': {
        'name': 'СБП-выплата (CreditPrecheck и Credit)',
        'test_path': 'tests/test_sbp.py::test_sbp_credit_scenarios[79110123456-10000000002-APPROVED]'
    },
    'identification_success': {
        'name': 'Идентификация (успех)',
        'test_path': 'tests/test_identification.py::test_identification_success'
    },
    'card_enroll': {
        'name': 'Привязка карты (CardEnroll)',
        'test_path': 'tests/test_card_enroll.py::test_card_enroll'
    },
    'get_token': {
        'name': 'Получение токена',
        'test_path': 'tests/test_get_token.py::test_get_token'
    },
    'purchase_by_token': {
        'name': 'Оплата по токену',
        'test_path': 'tests/test_purchase_by_token.py::test_purchase_by_token'
    },
    'sbp_subscription': {
        'name': 'Привязка СБП (GetSBPSubscription)',
        'test_path': 'tests/test_sbp_subscription.py::test_sbp_subscription'
    },
    'get_sbp_token': {
        'name': 'Получение SBP-токена (требуется ручное подтверждение)',
        'test_path': 'tests/test_get_sbp_token.py::test_get_sbp_token'
    },
    'sbp_purchase_by_token': {
        'name': 'Оплата по SBP-токену',
        'test_path': 'tests/test_sbp_purchase_by_token.py::test_sbp_purchase_by_token'
    },
        'get_sbp_token_via_subscription': {
        'name': 'Получение SBP-токена через подписку',
        'test_path': 'tests/test_get_sbp_token_via_subscription.py::test_get_sbp_token_via_subscription'
    },
    'get_sbp_token': {
        'name': 'Получение SBP-токена',
        'test_path': 'tests/test_get_sbp_token.py::test_get_sbp_token'
    },
    'purchase_with_fee': {
        'name': 'Оплата с комиссией (PURCHASE)',
        'test_path': 'tests/test_purchase_with_fee.py::test_purchase_with_fee'
    },
    'sbp_purchase_with_fee': {
        'name': 'Оплата СБП с комиссией',
        'test_path': 'tests/test_sbp_purchase_with_fee.py::test_sbp_purchase_with_fee'
    }
    # Добавьте другие сценарии по мере необходимости
}

@app.route('/')
def index():
    """Главная страница с формой."""
    return render_template('index.html', scenarios=SCENARIOS)

@app.route('/run_test', methods=['POST'])
def run_test():
    """Запуск выбранного теста с переданными параметрами."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        sector = data.get('sector')
        password = data.get('password')
        scenario_key = data.get('scenario')
        algorithm = data.get('algorithm', 'sha256')

        # Валидация
        if not sector:
            return jsonify({'error': 'Сектор (ID) обязателен'}), 400
        if not password:
            return jsonify({'error': 'Пароль обязателен'}), 400
        if not scenario_key:
            return jsonify({'error': 'Сценарий не выбран'}), 400

        if scenario_key not in SCENARIOS:
            return jsonify({'error': f'Неизвестный сценарий: {scenario_key}'}), 400

        # Подготавливаем переменные окружения
        env = os.environ.copy()
        env['B2P_SECTOR'] = str(sector)
        env['B2P_PASSWORD'] = password
        env['B2P_ALGORITHM'] = algorithm
        env['B2P_URL'] = 'https://test.best2pay.net'
        project_root = os.path.dirname(os.path.abspath(__file__))
        env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')

        # Временный файл (бинарный режим)
        with tempfile.NamedTemporaryFile(mode='wb+', suffix='.txt', delete=False) as tmp:
            tmp_filename = tmp.name

        # Команда для запуска одного теста
        cmd = [
            sys.executable, '-m', 'pytest',
            SCENARIOS[scenario_key]['test_path'],
            '-v', '-s', '--tb=short'
        ]

        # Запускаем процесс, записываем stdout в бинарный файл
        with open(tmp_filename, 'wb') as outfile:
            result = subprocess.run(
                cmd,
                env=env,
                stdout=outfile,
                stderr=subprocess.STDOUT,
                timeout=60
            )

        # Читаем бинарные данные
        with open(tmp_filename, 'rb') as infile:
            raw_data = infile.read()

        # Пытаемся декодировать как UTF-8, если не получается – как cp1251
        try:
            output = raw_data.decode('utf-8')
        except UnicodeDecodeError:
            output = raw_data.decode('cp1251', errors='replace')

        # Удаляем временный файл
        os.unlink(tmp_filename)

        return jsonify({
            'success': result.returncode == 0,
            'output': output
        })

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Тест превысил время ожидания (60 секунд)'}), 500
    except Exception as e:
        print("Ошибка в /run_test:", file=sys.stderr)
        traceback.print_exc()
        return jsonify({'error': f'Внутренняя ошибка сервера: {str(e)}'}), 500
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)