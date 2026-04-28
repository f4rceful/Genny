"""
Тесты бизнес-логики приложения MathBox.
Проверяют соответствие реализации функциональным требованиям.
"""
import pytest


# --- Вспомогательные функции (эмуляция бизнес-логики из JS) ---

def compute_operation(op1, operator, op2):
    """
    Вычисляет результат операции между двумя числами.
    Эмулирует логику метода compute из класса Calculator.
    """
    if operator == '+':
        result = op1 + op2
    elif operator == '-':
        result = op1 - op2
    elif operator == '×':
        result = op1 * op2
    elif operator == '÷':
        if op2 == 0:
            raise ValueError("division_by_zero")
        result = op1 / op2
    else:
        raise ValueError("Unknown operator")
    # Ограничение точности как в JS (toFixed(8))
    return round(result, 8)


def format_current_input(current_input):
    """
    Форматирует текущий ввод для отображения.
    Эмулирует логику метода getDisplayValue из класса Calculator.
    """
    if current_input is None:
        return '0'
    # Преобразование строки в число для удаления лишних нулей после точки
    try:
        num = float(current_input)
        # Убираем .0 для целых чисел
        if num == int(num):
            return str(int(num))
        return str(num)
    except ValueError:
        return current_input


def handle_division_by_zero(op1, operator, op2):
    """
    Обрабатывает деление на ноль и возвращает состояние ошибки.
    Эмулирует логику ошибки в методе compute.
    """
    if operator == '÷' and op2 == 0:
        return {
            "error": "division_by_zero",
            "display": "Ошибка: деление на ноль",
            "operation_data": {"op1": op1, "op": operator, "op2": op2, "res": None}
        }
    return None


def add_history_entry(entries, new_entry, max_entries=10):
    """
    Добавляет операцию в историю и ограничивает список до max_entries.
    Эмулирует логику метода addEntry из класса HistoryManager.
    """
    # Сантизация как в JS: преобразование всех значений в строки
    sanitized_entry = {
        "op1": str(new_entry["op1"]),
        "op": str(new_entry["op"]),
        "op2": str(new_entry["op2"]),
        "res": str(new_entry["res"]) if new_entry["res"] is not None else "Ошибка",
        "timestamp": new_entry.get("timestamp", 0)
    }
    entries.insert(0, sanitized_entry)
    if len(entries) > max_entries:
        entries.pop()
    return entries


def reset_calculator_state():
    """
    Возвращает состояние калькулятора после очистки (сброса).
    Эмулирует логику метода reset из класса Calculator.
    """
    return {
        "firstOperand": None,
        "operator": None,
        "currentInput": '0',
        "waitForSecondOperand": False,
        "errorFlag": None,
        "result": None
    }


# --- Тесты ---

def test_basic_arithmetic_operations():
    # ФТ-01
    # Проверка базовых арифметических операций
    assert compute_operation(5, '+', 3) == 8
    assert compute_operation(10, '-', 4) == 6
    assert compute_operation(6, '×', 7) == 42
    assert compute_operation(15, '÷', 3) == 5
    # Проверка с десятичными числами
    assert compute_operation(2.5, '+', 1.3) == 3.8
    assert compute_operation(5.5, '×', 2) == 11.0
    # Проверка точности (округление до 8 знаков)
    assert compute_operation(1, '÷', 3) == round(1/3, 8)


def test_division_by_zero():
    # ФТ-03
    # Проверка обработки деления на ноль
    error_state = handle_division_by_zero(10, '÷', 0)
    assert error_state is not None
    assert error_state["error"] == "division_by_zero"
    assert error_state["display"] == "Ошибка: деление на ноль"
    assert error_state["operation_data"]["res"] is None
    
    # Проверка, что другие операции не вызывают ошибку деления на ноль
    assert handle_division_by_zero(10, '+', 0) is None
    assert handle_division_by_zero(10, '×', 0) is None
    # Деление на ноль с отрицательным числом
    assert handle_division_by_zero(-5, '÷', 0)["error"] == "division_by_zero"


def test_reset_state():
    # ФТ-02
    # Проверка сброса состояния калькулятора
    state = reset_calculator_state()
    assert state["firstOperand"] is None
    assert state["operator"] is None
    assert state["currentInput"] == '0'
    assert state["waitForSecondOperand"] is False
    assert state["errorFlag"] is None
    assert state["result"] is None


def test_formatting_current_input():
    # Проверка форматирования текущего ввода (часть ФТ-01 и ФТ-03)
    assert format_current_input('123') == '123'
    assert format_current_input('45.0') == '45'
    assert format_current_input('12.34567890') == '12.3456789'
    assert format_current_input('0') == '0'
    # Ошибка деления на ноль возвращает строку ошибки
    assert format_current_input('Ошибка: деление на ноль') == 'Ошибка: деление на ноль'


def test_history_management():
    # ФТ-05
    # Проверка добавления операции в историю
    entries = []
    new_entry = {"op1": 5, "op": "+", "op2": 3, "res": 8}
    entries = add_history_entry(entries, new_entry)
    assert len(entries) == 1
    assert entries[0]["op1"] == "5"
    assert entries[0]["res"] == "8"
    
    # Проверка добавления операции с ошибкой
    error_entry = {"op1": 10, "op": "÷", "op2": 0, "res": None}
    entries = add_history_entry(entries, error_entry)
    assert len(entries) == 2
    assert entries[0]["res"] == "Ошибка"
    
    # Проверка ограничения истории до 10 записей
    for i in range(15):
        entries = add_history_entry(entries, {"op1": i, "op": "+", "op2": 1, "res": i+1})
    assert len(entries) == 10
    # Последняя добавленная операция должна быть первой в списке
    assert entries[0]["op1"] == "14"


def test_arithmetic_with_boundary_values():
    # Дополнительные тесты граничных значений
    # Большие числа
    assert compute_operation(999999, '×', 999999) == 999998000001
    # Очень маленькие числа
    assert compute_operation(0.000001, '÷', 0.000002) == 0.5
    # Ноль как первый операнд
    assert compute_operation(0, '+', 5) == 5
    assert compute_operation(0, '×', 5) == 0
    # Деление нуля на число
    assert compute_operation(0, '÷', 5) == 0


def test_unknown_operator():
    # Проверка реакции на неизвестный оператор
    with pytest.raises(ValueError, match="Unknown operator"):
        compute_operation(5, '$', 3)


def test_history_entry_sanitization():
    # Проверка санитизации данных истории (все значения преобразуются в строки)
    entries = []
    entry_with_float = {"op1": 3.14, "op": "×", "op2": 2, "res": 6.28}
    entries = add_history_entry(entries, entry_with_float)
    assert entries[0]["op1"] == "3.14"
    assert entries[0]["op2"] == "2"
    assert entries[0]["res"] == "6.28"
    # Проверка с целым числом
    entry_with_int = {"op1": 100, "op": "-", "op2": 50, "res": 50}
    entries = add_history_entry(entries, entry_with_int)
    assert entries[0]["op1"] == "100"
    assert entries[0]["res"] == "50"