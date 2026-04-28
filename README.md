# Genny (Команда Свободное плавание)

Генератор веб-приложений на основе LLM-агентов. Подаёте бизнес-требования и бизнес-процесс в формате Markdown — получаете готовое веб-приложение с полным комплектом документации (юз-кейсы, НФТ, ФТ, код, тесты).

```
БТ + БП + Features (опционально)
  └─► Юз-кейсы
      └─► НФТ + ФТ
          └─► Архитектурный план
              └─► Исходный код (HTML/CSS/JS)
                  └─► Тесты (pytest)
                      └─► Цикл автоисправления ↺
```

---

## Быстрый старт

> **Требования:** Python 3.11+, Node.js 18+, API-ключ [OpenRouter](https://openrouter.ai/keys)

### 1. Клонировать и установить зависимости

```bash
git clone https://github.com/f4rceful/Genny.git
cd Genny
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate.bat
pip install -r requirements.txt
```

### 2. Создать файл `.env`

Скопируйте пример и вставьте свой ключ:

```bash
cp .env.example .env
```

Откройте `.env` и вставьте ключ в первую строку:

```env
OPENROUTER_API_KEY=sk-or-v1-...
```

Остальные параметры в `.env.example` уже заполнены рабочими значениями — менять не нужно.

### 3. Запустить бэкенд

```bash
uvicorn main:app --reload
```

Сервер запустится на `http://localhost:8000`.

### 4. Запустить веб-интерфейс (в отдельном терминале)

```bash
cd frontend
npm install
npm run dev
```

Откройте **<http://localhost:3000>** — интерфейс готов.

### 5. Сгенерировать первый проект

В браузере:

1. Вставьте или загрузите файлы БТ и БП (примеры — в папке `test_input/`)
2. Нажмите «Начать разработку»
3. Дождитесь завершения (~3–7 минут)

Или через скрипт (пока сервер запущен):

```bash
python test_run.py              # Задание A — Веб-калькулятор
python test_run.py test_input_b # Задание B — Таск-трекер
python test_run.py test_input_c # Задание C — Конвертер валют
```

---

## Настройка моделей

Каждый агент использует свою модель. Всё задаётся в `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-...
# Основная модель
MODEL_DEFAULT=google/gemini-3-flash-preview

# Резервная модель (если основная упала)
MODEL_FALLBACK=deepseek/deepseek-v4-flash

# Модели по агентам
MODEL_USE_CASES=deepseek/deepseek-v3.2 # Юз кейсы
MODEL_ANALYST=deepseek/deepseek-v4-flash # Аналитик
MODEL_ARCHITECT=deepseek/deepseek-v4-flash #Архитектор
MODEL_CODER=google/gemini-3-flash-preview # Кодер(Разработчик-Программист)
MODEL_TESTER=deepseek/deepseek-v3.2 # Тестировщик
MODEL_FIXER=google/gemini-3-flash-preview # Фикшер(Исправляет ошибки тестов)
MODEL_PATCHER=google/gemini-3-flash-preview # Патчер (Редактирует итоговый код)

MAX_FIX_ATTEMPTS=3 # Попытки исправления тестов
```

> Если хотите использовать одну модель для всего, достаточно задать только `MODEL_DEFAULT`.

### Совместимые модели

Генератор работает через [OpenRouter](https://openrouter.ai) — совместим с любой моделью из их каталога. Проверенные варианты:

| Модель | OpenRouter ID | Подходит для |
| ------ | ------------- | ------------ |
| **Gemini 3.0 Flash Preview** | `google/gemini-3-flash-preview` | Кодинг, тесты, патчер — быстро и дёшево |
| **DeepSeek V3.2** | `deepseek/deepseek-v3.2` | Аналитика, юз-кейсы, архитектура |
| **DeepSeek V4 Flash** | `deepseek/deepseek-v4-flash` | Лучший баланс цена/качество |

> Любая другая модель из каталога OpenRouter тоже подойдёт. Предпочтительнее быстрые (flash/mini) — pipeline занимает меньше времени.

---

## Как это работает

Генератор запускает цепочку из 5 специализированных агентов:

| Агент | Задача | Выходной файл |
| ----- | ------ | ------------- |
| Use-cases | Выделяет пользовательские сценарии из БТ+БП | `docs/use-cases.md` |
| Аналитик | Генерирует НФТ и ФТ с привязкой к источникам | `docs/non-functional-req.md`, `docs/functional-req.md` |
| Архитектор | Проектирует файловую структуру приложения | `docs/architecture.json` |
| Кодогенератор | Пишет HTML/CSS/JS по архитектурному плану | `src/` + `README.md` |
| Тестировщик | Пишет pytest-тесты по ФТ | `tests/test_functional.py` |

После генерации автоматически запускаются тесты. Если что-то падает — агент-фиксер исправляет код и тесты перезапускаются (до 3 попыток).

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
│   └── test_functional.py
└── README.md
```

Сгенерированное приложение запускается напрямую: откройте `output/<run_id>/src/index.html` в браузере.

---

## Режим доработки

После завершённой генерации можно внести точечные правки через интерфейс (раздел «Доработка») или API:

```bash
curl -X POST http://localhost:8000/patch/<run_id> \
  -H "Content-Type: application/json" \
  -d '{"instruction": "добавь валидацию email"}'
```

Генератор обновит и код, и документацию.

---

## API

| Метод | Эндпоинт | Описание |
| ----- | -------- | -------- |
| POST | `/generate` | Запустить пайплайн, вернёт `run_id` |
| GET | `/status/{run_id}` | Статус, шаг, список файлов |
| POST | `/patch/{run_id}` | Точечные правки по инструкции |
| POST | `/cancel/{run_id}` | Отменить генерацию |
| GET | `/runs` | Список завершённых проектов |
| GET | `/file/{run_id}/{path}` | Содержимое файла |
| GET | `/download/{run_id}` | Скачать артефакты zip-архивом |

---

## Примеры сгенерированных приложений

В папке `examples/` лежат три готовых проекта, сгенерированных Genny из тестовых заданий:

| Папка | Приложение | Задание |
| ----- | ---------- | ------- |
| `examples/task-a-calculator/` | **MathBox** — веб-калькулятор с историей | A (простое) |
| `examples/task-b-tasktracker/` | **TaskFlow** — Kanban-трекер задач | B (среднее) |
| `examples/task-c-currency/` | **CurrencyFlow** — конвертер валют с API | C (сложное) |

Каждый пример содержит полный набор артефактов: `docs/`, `src/`, `tests/`, `README.md`.
Сгенерированное приложение запускается напрямую — откройте `src/index.html` в браузере.

---

## Тестовые задания

| Папка | Задание | Сложность |
| ----- | ------- | --------- |
| `test_input/` | A — Веб-калькулятор | Простое |
| `test_input_b/` | B — Таск-трекер | Среднее |
| `test_input_c/` | C — Конвертер валют с API | Сложное |
| `test_input_taskflow/` | D — TaskFlow (Kanban) | Сложное |
| `test_input_mealflow/` | E — MealFlow (планировщик питания) | Сложное |

---

## Стек

| Компонент | Технология |
| --------- | ---------- |
| Бэкенд генератора | Python 3.11, FastAPI |
| Веб-интерфейс | Next.js 15, React 19, Tailwind CSS |
| LLM-провайдер | OpenRouter (любая совместимая модель) |
| Генерируемое приложение | Vanilla HTML + CSS + JS |
| Тесты | pytest, pytest-timeout |
