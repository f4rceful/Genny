/**
 * Клиент для работы с внешним API валют
 */
const CurrencyAPI = {
    URL: 'https://open.er-api.com/v6/latest/USD',
    TIMEOUT: 5000,

    async fetchRates() {
        const controller = new AbortController();
        const id = setTimeout(() => controller.abort(), this.TIMEOUT);

        try {
            const response = await fetch(this.URL, {
                signal: controller.signal
            });
            
            clearTimeout(id);

            if (!response.ok) {
                throw new Error('Ошибка сети при запросе к API');
            }

            const data = await response.json();
            
            if (data && data.result === 'success' && data.rates) {
                return {
                    rates: data.rates,
                    timestamp: Date.now()
                };
            } else {
                throw new Error('Ошибка в формате ответа API');
            }
        } catch (error) {
            clearTimeout(id);
            throw error;
        }
    }
};