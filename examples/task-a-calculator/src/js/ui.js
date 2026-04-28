class UIManager {
    constructor() {
        this.displayMain = document.getElementById('display-main');
        this.displayPrev = document.getElementById('display-prev');
        this.historyList = document.getElementById('history-list');
        this.copyBtn = document.getElementById('copy-btn');
    }

    updateDisplay(value, prevValue = '', isError = false) {
        this.displayMain.textContent = value;
        this.displayPrev.textContent = prevValue;

        if (isError) {
            this.displayMain.classList.add('error');
            this.copyBtn.disabled = true;
        } else {
            this.displayMain.classList.remove('error');
            this.copyBtn.disabled = (value === '0' || value === '');
        }
    }

    updateHistoryPanel(entries) {
        if (!this.historyList) return;

        if (entries.length === 0) {
            this.historyList.innerHTML = '<li class="history-empty">История операций пуста</li>';
            return;
        }

        // Очищаем список и создаем элементы безопасно через textContent
        this.historyList.innerHTML = '';
        entries.forEach(item => {
            const li = document.createElement('li');
            li.className = 'history-item';
            
            const expSpan = document.createElement('span');
            expSpan.className = 'exp';
            expSpan.textContent = `${item.op1} ${item.op} ${item.op2} =`;
            
            const resSpan = document.createElement('span');
            resSpan.className = 'res';
            resSpan.textContent = item.res;

            li.appendChild(expSpan);
            li.appendChild(resSpan);
            this.historyList.appendChild(li);
        });
    }

    async copyResultToClipboard() {
        const text = this.displayMain.textContent;
        if (text && !this.displayMain.classList.contains('error')) {
            try {
                await navigator.clipboard.writeText(text);
                const originalContent = this.copyBtn.textContent;
                this.copyBtn.textContent = '✅';
                setTimeout(() => {
                    this.copyBtn.textContent = originalContent;
                }, 1000);
            } catch (err) {
                console.error('Не удалось скопировать', err);
            }
        }
    }
}