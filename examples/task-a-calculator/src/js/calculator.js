class Calculator {
    constructor() {
        this.reset();
    }

    reset() {
        this.firstOperand = null;
        this.operator = null;
        this.currentInput = '0';
        this.waitForSecondOperand = false;
        this.errorFlag = null;
        this.result = null;
    }

    inputDigit(digit) {
        if (this.errorFlag) this.reset();

        if (this.waitForSecondOperand) {
            this.currentInput = digit === '.' ? '0.' : digit;
            this.waitForSecondOperand = false;
        } else {
            if (digit === '.' && this.currentInput.includes('.')) return;
            this.currentInput = this.currentInput === '0' && digit !== '.' ? digit : this.currentInput + digit;
        }
    }

    backspace() {
        if (this.errorFlag) {
            this.reset();
            return;
        }
        if (this.currentInput.length > 1) {
            this.currentInput = this.currentInput.slice(0, -1);
        } else {
            this.currentInput = '0';
        }
    }

    setOperator(nextOperator) {
        if (this.errorFlag) return;

        const inputValue = parseFloat(this.currentInput);

        if (this.operator && this.waitForSecondOperand) {
            this.operator = nextOperator;
            return;
        }

        if (this.firstOperand === null) {
            if (!isNaN(inputValue)) {
                this.firstOperand = inputValue;
            }
        } else if (this.operator) {
            const operationData = this.compute();
            if (this.errorFlag) return;
            if (operationData) {
                this.firstOperand = operationData.res;
                this.currentInput = String(operationData.res);
            }
        }

        this.waitForSecondOperand = true;
        this.operator = nextOperator;
    }

    compute() {
        if (this.operator === null || this.waitForSecondOperand) return null;

        const secondOperand = parseFloat(this.currentInput);
        const firstOperand = this.firstOperand;
        let calculationResult = 0;

        if (isNaN(firstOperand) || isNaN(secondOperand)) {
            return null;
        }

        switch (this.operator) {
            case '+':
                calculationResult = firstOperand + secondOperand;
                break;
            case '-':
                calculationResult = firstOperand - secondOperand;
                break;
            case '×':
                calculationResult = firstOperand * secondOperand;
                break;
            case '÷':
                if (secondOperand === 0) {
                    this.errorFlag = 'division_by_zero';
                    return null;
                }
                calculationResult = firstOperand / secondOperand;
                break;
            default:
                return null;
        }

        this.result = parseFloat(calculationResult.toFixed(8));
        
        const operationData = {
            op1: firstOperand,
            op: this.operator,
            op2: secondOperand,
            res: this.result
        };

        this.firstOperand = this.result;
        this.operator = null;
        this.waitForSecondOperand = true;
        this.currentInput = String(this.result);

        return operationData;
    }

    getDisplayValue() {
        if (this.errorFlag === 'division_by_zero') return 'Ошибка: деление на ноль';
        // Очищаем результат от лишних нулей после запятой, преобразуя строку обратно в число через parseFloat
        if (this.currentInput.includes('.')) {
            return String(parseFloat(this.currentInput));
        }
        return this.currentInput;
    }

    getPrevStepDisplay() {
        if (this.firstOperand !== null && this.operator) {
            // Форматируем число, чтобы избежать .0 в выводе
            const formattedOp1 = parseFloat(this.firstOperand.toFixed(8));
            return `${formattedOp1} ${this.operator}`;
        }
        return '';
    }
}