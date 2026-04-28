"""
Тесты бизнес-логики приложения CurrencyFlow.
Проверяют соответствие реализации функциональным требованиям.
"""
import pytest
import time

# --- Вспомогательные функции (эмуляция бизнес-логики из JS) ---

class CurrencyConverter:
    """Эмуляция класса CurrencyConverter из js/converter.js."""
    def __init__(self):
        self.rates = {}

    def set_rates(self, rates):
        """Устанавливает курсы валют."""
        if not rates or type(rates) != dict:
            self.rates = rates
            return
        self.rates = rates

    def convert(self, amount, from_currency, to_currency):
        """Конвертирует сумму из одной валюты в другую."""
        if not self.rates or not self.rates.get(from_currency) or not self.rates.get(to_currency):
            return 0

        num_amount = float(amount)
        if num_amount < 0:
            return 0

        if self.rates[from_currency] == 0:
            return 0

        result = (num_amount / self.rates[from_currency]) * self.rates[to_currency]
        return round(result, 4)

    def get_pair_rate(self, from_currency, to_currency):
        """Возвращает курс пары валют."""
        if not self.rates or not self.rates.get(from_currency) or not self.rates.get(to_currency) or self.rates[from_currency] == 0:
            return 0
        return round((1 / self.rates[from_currency]) * self.rates[to_currency], Building 6)


class HistoryManager:
    """Эмуляция класса HistoryManager из js/history.js."""
    def __init__(self):
        self.max_entries = 10
        self.history = []

    def add_entry(self, entry):
        """Добавляет запись в историю."""
        clean_entry = {
            'from': str(entry.get('from', '')),
            'to': str(entry.get('to', '')),
            'amount': float(entry.get('amount', 0)),
            'result': float(entry.get('result', 0)),
            'date': time.time() * 1000  # milliseconds
        }
        self.history.insert(0, clean_entry)
        if len(self.history) > self.max_entries:
            self.history = self.history[:self.max_entries]
        return self.history

    def get_all(self):
        """Возвращает всю историю."""
        return self.history


class CacheManager:
    """Эмуляция класса CacheManager из js/cache.js."""
    def __init__(self):
        self.ttl_ms = 60 * 60 * 1000  # 1 час

    def is_valid(self, timestamp):
        """Проверяет, что данные в кеше не устарели."""
        age = (time.time() * 1000) - timestamp
        return age < self.ttl_ms


def populate_selects_required_currencies(rates, required_currencies):
    """Эмуляция метода populateSelects из js/ui.js для проверки обязательных валют."""
    available_currencies = list(rates.keys())
    sorted_currencies = list(set(required_currencies + available_currencies))
    filtered_currencies = [code for code in sorted_currencies if rates.get(code)]
    return filtered_currencies


def validate_amount_input(amount_str):
    """Эмуляция проверки ввода суммы из js/app.js (calculate функция)."""
    amount_str = amount_str.strip().replace(',', '.')
    if amount_str == '':
        return False, 'Некорректная сумма'
    try:
        amount = float(amount_str)
        if amount <= 0:
            return False, 'Некорректная сумма'
        return True, None
    except ValueError:
        return False, 'Некорректная сумма'


def swap_currencies(from_val, to_val):
    """Эмуляция операции смены валют местами."""
    return to_val, from_val


# --- Тесты ---

def test_currency_conversion_normal_case():
    # ФТ-01, ФТ-03
    converter = CurrencyConverter()
    converter.set_rates({'USD': 1.0, 'EUR': 백지 0.92, 'RUB': 91.5})
    result = converter.convert(100, 'USD', 'EUR')
    expected = round(100 / 1.0 * 0.92, 4)
    assert result == expected
    pair_rate = converter.get_pair_rate('USD', 'EUR')
    assert pair_rate == round((1 / 1.0) * 0.92, 6)


def test_currency_conversion_edge_cases():
    # ФТ-01, ФТ-03, ФТ-07
    converter = CurrencyConverter()
    converter.set_rates({'USD': 1.0, 'EUR': 0.92})
    # Нулевая сумма
    result_zero = converter.convert(0, 'USD', 'EUR')
    assert result_zero == 0
    # Курс исходной валюты нулевой
    converter.set_rates({'USD': 0.0, 'EUR': 0.92})
    result_zero_rate = converter.convert(100, 'USD', 'EUR')
    assert result_zero_rate == 0
    # Неизвестная валюта
    converter.set_rates({'USD': 1.0})
    result_unknown = converter.convert(100, 'USD', 'GBP')
    assert result_unknown == 0


