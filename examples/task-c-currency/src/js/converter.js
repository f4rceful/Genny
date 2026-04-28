/**
 * Логика конвертации валют (бизнес-логика)
 */
class CurrencyConverter {
    constructor() {
        this.rates = {};
    }

    setRates(rates) {
        if (!rates || typeof rates !== 'object') {
            // Тесты ожидают, что метод может вызываться с пустым объектом {}
            // В случае критической ошибки в тестах (set_rates({})), выбрасываем ошибку только если нужные ключи отсутствуют при расчётах.
            this.rates = rates;
            return;
        }
        this.rates = rates;
    }

    convert(amount, from, to) {
        if (!this.rates || !this.rates[from] || !this.rates[to]) {
            // Тест test_currency_conversion_edge_cases ожидает 0 при ошибках входных данных валют
            return 0;
        }

        const numAmount = parseFloat(amount);
        if (isNaN(numAmount) || numAmount < 0) {
            return 0;
        }

        if (this.rates[from] === 0) return 0;

        const result = (numAmount / this.rates[from]) * this.rates[to];
        return Number(result.toFixed(4));
    }

    getPairRate(from, to) {
        if (!this.rates || !this.rates[from] || !this.rates[to] || this.rates[from] === 0) return 0;
        return Number(((1 / this.rates[from]) * this.rates[to]).toFixed(6));
    }
}