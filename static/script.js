// ====================== ОБЩИЕ ФУНКЦИИ ======================
function showTab(tabIndex) {
    document.querySelectorAll('.tab-content').forEach((el, i) => {
        el.classList.toggle('active', i === tabIndex);
    });
    document.querySelectorAll('.tab-button').forEach((el, i) => {
        el.classList.toggle('active', i === tabIndex);
    });
}

// ====================== ВКЛАДКА 1: ГЕНЕРАТОР ======================
document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generateButton');
    if (generateBtn) {
        generateBtn.addEventListener('click', () => {
            const accessType = document.getElementById('accessType').value;
            const login = document.getElementById('login').value.trim();
            const hashType = document.getElementById('hashType').value;
            const sectors = document.getElementById('sectors').value.trim();

            let fixedText = '';

            if (accessType === 'combat') {
                fixedText = `Добрый день!  

Создан боевой доступ 

Личный кабинет:
https://pay.best2pay.net/personal-area/

Login: ${login}

${sectors}

URL для отправки запросов: https://pay.best2pay.net/webapi/

sign_hash=${hashType}

Пароль цифровой подписи для формирования HTTP-запросов:
Доступен в новом ЛК на вкладке "Администрирование" -> "Секторы"`;
            } else if (accessType === 'test') {
                fixedText = `Добрый день, коллеги.

Созданы тестовые доступы.

Ссылка на тестовый ЛК Б2П:
https://test.best2pay.net/personal-area/#/auth/login

Login: ${login}

Тестовые секторы:

${sectors}

Пароль цифровой подписи для формирования HTTP-запросов:
Доступен в новом ЛК на вкладке "Администрирование" -> "Секторы"
Алгоритм хеширования ${hashType}`;
            }

            document.getElementById('generator-output').value = fixedText;
            document.getElementById('copyButton').style.display = 'inline-block';
        });
    }

    const copyBtn = document.getElementById('copyButton');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const output = document.getElementById('generator-output');
            output.select();
            document.execCommand('copy');
            const original = copyBtn.textContent;
            copyBtn.textContent = '✅ Скопировано!';
            setTimeout(() => copyBtn.textContent = original, 2000);
        });
    }
});

// ====================== ВКЛАДКА 2: ТЕСТИРОВАНИЕ ======================
async function runTest() {
    const sector = document.getElementById('sector').value.trim();
    const password = document.getElementById('password').value.trim();
    const algorithm = document.getElementById('algorithm').value;
    const scenario = document.getElementById('scenario').value;

    if (!sector || !password) {
        document.getElementById('tester-output').innerHTML = '<span class="error-message">❌ Пожалуйста, заполните все поля</span>';
        return;
    }

    const data = { sector, password, algorithm, scenario };
    const outputEl = document.getElementById('tester-output');
    outputEl.innerHTML = '⏳ Запуск теста...';

    try {
        const response = await fetch('/run_test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            outputEl.innerHTML = '<span class="failure">❌ Ошибка сервера: получен не JSON</span><br><br>' + text;
            return;
        }

        const result = await response.json();

        if (result.error) {
            outputEl.innerHTML = '<span class="failure">❌ Ошибка:</span><br><br>' + result.error;
        } else if (result.success) {
            outputEl.innerHTML = '<span class="success">✅ ТЕСТ ПРОЙДЕН</span><br><br>' + result.output;
        } else {
            outputEl.innerHTML = '<span class="failure">❌ ТЕСТ НЕ ПРОЙДЕН</span><br><br>' + result.output;
        }
    } catch (error) {
        outputEl.innerHTML = '<span class="failure">❌ Ошибка соединения:</span><br><br>' + error;
    }
}

