# Genny

Генератор веб-приложений на основе LLM-агентов. Принимает бизнес-требования и бизнес-процесс в формате Markdown — выдаёт готовое веб-приложение с полным комплектом документации.

## Как это работает

```
БТ + БП + Features (опционально)
  → Агент 1: Use-cases      → docs/use-cases.md
  → Агент 2: Аналитик       → docs/non-functional-req.md
                             → docs/functional-req.md
  → Агент 3: Архитектор     → docs/architecture.json
  → Агент 4: Кодогенератор  → src/  +  README.md
  → Агент 5: Тестировщик    → tests/test_functional.py
  → Цикл самопроверки       → fix loop (до 3 попыток)
```

---

## Установка

**Требования:** Python 3.11+, Node.js 18+, API-ключ [OpenRouter](https://openrouter.ai/keys)

```bash
git clone <repo>
cd Genny

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Создайте `.env` в корне (минимальная конфигурация):

```env
OPENROUTER_API_KEY=

# Модель по умолчанию (если не задана модель агента)
MODEL_DEFAULT=google/gemini-3-flash-preview
# Резервная модель на случай ошибки основной
MODEL_FALLBACK=deepseek/deepseek-v4-flash

# Модели для каждого агента
MODEL_USE_CASES=deepseek/deepseek-v4-flash
MODEL_ANALYST=deepseek/deepseek-v4-flash
MODEL_ARCHITECT=deepseek/deepseek-v4-flash
MODEL_CODER=google/gemini-3-flash-preview
MODEL_TESTER=google/gemini-3-flash-preview
MODEL_FIXER=google/gemini-3-flash-preview
MODEL_PATCHER=google/gemini-3-flash-preview

# Максимум попыток автоисправления кода (тесты упали → fix → retry)
MAX_FIX_ATTEMPTS=3

# Настройки тестового скрипта (test_run.py)
GENERATOR_BASE_URL=http://localhost:8000
POLL_INTERVAL=5

```

Полный список переменных — см. `.env` (модели для каждого агента, параметры запуска).

---

## Запуск

### Бэкенд

```bash
source .venv/bin/activate
uvicorn main:app --reload
```

Сервер запустится на `http://localhost:8000`.

### Веб-интерфейс (опционально)

```bash
cd frontend
npm install
npm run dev
```

Откройте `http://localhost:3000` — веб-интерфейс для запуска генерации, просмотра файлов и preview сгенерированного приложения.

---

## Использование

### Через веб-интерфейс

1. Откройте `http://localhost:3000`
2. Вставьте или загрузите файлы БТ, БП и Features (опционально)
3. Нажмите «Начать разработку»
4. Следите за прогрессом в логе, просматривайте файлы и preview во вкладках справа

### Через тестовый скрипт

```bash
python test_run.py                  # Задание A (по умолчанию)
python test_run.py test_input_b     # Задание B
python test_run.py test_input_c     # Задание C
```

Скрипт отправляет запрос, опрашивает статус и выводит список файлов. Останавливается автоматически при завершении пайплайна или по Ctrl+C.

### Через curl

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d "{\"bt\": \"$(cat test_input/bt.md)\", \"bp\": \"$(cat test_input/bp.md)\"}"
```

---

## API

| Метод | Эндпоинт | Описание |
| ----- | -------- | -------- |
| POST | `/generate` | Запустить пайплайн, вернёт `run_id` |
| GET | `/status/{run_id}` | Статус, текущий шаг, список файлов |
| GET | `/file/{run_id}/{path}` | Содержимое конкретного файла |
| POST | `/patch/{run_id}` | Режим доработки — точечные правки по инструкции |
| POST | `/refine/{run_id}` | Повторный запуск fix loop |
| GET | `/download/{run_id}` | Скачать все артефакты zip-архивом |

### Режим доработки

```bash
curl -X POST http://localhost:8000/patch/<run_id> \
  -H "Content-Type: application/json" \
  -d '{"instruction": "добавь валидацию email"}'
```

Обновляет и код (`src/`), и документацию (`docs/`).

---

## Структура вывода

```
output/<run_id>/
├── docs/
│   ├── use-cases.md           # Юз-кейсы (UC-XX → БТ-XX)
│   ├── non-functional-req.md  # НФТ с категориями
│   ├── functional-req.md      # ФТ (→ БТ-XX + UC-XX)
│   └── architecture.json      # Архитектурный план
├── src/
│   ├── index.html
│   ├── css/style.css
│   └── js/...
├── tests/
│   └── test_functional.py     # pytest, 1 тест на каждое ФТ
└── README.md                  # Инструкция по запуску приложения
```

Сгенерированное приложение открывается без сервера: `output/<run_id>/src/index.html`.

---

## Тестовые задания

| Папка | Задание | Сложность |
| ----- | ------- | --------- |
| `test_input/` | **A — Веб-калькулятор** | Простое |
| `test_input_b/` | **B — Таск-трекер** | Среднее |
| `test_input_c/` | **C — Конвертер валют с API** | Сложное |

Для своего задания создайте папку с тремя файлами:

| Файл | Содержимое |
| ---- | ---------- |
| `bt.md` | Таблица бизнес-требований с ID (БТ-01...) и признаком обязательности |
| `bp.md` | Описание бизнес-процесса: актор, основные и альтернативные потоки |
| `features.md` | Произвольные пожелания: тема, язык, название, ограничения (опционально) |

---

## Рекомендуемые модели

Актуально на **апрель 2026**. Разные агенты решают разные задачи — оптимальный выбор:

### Топовые модели для кодинга (по бенчмаркам)

| Модель | OpenRouter ID | Особенности |
| ------ | ------------- | ----------- |
| Claude Sonnet 4.6 | `anthropic/claude-sonnet-4-6` | Лучший баланс цена/качество для агентов и кода |
| Claude Opus 4.7 | `anthropic/claude-opus-4-7` | #2 в coding arena (1098/1100), лучший для сложных задач |
| DeepSeek V4 Flash | `deepseek/deepseek-v4-flash` | Быстрый, дешёвый, хороший для аналитических задач |
| DeepSeek V3.2 | `deepseek/deepseek-v3.2` | GPT-5 класс, отличный coding, дешевле frontier |
| Gemini 3 Flash Preview | `google/gemini-3-flash-preview` | Высокая скорость, thinking, coding и агентные задачи |
| MiMo-V2-Flash | `xiaomi/mimo-v2-flash` | **#1 open-source на SWE-bench Verified**, быстрый |
| MiMo-V2-Pro | `xiaomi/mimo-v2-pro` | Топ open-source, приближается к Opus 4.6 |
| Gemini 2.5 Flash | `google/gemini-2.5-flash` | Быстрый, хорошее reasoning и coding |
| Kimi K2.6 | `moonshot/kimi-k2.6` | Лучший open-source для кода на апрель 2026 |

### По агентам

| Агент | Задача | Лучший выбор | Бюджетный вариант |
| ----- | ------ | ------------ | ----------------- |
| `use_cases` | Юз-кейсы из БТ/БП | `deepseek/deepseek-v3.2` | `xiaomi/mimo-v2-flash` |
| `analyst` | Структурированный текст НФТ/ФТ | `anthropic/claude-sonnet-4-6` | `deepseek/deepseek-v3.2` |
| `architect` | JSON-план, архитектура | `anthropic/claude-opus-4-7` | `moonshot/kimi-k2.6` |
| `coder` | Генерация HTML/CSS/JS | `anthropic/claude-sonnet-4-6` | `xiaomi/mimo-v2-pro` |
| `self_check` | Code review, исправление структуры | `deepseek/deepseek-v3.2` | `xiaomi/mimo-v2-flash` |
| `tester` | Написание pytest-тестов | `deepseek/deepseek-v3.2` | `google/gemini-2.5-flash` |
| `fixer` | Исправление кода по тестам | `anthropic/claude-sonnet-4-6` | `moonshot/kimi-k2.6` |
| `patcher` | Точечные правки по инструкции | `google/gemini-2.5-flash` | `xiaomi/mimo-v2-flash` |

**Советы:**

- `coder`, `architect`, `fixer` — не экономить, от них зависит качество итогового кода
- `patcher`, `use_cases` — задачи простые, подойдут быстрые и дешёвые модели
- Бесплатно попробовать: `tencent/hy3-preview:free` или роутер `openrouter/free` (50 запросов/день)
- MiMo-V2-Flash — неожиданно сильный open-source вариант за малые деньги

---

## Стек

| Компонент | Технология |
| --------- | ---------- |
| Бэкенд генератора | Python 3.11, FastAPI |
| Веб-интерфейс | Next.js 15, React 19, Tailwind CSS |
| LLM-провайдер | OpenRouter |
| Генерируемое приложение | Vanilla HTML + CSS + JS |
| Тесты | pytest, pytest-timeout |
