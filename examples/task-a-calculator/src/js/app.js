document.addEventListener('DOMContentLoaded', () => {
    const calc = new Calculator();
    const history = new HistoryManager();
    const ui = new UIManager();

    ui.updateHistoryPanel(history.getEntries());

    const keypad = document.getElementById('keypad');
    if (keypad) {
        keypad.addEventListener('click', (e) => {
            const target = e.target.closest('.btn');
            if (!target) return;

            const digit = target.dataset.digit;
            const op = target.dataset.op;
            const action = target.dataset.action;

            if (digit !== undefined) {
                calc.inputDigit(digit);
            } else if (op !== undefined) {
                calc.setOperator(op);
            } else if (action === 'compute') {
                const resultData = calc.compute();
                if (calc.errorFlag) {
                    history.addEntry({
                        op1: calc.firstOperand,
                        op: calc.operator,
                        op2: 0,
                        res: null
                    });
                } else if (resultData) {
                    history.addEntry(resultData);
                }
                ui.updateHistoryPanel(history.getEntries());
            } else if (action === 'clear') {
                calc.reset();
            } else if (action === 'backspace') {
                calc.backspace();
            }

            ui.updateDisplay(
                calc.getDisplayValue(), 
                calc.getPrevStepDisplay(), 
                !!calc.errorFlag
            );
        });
    }

    const copyBtn = document.getElementById('copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            ui.copyResultToClipboard();
        });
    }

    document.addEventListener('keydown', (e) => {
        const keyMap = {
            'Enter': '[data-action="compute"]',
            '=': '[data-action="compute"]',
            'Escape': '[data-action="clear"]',
            'Backspace': '[data-action="backspace"]',
            '/': '[data-op="÷"]',
            '*': '[data-op="×"]',
            '+': '[data-op="+"]',
            '-': '[data-op="-"]',
            '.': '[data-digit="."]',
            ',': '[data-digit="."]'
        };

        if (keyMap[e.key]) {
            e.preventDefault();
            const btn = document.querySelector(keyMap[e.key]);
            if (btn) btn.click();
        } else if (/[0-9]/.test(e.key)) {
            const btn = document.querySelector(`[data-digit="${e.key}"]`);
            if (btn) btn.click();
        }
    });
});