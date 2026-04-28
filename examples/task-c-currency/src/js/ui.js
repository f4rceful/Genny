/**
 * Контроллер UI компонентов (DOM-манипуляции)
 */
class UIController {
    constructor(elements) {
        this.els = elements;
        this.requiredCurrencies = ['USD', 'EUR', 'RUB', 'GBP', 'JPY', 'CNY', 'TRY', 'KZT', 'BYN', 'GEL'];
    }

    populateSelects(rates) {
        const availableCurrencies = Object.keys(rates);
        const sorted = [...new Set([...this.requiredCurrencies, ...availableCurrencies])]
            .filter(code => rates[code]);

        const fragmentFrom = document.createDocumentFragment();
        const fragmentTo = document.createDocumentFragment();

        sorted.forEach(code => {
            const opt1 = document.createElement('option');
            opt1.value = code;
            opt1.textContent = code;
            fragmentFrom.appendChild(opt1);

            const opt2 = document.createElement('option');
            opt2.value = code;
            opt2.textContent = code;
            fragmentTo.appendChild(opt2);
        });

        this.els.fromSelect.innerHTML = '';
        this.els.toSelect.innerHTML = '';
        this.els.fromSelect.appendChild(fragmentFrom);
        this.els.toSelect.appendChild(fragmentTo);

        this.els.fromSelect.value = 'USD';
        this.els.toSelect.value = 'RUB';
    }

    showError(msg) {
        this.els.errorBox.textContent = msg;
        this.els.errorBox.classList.remove('hidden');
        this.els.amountInput.classList.add('error');
        this.els.resultContainer.classList.add('hidden');
    }

    hideError() {
        this.els.errorBox.classList.add('hidden');
        this.els.amountInput.classList.remove('error');
    }

    updateStatus(message, isWarning = false) {
        this.els.statusBar.textContent = message;
        this.els.statusBar.style.color = isWarning ? 'var(--error-color)' : 'var(--text-secondary)';
    }

    displayResult(amount, from, result, to, pairRate) {
        this.els.resultValue.textContent = `${amount} ${from} = ${result.toLocaleString(undefined, { maximumFractionDigits: 4 })} ${to}`;
        this.els.rateInfo.textContent = `Курс: 1 ${from} = ${pairRate.toFixed(4)} ${to}`;
        this.els.resultContainer.classList.remove('hidden');
    }

    renderHistory(history) {
        this.els.historyList.innerHTML = '';
        const fragment = document.createDocumentFragment();
        
        history.forEach(item => {
            const li = document.createElement('li');
            li.className = 'history-item';
            
            const info = document.createElement('span');
            info.textContent = `${item.amount} ${item.from} → ${item.result} ${item.to}`;
            
            const time = document.createElement('small');
            time.style.color = 'var(--text-secondary)';
            time.textContent = new Date(item.date).toLocaleTimeString();
            
            li.appendChild(info);
            li.appendChild(time);
            fragment.appendChild(li);
        });
        
        this.els.historyList.appendChild(fragment);
    }

    disableApp(msg) {
        this.updateStatus(msg, true);
        this.els.amountInput.disabled = true;
        this.els.fromSelect.disabled = true;
        this.els.toSelect.disabled = true;
        this.els.swapBtn.disabled = true;
        this.els.resultContainer.classList.add('hidden');
    }
}