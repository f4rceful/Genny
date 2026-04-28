/**
 * Главный контроллер приложения (связующее звено)
 */
document.addEventListener('DOMContentLoaded', async () => {
    const uiElements = {
        amountInput: document.getElementById('amount-input'),
        fromSelect: document.getElementById('from-currency'),
        toSelect: document.getElementById('to-currency'),
        swapBtn: document.getElementById('swap-btn'),
        resultContainer: document.getElementById('result-container'),
        resultValue: document.getElementById('result-value'),
        rateInfo: document.getElementById('rate-info'),
        errorBox: document.getElementById('error-message'),
        statusBar: document.getElementById('status-bar'),
        historyList: document.getElementById('history-list')
    };

    const cache = new CacheManager();
    const converter = new CurrencyConverter();
    const history = new HistoryManager();
    const ui = new UIController(uiElements);

    let currentRates = null;

    const calculate = () => {
        const amountStr = uiElements.amountInput.value.trim().replace(',', '.');
        const from = uiElements.fromSelect.value;
        const to = uiElements.toSelect.value;

        // ФТ-07: Некорректными считаются пустая строка, ноль, отрицательное число
        if (amountStr === '') {
            ui.showError('Некорректная сумма');
            return;
        }

        const amount = parseFloat(amountStr);
        if (isNaN(amount) || amount <= 0) {
            ui.showError('Некорректная сумма');
            return;
        }

        ui.hideError();

        try {
            const result = converter.convert(amount, from, to);
            const pairRate = converter.getPairRate(from, to);

            if (result !== null) {
                ui.displayResult(amount, from, result, to, pairRate);
                const updatedHistory = history.addEntry({ amount, from, result, to });
                ui.renderHistory(updatedHistory);
            }
        } catch (e) {
            ui.showError('Ошибка при расчете');
        }
    };

    const setupListeners = () => {
        uiElements.amountInput.addEventListener('input', calculate);
        uiElements.fromSelect.addEventListener('change', calculate);
        uiElements.toSelect.addEventListener('change', calculate);

        uiElements.swapBtn.addEventListener('click', () => {
            const fromVal = uiElements.fromSelect.value;
            uiElements.fromSelect.value = uiElements.toSelect.value;
            uiElements.toSelect.value = fromVal;
            calculate();
        });
    };

    const init = async () => {
        try {
            const data = await CurrencyAPI.fetchRates();
            currentRates = data.rates;
            cache.save(data.rates, data.timestamp);
            ui.updateStatus('Курсы валют актуальны');
        } catch (error) {
            const cachedData = cache.load();
            if (cachedData && cachedData.rates) {
                const isRecent = cache.isValid();
                
                if (!isRecent) {
                    ui.disableApp('Актуальные данные временно недоступны');
                    return;
                }

                currentRates = cachedData.rates;
                const date = new Date(cachedData.timestamp);
                const dateStr = `${String(date.getDate()).padStart(2, '0')}.${String(date.getMonth() + 1).padStart(2, '0')}.${date.getFullYear()}`;
                
                ui.updateStatus(`Курс от ${dateStr}. Актуальные данные временно недоступны`, true);
            } else {
                ui.disableApp('Актуальные данные временно недоступны');
                return;
            }
        }

        converter.setRates(currentRates);
        ui.populateSelects(currentRates);
        ui.renderHistory(history.getAll());
        setupListeners();
    };

    init();
});