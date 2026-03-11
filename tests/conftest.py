import os
import pytest
from helpers.client import Best2PayClient
from helpers.callback_server import callback_server

@pytest.fixture(scope='session')
def sector():
    return int(os.getenv('B2P_SECTOR', '1'))

@pytest.fixture(scope='session')
def password():
    return os.getenv('B2P_PASSWORD', 'test')

@pytest.fixture(scope='session')
def base_url():
    return os.getenv('B2P_URL', 'https://test.best2pay.net')

@pytest.fixture(scope='session')
def algorithm():
    return os.getenv('B2P_ALGORITHM', 'sha256')

@pytest.fixture(scope='session')
def client(sector, password, base_url, algorithm):
    return Best2PayClient(sector, password, base_url, algorithm)

@pytest.fixture
def callback_server_fixture():
    """Запускает и останавливает callback-сервер для теста."""
    callback_server.start()
    callback_server.clear()
    yield callback_server
    callback_server.stop()

@pytest.fixture
def test_card():
    """Тестовая карта (без 3DS)."""
    return {
        'pan': '4986290000000080',
        'month': 8,
        'year': 2025,
        'cvc': '721'
    }