// ====================== ВКЛАДКА 3: ДОНАСТРОЙКА СЕКТОРОВ ======================
document.addEventListener('DOMContentLoaded', function() {
    // Данные
    const handlesList = [
        'IdentificationStatus', 'P2PCredit', 'P2PCreditBalance', 'Order', 'Operation', 'GetOperationConfirmation',
        'SBPCredit', 'SBPCreditPrecheck', 'SBPCreditBalance', 'GetSBPBankList', 'PurchaseSBP', 'Purchase',
        'PurchaseByToken', 'PurchaseSBPByToken', 'CardEnroll', 'GetSBPSubscription', 'PaymentFee'
    ];

    const settingsConfig = [
        { id: 'sync', label: 'прожать sync' },
        { id: 'stub_sbpcredit', label: 'включить stub mode на SBPCredit' },
        { id: 'vyplaty_karty', label: 'настроить выплаты на карты' },
        { id: 'vyplaty_sbp', label: 'настроить выплаты на СБП' },
        { id: 'processor10', label: 'выставить 10-й процессор' },
        { id: 'sbp_merchants', label: 'настроить SBP Merchants' },
        { id: 'komissiya_check_fee', label: 'настроить комиссию check_fee' },
        { id: 'komissiya_sbp_fee', label: 'настроить комиссию для СБП fee' },
        { id: 'pogasheniya_karty', label: 'настроить погашения по картам' },
        { id: 'pogasheniya_sbp', label: 'настроить погашения по СБП' },
        { id: 'privyazka_rekurrenty', label: 'настроить привязку и рекурренты для карт + СБП' }
    ];

    // Расширенное маппирование для поддержки латиницы и кириллицы
    const typeMapping = {
        // СБП - поддерживаем оба варианта
        'СБП': 'SBP_FL',
        'СБП (ФЛ)': 'SBP_FL',
        'SBP': 'SBP_FL',
        'SBP_FL': 'SBP_FL',
        'sbp': 'SBP_FL',
        'FL': 'SBP_FL',
        
        // C2A - поддерживаем оба варианта
        'С2А': 'C2A_FL',
        'С2А (ФЛ)': 'C2A_FL',
        'C2A': 'C2A_FL',
        'C2A_FL': 'C2A_FL',
        'c2a': 'C2A_FL',
        
        // Другие типы
        'In': 'In',
        'In (ФЛ)': 'In_FL',
        'In(ФЛ)': 'In_FL',
        'Out': 'Out',
        'Token': 'Token',
        'SBP Token': 'SBP Token',
        'SBPТoken': 'SBP Token',
        'A2C': 'A2C',
        'СМЭВ': 'SMEV',
        'P2PCredit': 'P2PCredit',
        'SBPCredit': 'SBPCredit'
    };

    // Русские названия для вывода (всегда отображаем на русском)
    const russianType = {
        'SBP_FL': 'СБП',
        'C2A_FL': 'С2А',
        'In': 'In',
        'In_FL': 'In (ФЛ)',
        'Out': 'Out',
        'Token': 'Token',
        'SBP Token': 'SBP Token',
        'A2C': 'A2C',
        'SMEV': 'СМЭВ',
        'P2PCredit': 'P2PCredit',
        'SBPCredit': 'SBPCredit'
    };

    // Функция определения типа по разным вариантам написания
    function detectSectorType(inputText) {
        // Приводим к нижнему регистру и удаляем лишние пробелы
        const lowerInput = inputText.toLowerCase().trim();
        
        // Проверяем на СБП (разные варианты)
        if (lowerInput === 'сбп' || lowerInput === 'sbp' || lowerInput === 'fl' || 
            lowerInput.includes('сбп') || lowerInput.includes('sbp')) {
            return 'SBP_FL';
        }
        
        // Проверяем на C2A (разные варианты)
        if (lowerInput === 'с2а' || lowerInput === 'c2a' || 
            lowerInput.includes('с2а') || lowerInput.includes('c2a')) {
            return 'C2A_FL';
        }
        
        // Для остальных типов используем стандартное маппирование
        return null;
    }

    const sectorTypes = {
        'SMEV': { handles: ['IdentificationStatus'], settings: ['sync'] },
        'P2PCredit': { handles: ['P2PCredit', 'P2PCreditBalance', 'Order', 'Operation', 'GetOperationConfirmation'], settings: ['sync', 'vyplaty_karty'] },
        'SBPCredit': { handles: ['SBPCredit', 'SBPCreditPrecheck', 'SBPCreditBalance', 'GetSBPBankList', 'Order', 'Operation', 'GetOperationConfirmation'], settings: ['sync', 'stub_sbpcredit', 'vyplaty_sbp', 'processor10'] },
        'Out': { handles: ['P2PCredit', 'P2PCreditBalance', 'SBPCredit', 'SBPCreditPrecheck', 'SBPCreditBalance', 'GetSBPBankList', 'Order', 'Operation', 'GetOperationConfirmation'], settings: ['sync', 'vyplaty_karty', 'vyplaty_sbp', 'stub_sbpcredit', 'processor10'] },
        'In': { handles: ['PurchaseSBP', 'Purchase', 'Order', 'Operation', 'GetOperationConfirmation'], handlesNoComm: ['PurchaseByToken', 'PurchaseSBPByToken', 'CardEnroll', 'GetSBPSubscription'], settings: ['sync', 'sbp_merchants', 'komissiya_check_fee', 'pogasheniya_karty', 'pogasheniya_sbp'], settingsNoComm: ['privyazka_rekurrenty'] },
        'In_FL': { handles: ['PurchaseSBP', 'Purchase', 'Order', 'Operation', 'GetOperationConfirmation', 'PaymentFee'], settings: ['sync', 'sbp_merchants', 'komissiya_check_fee', 'pogasheniya_karty', 'pogasheniya_sbp'] },
        'Token': { handles: ['CardEnroll', 'Order', 'Operation', 'GetOperationConfirmation'], settings: ['sync', 'privyazka_rekurrenty'] },
        'SBP Token': { handles: ['GetSBPSubscription', 'PurchaseSBPByToken'], settings: ['sync', 'privyazka_rekurrenty'] },
        'A2C': { handles: ['P2PCredit', 'P2PCreditBalance', 'Order', 'Operation', 'GetOperationConfirmation'], settings: ['sync', 'vyplaty_karty'] },
        'C2A_FL': { handles: ['Purchase', 'Order', 'Operation', 'GetOperationConfirmation', 'PaymentFee'], settings: ['sync', 'komissiya_check_fee', 'pogasheniya_karty'] },
        'SBP_FL': { handles: ['PurchaseSBP', 'Order', 'Operation', 'GetOperationConfirmation', 'PaymentFee'], settings: ['sync', 'sbp_merchants', 'komissiya_sbp_fee', 'pogasheniya_sbp'] }
    };

    let sectors = [];
    let editingIndex = -1;

    // Элементы
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const addSectorBtn = document.getElementById('dona-addSectorButton');
    const closeBtn = document.querySelector('.close');
    const sectorTypeSelect = document.getElementById('sectorType');
    const hasCommCheckbox = document.getElementById('hasCommission');
    const commDetails = document.getElementById('commissionDetails');
    const handlesDiv = document.getElementById('handles');
    const settingsDiv = document.getElementById('settings');
    const modalActionBtn = document.getElementById('modalActionBtn');
    const generateBtn = document.getElementById('dona-generateButton');
    const copyBtn = document.getElementById('dona-copyButton');
    const outputDiv = document.getElementById('dona-output');
    const sectorsListDiv = document.getElementById('dona-sectorsList');
    const requestTitleInput = document.getElementById('dona-requestTitle');
    const loginInput = document.getElementById('dona-login');
    const sectorDataInput = document.getElementById('sectorData');
    const parseBtn = document.getElementById('parseSectorDataBtn');
    const modalError = document.getElementById('modal-error');

    const commissionTypeRadios = document.querySelectorAll('input[name="commissionType"]');
    const commissionPercent = document.getElementById('commissionPercent');
    const commissionFix = document.getElementById('commissionFix');
    const commissionMin = document.getElementById('commissionMin');
    const fixField = document.getElementById('fixField');
    const minField = document.getElementById('minField');
    const commissionHint = document.getElementById('commissionHint');

    // Создание чекбоксов
    handlesList.forEach(handle => {
        const label = document.createElement('label');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'handle-checkbox';
        checkbox.value = handle;
        label.appendChild(checkbox);
        let displayName = handle;
        if (handle === 'GetOperationConfirmation') displayName += ' (on custom email)';
        label.appendChild(document.createTextNode(' ' + displayName));
        handlesDiv.appendChild(label);
    });

    settingsConfig.forEach(setting => {
        const label = document.createElement('label');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'setting-checkbox';
        checkbox.value = setting.id;
        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(' ' + setting.label));
        settingsDiv.appendChild(label);
    });

    // Переключение комиссии
    function updateCommissionFields() {
        const selectedType = document.querySelector('input[name="commissionType"]:checked')?.value;
        if (selectedType === 'fix') {
            fixField.classList.remove('hidden');
            minField.classList.add('hidden');
            commissionHint.textContent = 'Для фиксированной: заполните хотя бы одно поле (процент или фикс).';
        } else {
            fixField.classList.add('hidden');
            minField.classList.remove('hidden');
            commissionHint.textContent = 'Для минимальной: заполните оба поля (процент и минимум).';
        }
    }
    commissionTypeRadios.forEach(radio => radio.addEventListener('change', updateCommissionFields));

    // Обновление формы
    function updateModalForm() {
        const type = sectorTypeSelect.value;
        const config = sectorTypes[type];
        if (!config) return;

        if (type === 'In_FL') {
            hasCommCheckbox.checked = true;
            hasCommCheckbox.disabled = true;
        } else {
            hasCommCheckbox.disabled = false;
        }

        commDetails.classList.toggle('hidden', !hasCommCheckbox.checked);

        document.querySelectorAll('.handle-checkbox').forEach(cb => cb.checked = false);
        config.handles.forEach(handle => {
            const cb = document.querySelector(`.handle-checkbox[value="${handle}"]`);
            if (cb) cb.checked = true;
        });
        if (type === 'In' && !hasCommCheckbox.checked && config.handlesNoComm) {
            config.handlesNoComm.forEach(handle => {
                const cb = document.querySelector(`.handle-checkbox[value="${handle}"]`);
                if (cb) cb.checked = true;
            });
        }

        document.querySelectorAll('.setting-checkbox').forEach(cb => cb.checked = false);
        config.settings.forEach(settingId => {
            const cb = document.querySelector(`.setting-checkbox[value="${settingId}"]`);
            if (cb) cb.checked = true;
        });
        if (type === 'In' && !hasCommCheckbox.checked && config.settingsNoComm) {
            config.settingsNoComm.forEach(settingId => {
                const cb = document.querySelector(`.setting-checkbox[value="${settingId}"]`);
                if (cb) cb.checked = true;
            });
        }

        if (type === 'SBPCredit' || type === 'Out') {
            ['stub_sbpcredit', 'processor10'].forEach(settingId => {
                const cb = document.querySelector(`.setting-checkbox[value="${settingId}"]`);
                if (cb) cb.checked = true;
            });
        }
    }

    // парсинг с поддержкой латиницы, комиссии и различных форматов
    function parseSectorData(input) {
        let cleanInput = input.trim().replace(/\t+/g, ' ');
        const sectorIdPrefix = /^sector\s*id:\s*/i;
        if (sectorIdPrefix.test(cleanInput)) cleanInput = cleanInput.replace(sectorIdPrefix, '');

        // Находим первую открывающую скобку
        const firstParenIndex = cleanInput.indexOf('(');
        if (firstParenIndex === -1) {
            return { error: 'Не найдена открывающая скобка' };
        }

        // Часть до первой скобки: ID и название
        const beforeFirstParen = cleanInput.substring(0, firstParenIndex).trim();
        const idMatch = beforeFirstParen.match(/^(\d+)/);
        if (!idMatch) {
            return { error: 'Не удалось определить ID сектора' };
        }
        const sectorId = idMatch[1];
        let jurName = beforeFirstParen.substring(sectorId.length).trim();
        if (!jurName) {
            return { error: 'Не удалось определить название сектора' };
        }

        // Собираем все скобки
        const allBrackets = [];
        let remaining = cleanInput.substring(firstParenIndex);
        const bracketRegex = /\(([^)]+)\)/g;
        let match;
        while ((match = bracketRegex.exec(remaining)) !== null) {
            allBrackets.push(match[1].trim());
        }

        if (allBrackets.length < 2) {
            return { error: 'Недостаточно данных: нужны сайт и тип сектора' };
        }

        const site = allBrackets[0];
        const typeRaw = allBrackets[1];
        let hasFL = false;
        let commissionPercent = null;

        // Обрабатываем остальные скобки (опции)
        for (let i = 2; i < allBrackets.length; i++) {
            const bracket = allBrackets[i];
            const bracketLower = bracket.toLowerCase();
            if (bracketLower === 'фл' || bracketLower === 'fl') {
                hasFL = true;
            } else if (/^[\d,\.]+$/.test(bracket) && !isNaN(parseFloat(bracket.replace(',', '.')))) {
                commissionPercent = parseFloat(bracket.replace(',', '.'));
            }
        }

        // Определяем тип сектора
        let sectorType = detectSectorType(typeRaw);
        if (!sectorType) {
            sectorType = typeMapping[typeRaw];
            if (!sectorType) {
                const possibleKeys = [typeRaw, typeRaw.replace(/\s+/g, ''), typeRaw.toUpperCase(), typeRaw.toLowerCase()];
                for (let key of possibleKeys) {
                    if (typeMapping[key]) {
                        sectorType = typeMapping[key];
                        break;
                    }
                }
            }
        }

        if (!sectorType) {
            return { error: `Неизвестный тип сектора: "${typeRaw}". Поддерживаемые типы: СБП, SBP, С2А, C2A, In, Out, Token, A2C, СМЭВ, P2PCredit, SBPCredit` };
        }

        // Если есть комиссия, автоматически включаем ФЛ
        if (commissionPercent !== null && commissionPercent > 0) {
            hasFL = true;
        }

        return {
            sectorId,
            jurName,
            site,
            sectorType,
            hasCommission: hasFL,
            commissionPercent: commissionPercent,
            error: null
        };
    }

    function fillFormFromParsed(parsed) {
    if (parsed.error) { modalError.textContent = parsed.error; return; }
    if (parsed.sectorType) sectorTypeSelect.value = parsed.sectorType;
    hasCommCheckbox.checked = parsed.hasCommission;
    
    if (parsed.commissionPercent !== null && parsed.commissionPercent > 0) {
        commissionPercent.value = parsed.commissionPercent;
        document.querySelector('input[name="commissionType"][value="fix"]').checked = true;
        commissionFix.value = 0;
    } else {
        commissionPercent.value = '';
        commissionFix.value = '';
        commissionMin.value = '';
    }
    
    updateCommissionFields();
    updateModalForm();
    modalError.textContent = '';
}

    parseBtn.addEventListener('click', () => {
        const raw = sectorDataInput.value.trim();
        if (!raw) { modalError.textContent = 'Введите данные сектора'; return; }
        const parsed = parseSectorData(raw);
        fillFormFromParsed(parsed);
    });

    sectorTypeSelect.addEventListener('change', updateModalForm);
    hasCommCheckbox.addEventListener('change', updateModalForm);

    // Открытие модалки
    addSectorBtn.addEventListener('click', () => {
        editingIndex = -1;
        modalTitle.textContent = 'Добавить сектор';
        modalActionBtn.textContent = 'Добавить в список';
        document.getElementById('sectorForm').reset();
        document.querySelector('input[name="commissionType"][value="fix"]').checked = true;
        hasCommCheckbox.disabled = false;
        updateCommissionFields();
        updateModalForm();
        modal.style.display = 'block';
        modalError.textContent = '';
    });

    closeBtn.addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', e => { if (e.target === modal) modal.style.display = 'none'; });

    // Сохранение сектора
    modalActionBtn.addEventListener('click', () => {
        const raw = sectorDataInput.value.trim();
        if (!raw) { modalError.textContent = 'Введите данные сектора'; return; }

        const parsed = parseSectorData(raw);
        if (parsed.error) { modalError.textContent = parsed.error; return; }

        const sectorId = parsed.sectorId;
        const jur = parsed.jurName;
        const site = parsed.site;

        const sectorType = sectorTypeSelect.value;
        const hasComm = hasCommCheckbox.checked;
        const commType = document.querySelector('input[name="commissionType"]:checked')?.value;

        const percVal = parseFloat(commissionPercent.value) || 0;
        const fixVal = parseFloat(commissionFix.value) || 0;
        const minVal = parseFloat(commissionMin.value) || 0;

        let commissionInfo = {};
        if (hasComm) {
            if (commType === 'fix') {
                if (percVal === 0 && fixVal === 0) { modalError.textContent = 'Заполните хотя бы одно поле'; return; }
                commissionInfo = { type: 'fix', percent: percVal, fix: fixVal };
            } else {
                if (percVal === 0 || minVal === 0) { modalError.textContent = 'Заполните оба поля'; return; }
                commissionInfo = { type: 'min', percent: percVal, min: minVal };
            }
        } else {
            commissionInfo = { type: 'none' };
        }

        const fl = hasComm ? ' (ФЛ)' : '';
        let percentSuffix = '';
        if (hasComm && commissionInfo.percent > 0) percentSuffix = ` (${commissionInfo.percent})`;

        // Всегда выводим русское название для СБП и С2А
        let typeRussianForDisplay = russianType[sectorType] || sectorType;
        
        // Дополнительная проверка для гарантии правильного отображения
        if (sectorType === 'SBP_FL') {
            typeRussianForDisplay = 'СБП';
        } else if (sectorType === 'C2A_FL') {
            typeRussianForDisplay = 'С2А';
        }
        
        const name = `${jur} (${site}) (${typeRussianForDisplay})${fl}${percentSuffix}`;

        const selectedHandles = Array.from(document.querySelectorAll('.handle-checkbox:checked')).map(cb => cb.value);
        const selectedSettingIds = Array.from(document.querySelectorAll('.setting-checkbox:checked')).map(cb => cb.value);

        const selectedSettings = [];
        document.querySelectorAll('.setting-checkbox:checked').forEach(cb => {
            const setting = settingsConfig.find(s => s.id === cb.value);
            if (!setting) return;
            let text = setting.label;
            if (setting.id.includes('komissiya') && hasComm) {
                if (commissionInfo.type === 'fix') {
                    const parts = [];
                    if (commissionInfo.percent > 0) parts.push(`${commissionInfo.percent}%`);
                    if (commissionInfo.fix > 0) parts.push(`${commissionInfo.fix} руб.`);
                    text += parts.length ? ` = ${parts.join(' + ')}` : ' = 0';
                } else {
                    text += ` = ${commissionInfo.percent}%, min = ${commissionInfo.min} руб.`;
                }
            }
            selectedSettings.push(text);
        });

        const sectorData = { id: sectorId, name, handles: selectedHandles, settings: selectedSettings, settingsIds: selectedSettingIds, commission: commissionInfo, sectorType: sectorType };

        if (editingIndex === -1) sectors.push(sectorData);
        else sectors[editingIndex] = sectorData;

        renderSectorsList();
        modal.style.display = 'none';
        document.getElementById('sectorForm').reset();
        document.querySelector('input[name="commissionType"][value="fix"]').checked = true;
        hasCommCheckbox.disabled = false;
        updateCommissionFields();
        updateModalForm();
        modalError.textContent = '';
    });

    function formatHandle(handle) {
        return handle === 'GetOperationConfirmation' ? 'GetOperationConfirmation (on custom email)' : handle;
    }

    function renderSectorsList() {
        sectorsListDiv.innerHTML = '';
        sectors.forEach((sec, index) => {
            const div = document.createElement('div');
            div.className = 'sector-item';
            let commStr = '';
            if (sec.commission.type !== 'none') {
                if (sec.commission.type === 'fix') {
                    const parts = [];
                    if (sec.commission.percent > 0) parts.push(`${sec.commission.percent}%`);
                    if (sec.commission.fix > 0) parts.push(`${sec.commission.fix} руб.`);
                    commStr = `Комиссия: ${parts.join(' + ')}`;
                } else {
                    commStr = `Комиссия: ${sec.commission.percent}%, min = ${sec.commission.min} руб.`;
                }
            }
            const formattedHandles = sec.handles.map(formatHandle).join(', ');
            div.innerHTML = 
                '<strong>Sector ID: ' + sec.id + ' ' + sec.name + '</strong><br>' +
                'Ручки: ' + formattedHandles + '<br>' +
                'Настройки: ' + sec.settings.join('; ') + '<br>' +
                (commStr ? commStr + '<br>' : '') +
                '<div class="sector-actions">' +
                '<button onclick="editSector(' + index + ')">Редактировать</button>' +
                '<button onclick="deleteSector(' + index + ')">Удалить</button>' +
                '</div>';
            sectorsListDiv.appendChild(div);
        });
        saveToLocalStorage();
    }

    window.deleteSector = (index) => {
        if (confirm('Удалить сектор?')) {
            sectors.splice(index, 1);
            renderSectorsList();
        }
    };

    // Редактирование сектора
    window.editSector = (index) => {
        editingIndex = index;
        modalTitle.textContent = 'Редактировать сектор';
        modalActionBtn.textContent = 'Сохранить изменения';
        const sec = sectors[index];

        // Парсинг имени
        const nameMatch = sec.name.match(/^(.+?)\s+\(([^)]+)\)\s+\(([^)]+)\)(?:\s+\(ФЛ\))?(?:\s+\((\d+)\))?$/);
        
        if (!nameMatch) {
            console.error('Ошибка парсинга имени:', sec.name);
            alert('Ошибка восстановления данных сектора');
            return;
        }

        const jur = nameMatch[1];
        const site = nameMatch[2];
        const typeRussian = nameMatch[3];
        const percent = nameMatch[4] ? parseInt(nameMatch[4]) : 0;
        const hasFL = sec.name.includes('(ФЛ)');

        // Восстанавливаем строку для поля ввода
        sectorDataInput.value = `${sec.id} ${jur} (${site}) (${typeRussian})${hasFL ? ' (ФЛ)' : ''}`;

        // Находим тип сектора
        sectorTypeSelect.value = sec.sectorType || 'In';

        hasCommCheckbox.checked = sec.commission.type !== 'none';
        if (sec.commission.type !== 'none') {
            commissionPercent.value = sec.commission.percent || '';
            if (sec.commission.type === 'fix') {
                document.querySelector('input[name="commissionType"][value="fix"]').checked = true;
                commissionFix.value = sec.commission.fix || '';
                commissionMin.value = '';
            } else {
                document.querySelector('input[name="commissionType"][value="min"]').checked = true;
                commissionMin.value = sec.commission.min || '';
                commissionFix.value = '';
            }
        } else {
            commissionPercent.value = '';
            commissionFix.value = '';
            commissionMin.value = '';
            document.querySelector('input[name="commissionType"][value="fix"]').checked = true;
        }
        updateCommissionFields();
        updateModalForm();

        document.querySelectorAll('.handle-checkbox').forEach(cb => cb.checked = sec.handles.includes(cb.value));
        document.querySelectorAll('.setting-checkbox').forEach(cb => cb.checked = sec.settingsIds.includes(cb.value));

        modal.style.display = 'block';
        modalError.textContent = '';
    };

    // Генерация
    generateBtn.addEventListener('click', () => {
        const login = loginInput.value.trim();
        if (!login) { alert('Пожалуйста, заполните поле "Логин"'); return; }
        const title = requestTitleInput.value;
        let html = title + '<br><br>';

        sectors.forEach(sec => {
            html += `<span class="output-sector-name">Sector ID: ${sec.id} ${sec.name}</span><br>`;
            if (sec.handles.length) {
                const formattedHandles = sec.handles.map(formatHandle).join(', ');
                html += `- включить ручки ${formattedHandles};<br>`;
            }
            sec.settings.forEach(set => html += `- ${set};<br>`);
            html += '<br>';
        });

        html += login + '<br>';
        html += 'Настроить для секторов выше с правами full office (lk personal-area)';

        outputDiv.innerHTML = html;
        copyBtn.style.display = 'inline-block';
    });

    // Копирование
    copyBtn.addEventListener('click', () => {
        const login = loginInput.value.trim();
        if (!login) { alert('Пожалуйста, заполните поле "Логин"'); return; }
        const title = requestTitleInput.value;
        let text = title + '\n\n';

        sectors.forEach(sec => {
            text += '```\n';
            text += `Sector ID: ${sec.id} ${sec.name}\n`;
            text += '```\n';
            if (sec.handles.length) {
                const formattedHandles = sec.handles.map(formatHandle).join(', ');
                text += `- включить ручки ${formattedHandles};\n`;
            }
            sec.settings.forEach(set => text += `- ${set};\n`);
            text += '\n';
        });

        text += login + '\n';
        text += 'Настроить для секторов выше с правами full office (lk personal-area)';

        navigator.clipboard.writeText(text).catch(() => {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
        });
    });

    // LocalStorage
    function saveToLocalStorage() {
        localStorage.setItem('donaSectors', JSON.stringify(sectors));
        localStorage.setItem('donaRequestTitle', requestTitleInput.value);
        localStorage.setItem('donaLogin', loginInput.value);
    }

    function loadFromLocalStorage() {
        const saved = localStorage.getItem('donaSectors');
        if (saved) {
            sectors = JSON.parse(saved);
            renderSectorsList();
        }
        const savedTitle = localStorage.getItem('donaRequestTitle');
        if (savedTitle) requestTitleInput.value = savedTitle;
        const savedLogin = localStorage.getItem('donaLogin');
        if (savedLogin) loginInput.value = savedLogin;
    }

    document.getElementById('dona-requestTitle').addEventListener('change', saveToLocalStorage);
    document.getElementById('dona-login').addEventListener('change', saveToLocalStorage);

    loadFromLocalStorage();
    updateCommissionFields();
    updateModalForm();
});
// Показываем первую вкладку
showTab(0);