import requests
import threading
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs
from .signature import generate_signature

class Best2PayClient:
    def __init__(self, sector: int, password: str, base_url: str, algorithm: str = 'sha256'):
        self.sector = sector
        self.password = password
        self.base_url = base_url.rstrip('/')
        self.algorithm = algorithm
        self.session = requests.Session()

    def _post(self, endpoint: str, data: dict) -> requests.Response:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if 'sector' not in data:
            data['sector'] = self.sector
        resp = self.session.post(url, data=data)
        return resp

    def _parse_response(self, resp: requests.Response):
        if resp.status_code == 302:
            location = resp.headers['Location']
            parsed = urlparse(location)
            query = parse_qs(parsed.query)
            return {k: v[0] for k, v in query.items()}
        
        content_type = resp.headers.get('Content-Type', '')
        
        # Если ответ пустой (200 OK, но нет тела) – возвращаем пустой словарь
        if not resp.text:
            return {}
            
        if 'text/plain' in content_type:
            return resp.text.strip()
        elif 'xml' in content_type:
            return self._xml_to_dict(resp.text)
        else:
            # Для неизвестного типа – пытаемся вернуть как текст
            return {'raw_response': resp.text}

    def _xml_to_dict(self, xml_str: str) -> dict:
        root = ET.fromstring(xml_str)
        result = {}
        for elem in root.iter():
            if elem.text and elem.text.strip():
                result[elem.tag] = elem.text.strip()
        return result

    # ---- Методы API ----

    def register(self, amount: int, currency: int, description: str,
             reference: str = None, url: str = None, failurl: str = None,
             email: str = None, phone: str = None, ps: int = None,
             recurring_period: int = None, fiscal_data: str = None,
             notify_url: str = None, fee: int = None, **kwargs) -> dict:
        params = {
            'amount': amount,
            'currency': currency,
            'description': description,
        }
        if reference:
            params['reference'] = reference
        if url:
            params['url'] = url
        if failurl:
            params['failurl'] = failurl
        if email:
            params['email'] = email
        if phone:
            params['phone'] = phone
        if ps is not None:
            params['ps'] = ps
        if recurring_period is not None:
            params['recurring_period'] = recurring_period
        if fiscal_data:
            params['fiscalData'] = fiscal_data
        if notify_url:
            params['notify_url'] = notify_url
        if fee is not None:
            params['fee'] = fee
        params.update(kwargs)

        # Подпись: sector, amount, currency, password (fee не участвует)
        signature = generate_signature(
            [self.sector, params['amount'], params['currency'], self.password],
            algorithm=self.algorithm
        )
        params['signature'] = signature
        print(signature)

        resp = self._post('/webapi/Register', params)
        return self._parse_response(resp)

    def gateway_payment(self, order_id: int, pan: str, month: int, year: int,
                        cvc: str, preauth: str = 'N', amount: int = None,
                        currency: int = None, **kwargs) -> dict:
        params = {
            'id': order_id,
            'pan': pan,
            'month': month,
            'year': year,
            'cvc': cvc,
            'preauth': preauth,
        }
        if amount:
            params['amount'] = amount
        if currency:
            params['currency'] = currency
        params.update(kwargs)

        signature = generate_signature(
            [self.sector,
             order_id,
             pan,
             kwargs.get('token', ''),
             kwargs.get('name', ''),
             month,
             year,
             cvc,
             amount if amount else '',
             currency if currency else '',
             preauth,
             kwargs.get('transaction_id', ''),
             kwargs.get('unique_key', ''),
             kwargs.get('cof_ind', ''),
             self.password],
            algorithm=self.algorithm
        )
        params['signature'] = signature

        resp = self._post('/gateweb/Payment', params)
        return self._parse_response(resp)

    def reverse(self, order_id: int, amount: int, currency: int,
                unique_key: str = None) -> dict:
        params = {
            'id': order_id,
            'amount': amount,
            'currency': currency,
        }
        if unique_key:
            params['unique_key'] = unique_key

        signature = generate_signature(
            [self.sector, order_id, amount, currency, unique_key or '', self.password],
            algorithm=self.algorithm
        )
        params['signature'] = signature

        resp = self._post('/webapi/Reverse', params)
        return self._parse_response(resp)

    def recurring(self, order_id: int, amount: int, currency: int,
                  fee: int = None) -> dict:
        params = {
            'id': order_id,
            'amount': amount,
            'currency': currency,
        }
        if fee is not None:
            params['fee'] = fee

        signature = generate_signature(
            [self.sector, order_id, amount, currency, self.password],
            algorithm=self.algorithm
        )
        params['signature'] = signature

        resp = self._post('/webapi/Recurring', params)
        return self._parse_response(resp)

    def sbp_credit_precheck(self, order_id: int, phone: str,
                            recipient_bank_id: str) -> dict:
        params = {
            'id': order_id,
            'phone': phone,
            'recipientBankId': recipient_bank_id,
        }
        signature = generate_signature(
            [self.sector, order_id, recipient_bank_id, phone, self.password],
            algorithm=self.algorithm
        )
        params['signature'] = signature

        resp = self._post('/webapi/sbp/SBPCreditPrecheck', params)
        return self._parse_response(resp)

    def sbp_credit(self, order_id: int, precheck_id: str) -> dict:
        params = {
            'id': order_id,
            'precheck_id': precheck_id,
        }
        signature = generate_signature(
            [self.sector, order_id, precheck_id, self.password],
            algorithm=self.algorithm
        )
        params['signature'] = signature

        resp = self._post('/webapi/sbp/SBPCredit', params)
        return self._parse_response(resp)

    def identification_status(self, first_name: str, patronymic: str, last_name: str,
                              birth_date: str, persondoc_number: str) -> dict:
        """
        Запрос на идентификацию физлица (webapi/b2puser/IdentificationStatus).
        """
        params = {
            'first_name': first_name,
            'patronymic': patronymic,
            'last_name': last_name,
            'birth_date': birth_date,
            'persondoc_number': persondoc_number,
        }
        signature = generate_signature(
            [self.sector, first_name, patronymic, last_name, birth_date, persondoc_number, self.password],
            algorithm=self.algorithm
        )
        params['signature'] = signature

        resp = self._post('/webapi/b2puser/IdentificationStatus', params)
        return self._parse_response(resp)
    
    def card_enroll(self, order_id: int, cof_ind: str = None) -> dict:
        """
        Регистрация карты и получение токена (webapi/CardEnroll).
        :param order_id: ID заказа
        :param cof_ind: опциональный параметр для карт МИР
        """
        params = {'id': order_id}
        if cof_ind:
            params['cof_ind'] = cof_ind

        # Подпись: sector, id, cof_ind?, password
        sig_parts = [self.sector, order_id]
        if cof_ind:
            sig_parts.append(cof_ind)
        sig_parts.append(self.password)

        signature = generate_signature(sig_parts, algorithm=self.algorithm)
        params['signature'] = signature

        resp = self._post('/webapi/CardEnroll', params)
        return self._parse_response(resp)

    def operation(self, order_id: int, operation_id: int, get_token: int = 0) -> dict:
        """
        Получение информации по операции (webapi/Operation).
        :param order_id: ID заказа
        :param operation_id: ID операции
        :param get_token: 1 - запросить токен
        """
        params = {
            'id': order_id,
            'operation': operation_id,
            'get_token': get_token
        }
        signature = generate_signature(
            [self.sector, order_id, operation_id, self.password],
            algorithm=self.algorithm
        )
        params['signature'] = signature
        resp = self._post('/webapi/Operation', params)
        return self._parse_response(resp)

    def purchase_by_token(self, order_id: int, token: str, cvc: str = None, cof_ind: str = None) -> dict:
        """
        Оплата по токену карты (webapi/PurchaseByToken).
        :param order_id: ID заказа
        :param token: токен карты
        :param cvc: код безопасности (необязательно)
        :param cof_ind: опционально для карт МИР
        """
        params = {
            'id': order_id,
            'token': token,
        }
        if cvc:
            params['cvc'] = cvc
        if cof_ind:
            params['cof_ind'] = cof_ind

        # Подпись: sector, id, token, cvc?, cof_ind?, password
        sig_parts = [self.sector, order_id, token]
        if cvc:
            sig_parts.append(cvc)
        if cof_ind:
            sig_parts.append(cof_ind)
        sig_parts.append(self.password)

        signature = generate_signature(sig_parts, algorithm=self.algorithm)
        params['signature'] = signature

        resp = self._post('/webapi/PurchaseByToken', params)
        return self._parse_response(resp)

    def get_sbp_subscription(self, description: str, url: str = None, life_period: int = None, get_qr_img: int = None) -> dict:
        """
        Регистрация СБП-привязки без оплаты (webapi/GetSBPSubscription).
        :param description: Назначение привязки (отображается в банке)
        :param url: Ссылка для возврата в приложение ТСП
        :param life_period: Срок жизни ссылки в минутах
        :param get_qr_img: 1 - получить QR-код
        """
        params = {'description': description}
        if url:
            params['url'] = url
        if life_period:
            params['life_period'] = life_period
        if get_qr_img is not None:
            params['get_qr_img'] = get_qr_img

        # Подпись ТОЛЬКО из sector и description (согласно документации)
        sig_parts = [self.sector, description, self.password]
        
        signature = generate_signature(sig_parts, algorithm=self.algorithm)
        params['signature'] = signature

        # Отладка
        print(f"DEBUG GetSBPSubscription sig_parts: {sig_parts}")
        print(f"DEBUG GetSBPSubscription signature: {signature}")
        print(f"DEBUG GetSBPSubscription params: {params}")

        resp = self._post('/webapi/GetSBPSubscription', params)
        return self._parse_response(resp)

    def purchase_sbp(self, order_id: int, get_token: int = None) -> dict:
        """
        Оплата QR-кодом СБП (webapi/PurchaseSBP).
        :param order_id: ID заказа
        :param get_token: 1 - запросить токен
        """
        params = {'id': order_id}
        if get_token is not None:
            params['get_token'] = get_token

        signature = generate_signature(
            [self.sector, order_id, self.password],
            algorithm=self.algorithm
        )
        params['signature'] = signature

        resp = self._post('/webapi/PurchaseSBP', params)
        return self._parse_response(resp)

    def purchase_sbp_by_token(self, order_id: int, token: str) -> dict:
        params = {
            'id': order_id,
            'token': token
        }
        signature = generate_signature(
            [self.sector, order_id, token, self.password],
            algorithm=self.algorithm
        )
        params['signature'] = signature
        resp = self._post('/webapi/PurchaseSBPByToken', params)
        return self._parse_response(resp)

    def sbp_test_case(self, case_id: int, order_id: int = None, qrc_id: str = None) -> dict:
        """
        Проведение тест-кейсов СБП (test/SBPTestCase) - только для тестового стенда.
        :param case_id: номер тест-кейса (case_id)
        :param order_id: ID заказа (необязательно, если указан qrc_id)
        :param qrc_id: идентификатор функциональной ссылки (необязательно, если указан order_id)
        """
        params = {'case_id': case_id}
        if order_id:
            params['order_id'] = order_id
        if qrc_id:
            params['qrc_id'] = qrc_id
        if not (order_id or qrc_id):
            raise ValueError("Either order_id or qrc_id must be provided")

        # Подпись: sector, case_id, qrc_id (пустая строка, если нет), order_id (пустая строка, если нет), password
        sig_parts = [
            self.sector,
            case_id,
            qrc_id if qrc_id else '',
            order_id if order_id else '',
            self.password
        ]
        signature = generate_signature(sig_parts, algorithm=self.algorithm)
        params['signature'] = signature

        resp = self._post('/test/SBPTestCase', params)
        return self._parse_response(resp)
    
    def purchase_sbp_by_token_async(self, order_id: int, token: str):
        """
        Отправляет запрос PurchaseSBPByToken в фоновом потоке, не дожидаясь ответа.
        """
        def target():
            try:
                # Используем отдельную сессию, чтобы избежать конфликтов
                with requests.Session() as session:
                    url = f"{self.base_url}/webapi/PurchaseSBPByToken"
                    params = {'id': order_id, 'token': token}
                    signature = generate_signature(
                        [self.sector, order_id, token, self.password],
                        algorithm=self.algorithm
                    )
                    params['signature'] = signature
                    session.post(url, data=params, timeout=5)
            except Exception:
                pass  # игнорируем ошибки, так как нам не важен ответ

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()

    def order(self, order_id: int = None, reference: str = None, mode: int = None, get_token: int = None) -> dict:
        """
        Получение информации по заказу (webapi/Order).
        """
        params = {}
        if order_id:
            params['id'] = order_id
        if reference:
            params['reference'] = reference
        if mode is not None:
            params['mode'] = mode
        if get_token is not None:
            params['get_token'] = get_token

        # Подпись: sector, id, reference, password
        sig_parts = [self.sector]
        if order_id:
            sig_parts.append(order_id)
        if reference:
            sig_parts.append(reference)
        sig_parts.append(self.password)

        signature = generate_signature(sig_parts, algorithm=self.algorithm)
        params['signature'] = signature

        resp = self._post('/webapi/Order', params)
        return self._parse_response(resp)
    
    def payment_fee(self, amount: int, currency: int, ps: int = None, pan: str = None, token: str = None, mode: int = 2) -> dict:
        params = {
            'amount': amount,
            'currency': currency,
            'mode': mode
        }
        if ps is not None:
            params['ps'] = ps
        if pan:
            params['pan'] = pan
        if token:
            params['token'] = token
        if not (pan or token or ps):
            raise ValueError("Необходимо указать pan, token или ps")

        # Формируем подпись с фиксированным порядком: sector, amount, ps, pan, token, password
        # Недостающие заменяем пустой строкой
        sig_parts = [
            self.sector,
            amount,
            ps if ps is not None else '',
            pan if pan else '',
            token if token else '',
            self.password
        ]
        signature = generate_signature(sig_parts, algorithm=self.algorithm)
        params['signature'] = signature
        print(signature)

        resp = self._post('/webapi/PaymentFee', params)

        if mode == 0:
            text = resp.text.strip()
            return {'fee_value': int(text) if text.lstrip('-').isdigit() else -1}
        else:
            return self._parse_response(resp)
        
    def webapi_purchase(self, order_id: int, pan: str = None, month: int = None, year: int = None,
                    cvc: str = None, action: str = None, payer_id: str = None,
                    pan_token_sha256: str = None, cof_ind: str = None, **kwargs) -> dict:
        """
        Оплата через webapi/Purchase (с редиректом или action=pay).
        :param order_id: ID заказа
        :param pan: номер карты
        :param month: месяц срока действия
        :param year: год срока действия
        :param cvc: код безопасности
        :param action: 'pay' для синхронного проведения
        :param payer_id: идентификатор плательщика на стороне ТСП
        :param pan_token_sha256: хеш pan_token (если используется)
        :param cof_ind: признак COF для карт МИР
        :return: словарь с ответом (XML или параметры редиректа)
        """
        params = {'id': order_id}
        if pan:
            params['pan'] = pan
        if month:
            params['month'] = month
        if year:
            params['year'] = year
        if cvc:
            params['cvc'] = cvc
        if action:
            params['action'] = action
        if payer_id:
            params['payer_id'] = payer_id
        if pan_token_sha256:
            params['pan_token_sha256'] = pan_token_sha256
        if cof_ind:
            params['cof_ind'] = cof_ind
        params.update(kwargs)

        # Подпись: sector, id, payer_id, pan_token_sha256, cof_ind, password
        sig_parts = [
            self.sector,
            order_id,
            payer_id if payer_id else '',
            pan_token_sha256 if pan_token_sha256 else '',
            cof_ind if cof_ind else '',
            self.password
        ]
        signature = generate_signature(sig_parts, algorithm=self.algorithm)
        params['signature'] = signature

        resp = self._post('/webapi/Purchase', params)
        return self._parse_response(resp)
    
    def p2p_credit(self, order_id: int = None, amount: int = None, currency: int = None,
               reference: str = None, pan: str = None, token: str = None,
               address: str = None, city: str = None, post_code: str = None,
               countrynum: str = None, name: str = None, receiver_name: str = None,
               get_token: int = None, email: str = None) -> dict:
        """
        Зачисление средств на карту со счета ТСП (gateweb/P2PCredit).
        Должен быть указан либо order_id, либо amount+currency+reference.
        Также должен быть указан либо pan, либо token.
        """
        params = {}
        if order_id:
            params['id'] = order_id
        if amount is not None:
            params['amount'] = amount
        if currency is not None:
            params['currency'] = currency
        if reference:
            params['reference'] = reference
        if pan:
            params['pan'] = pan
        if token:
            params['token'] = token
        if address:
            params['address'] = address
        if city:
            params['city'] = city
        if post_code:
            params['post_code'] = post_code
        if countrynum:
            params['countrynum'] = countrynum
        if name:
            params['name'] = name
        if receiver_name:
            params['receiver_name'] = receiver_name
        if get_token is not None:
            params['get_token'] = get_token
        if email:
            params['email'] = email

        # Проверка наличия обязательных групп
        if not (order_id or (amount is not None and currency is not None and reference)):
            raise ValueError("Необходимо указать либо order_id, либо amount+currency+reference")
        if not (pan or token):
            raise ValueError("Необходимо указать либо pan, либо token")

        # Подпись: sector, id, amount, currency, pan, token, password
        sig_parts = [
            self.sector,
            order_id if order_id else '',
            amount if amount is not None else '',
            currency if currency is not None else '',
            pan if pan else '',
            token if token else '',
            self.password
        ]
        signature = generate_signature(sig_parts, algorithm=self.algorithm)
        params['signature'] = signature

        resp = self._post('/gateweb/P2PCredit', params)
        return self._parse_response(resp)

    def p2p_credit_balance(self, nonce: int) -> dict:
        """
        Получение баланса счета сектора для выплат (webapi/P2PCreditBalance).
        :param nonce: уникальный номер запроса (должен увеличиваться)
        """
        params = {'nonce': nonce}
        signature = generate_signature([self.sector, nonce, self.password], algorithm=self.algorithm)
        params['signature'] = signature
        resp = self._post('/webapi/P2PCreditBalance', params)
        return self._parse_response(resp)