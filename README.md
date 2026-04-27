# Genny — Автономная команда разработки

Генератор веб-приложений на основе LLM-агентов. Принимает бизнес-требования и бизнес-процесс в формате Markdown — выдаёт готовое веб-приложение с полным комплектом документации.

## Как это работает

```
БТ + БП + Features (опционально)
  → Агент 1: Use-cases          → docs/use-cases.md
  → Агент 2: Аналитик           → docs/non-functional-req.md
                                 → docs/functional-req.md
  → Агент 3: Архитектор         → docs/architecture.json
  → Агент 4: Кодогенератор      → src/index.html, src/css/, src/js/
                                 → README.md
  → Агент 5: Тестировщик        → tests/test_functional.py
```

---

## Установка

**Требования:** Python 3.11+, API-ключ OpenRouter

```bash
git clone <repo>
cd Genny

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Создайте файл `.env` в корне проекта:

```
OPENROUTER_API_KEY=sk-or-...
```

---

## Запуск сервера

```bash
source .venv/bin/activate
uvicorn main:app --reload
```

Сервер запустится на `http://localhost:8000`.

---

## Использование

### Вариант 1 — через тестовый скрипт (рекомендуется для демо)

Положите входные файлы в папку `test_input/`:

```
test_input/
├── bt.md        # Бизнес-требования
├── bp.md        # Бизнес-процесс
└── features.md  # Характеристики (опционально)
```

Запустите:

```bash
python test_run.py
```

Скрипт отправит запрос, будет опрашивать статус каждые 5 секунд и выведет список сгенерированных файлов. Ждёт появления всех ключевых артефактов (максимум 3 минуты).

### Вариант 2 — через curl

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d "{
    \"bt\": \"$(cat test_input/bt.md)\",
    \"bp\": \"$(cat test_input/bp.md)\",
    \"features\": \"$(cat test_input/features.md)\"
  }"
```

Ответ:
```json
{"run_id": "uuid", "status": "started", "artifacts": []}
```

### Проверка статуса

```bash
curl http://localhost:8000/status/<run_id>
```

Ответ когда готово:
```json
{
  "run_id": "...",
  "status": "done",
  "files": [
    "README.md",
    "docs/architecture.json",
    "docs/functional-req.md",
    "docs/non-functional-req.md",
    "docs/use-cases.md",
    "src/css/style.css",
    "src/index.html",
    "src/js/app.js",
    "src/js/calculator.js",
    "tests/test_functional.py"
  ]
}
```

### Скачать результат архивом

```bash
curl http://localhost:8000/download/<run_id> -o result.zip
```

---

## Структура вывода

```
output/<run_id>/
├── docs/
│   ├── use-cases.md           # Юз-кейсы со ссылками на БТ
│   ├── non-functional-req.md  # Нефункциональные требования
│   ├── functional-req.md      # Функциональные требования
│   └── architecture.json      # Архитектурный план (файлы, классы, зависимости)
├── src/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── <логика>.js
│       └── app.js
├── tests/
│   └── test_functional.py
└── README.md                  # Инструкция по запуску приложения
```

Сгенерированное приложение открывается без сервера: просто откройте `output/<run_id>/src/index.html` в браузере.

---

## Запуск тестов сгенерированного приложения

```bash
cd output/<run_id>
pip install pytest
pytest tests/
```

---

## Тестовые задания

Все три задания организаторов готовы к запуску:

| Папка | Задание | Сложность |
| ----- | ------- | --------- |
| `test_input/` | **A — Веб-калькулятор** | Простое |
| `test_input_b/` | **B — Таск-трекер** | Среднее |
| `test_input_c/` | **C — Конвертер валют с API** | Сложное |

Запуск конкретного задания:

```bash
python test_run.py                  # Задание A (по умолчанию)
python test_run.py test_input_b     # Задание B
python test_run.py test_input_c     # Задание C
```

Для своего задания создайте аналогичную папку с файлами:

| Файл | Содержимое |
|------|-----------|
| `bt.md` | Таблица бизнес-требований с ID (БТ-01, БТ-02...) и признаком обязательности |
| `bp.md` | Описание бизнес-процесса: актор, основные и альтернативные потоки |
| `features.md` | Произвольный список пожеланий: тема, язык, название, ограничения |

---

## Стек

| Компонент | Технология |
|-----------|-----------|
| Генератор | Python 3.11, FastAPI |
| LLM-провайдер | OpenRouter (`qwen/qwen3-235b-a22b`) |
| Генерируемое приложение | Vanilla HTML + CSS + JS |
| Тесты | pytest |