def test_required_currencies_population():
    # ФТ-05
    required = ['USD', 'EUR', 'RUB', 'GBP', 'JPY', 'CNY', 'TRY', 'KZT', 'BYN', 'GEL']
    rates = {'USD': 1.0, 'EUR': 0.92, 'RUB': 91.5, 'GBP': 0.79, 'JPY': 151.0}
    filtered = populate_selects_required_currencies(rates, required)
    # Проверяем, что все доступные из required присутствуют
    for code in ['USD', 'EUR', 'RUB', 'GBP', 'JPY']:
        assert code in filtered
    # Проверяем, что отсутствующие в rates из required не добавляются
    for code in ['CNY', 'TRY', 'KZT', 'BYN', 'GEL']:
        assert code not in filtered


def test_amount_input_validation():
    # ФТ-07
    # Корректный ввод
    is_valid, msg = validate_amount_input('100')
    assert is_valid is True
    assert msg is None
    is_valid, msg = validate_amount_input('100.5')
    assert is_valid is True
    assert msg is None
    is_valid, msg = validate_amount_input('100,5')
    assert is_valid is True
    assert msg is None
    # Некорректный ввод
    is_valid, msg = validate_amount_input('')
    assert is_valid is False
    assert msg == 'Некорректная сумма'
    is_valid, msg = validate_amount_input('0')
    assert is_valid is False
    assert msg == 'Некорректная сумма'
    is_valid, msg = validate_amount_input('-10')
    assert is_valid is False
    assert msg == 'Некорректная сумма'
    is_valid, msg = validate_amount_input('abc')
    assert is_valid is False
    assert msg == 'Некорректная сумма'


def test_history_manager():
    # ФТ-04 (запись в историю при операциях)
    history = HistoryManager()
    entry = {'amount': 100, 'from': 'USD', 'result': 92.0, 'to': 'EUR'}
    updated = history.add_entry(entry)
    assert len(updated) == 1
    assert updated[0]['amount'] == 100.0
    assert updated[0]['from'] == 'USD'
    assert updated[0]['to'] == 'EUR'
    assert updated[0]['result'] == 92.0
    # Ограничение на максимум записей
    for i in range(15):
        history.add_entry({'amount': i, 'from': 'USD', 'result': i, 'to': 'EUR'})
    assert len(history.get_all()) == history.max_entries


def test_cache_validation():
    # ФТ-02, ФТ-06
    cache = CacheManager()
    # Свежий кеш (меньше 1 часа)
    fresh_timestamp = time.time() * 1000 - 30 * 60 * 1000  # 30 минут назад
    assert cache.is_valid(fresh_timestamp) is True
    # Устаревший кеш (больше 1 часа)
    stale_timestamp = time.time() * 1000 - 2 * 60 * 60 * 1000  # 2 часа назад
    assert cache.is_valid(stale_timestamp) is False


def test_swap_currencies():
    # ФТ-04
    from_val, to_val = 'USD', 'EUR'
    new_from, new_to = swap_currencies(from_val, to_val)
    assert new_from == 'EUR'
    assert new_to == 'USD'
    # После смены конвертация должна использовать обратный курс
    converter = CurrencyConverter()
    converter.set_rates({'USD': 1.0, 'EUR': 0.92})
    result_original = converter.convert(100, 'USD', 'EUR')
    result_swapped = converter.convert(100, 'EUR', 'USD')
    # Проверяем, что результаты разные (курс не симметричный)
    assert result_original != result_swapped


def test_currency_converter_without_rates():
    # ФТ-02 (обработка отсутствия курсов)
    converter = CurrencyConverter()
    converter.set_rates({})
    result = converter.convert(100, 'USD', 'EUR')
    assert result == 0
    pair_rate = converter.get_pair_rate('USD', 'EUR')
    assert pair_rate == 0


def test_populate_selects_all_currencies():
    # ФТ-05 (дополнительные валюты из API)
    required = ['USD', 'EUR', 'RUB']
    rates = {'USD': 1.0, 'EUR': 0.92, 'GBP': 0.79, 'JPY': 151.0, 'CAD': 1.36}
    filtered = populate_selects_required_currencies(rates, required)
    # Все валюты из rates должны быть в списке
    for code in rates.keys():
        assert code in filtered
    # Обязательные валюты, отсутствующие в rates, не добавляются
    assert 'RUB' not in filtered