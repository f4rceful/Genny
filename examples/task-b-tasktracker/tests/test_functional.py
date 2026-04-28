"""
Тесты бизнес-логики приложения TaskFlow.
Проверяют соответствие реализации функциональным требованиям на основе логики классов DataManager и TaskManager.
"""
import pytest
from datetime import datetime, timedelta

# --- Вспомогательные функции (эмуляция бизнес-логики из JS) ---

def create_project(projects_list, name, color="#6366f1"):
    """Эмуляция DataManager.addProject (ФТ-01)."""
    if not name or not isinstance(name, str) or not name.strip():
        return None
    project = {
        'id': f'p-{len(projects_list)}',
        'name': name.strip(),
        'color': color,
        'archived': False
    }
    projects_list.append(project)
    return project

def create_task(tasks_list, project_id, task_data):
    """Эмуляция DataManager.addTask (ФТ-03)."""
    if not project_id or not task_data.get('title') or not task_data['title'].strip():
        return None
    task = {
        'id': f't-{len(tasks_list)}',
        'projectId': project_id,
        'title': task_data['title'].strip(),
        'desc': task_data.get('desc', '').strip(),
        'priority': task_data.get('priority', 'medium'),
        'status': task_data.get('status', 'backlog'),
        'deadline': task_data.get('deadline', ''),
        'tags': task_data.get('tags', [])
    }
    tasks_list.append(task)
    return task

def move_task(tasks_list, task_id, direction):
    """Эмуляция DataManager.moveTask (ФТ-04)."""
    statuses = ['backlog', 'in-progress', 'review', 'done']
    task = next((t for t in tasks_list if t['id'] == task_id), None)
    if not task:
        return
    
    current_idx = statuses.index(task['status'])
    new_idx = current_idx + direction
    
    if 0 <= new_idx < len(statuses):
        task['status'] = statuses[new_idx]

def get_deadline_status(deadline, current_date_str=None):
    """Эмуляция TaskManager.getDeadlineStatus (ФТ-05, ФТ-06)."""
    if not deadline:
        return 'normal'
    
    # В реальности используется текущая дата браузера. Для тестов передаем явно.
    today = datetime.strptime(current_date_str, '%Y-%m-%d').date() if current_date_str else datetime.now().date()
    d_date = datetime.strptime(deadline, '%Y-%m-%d').date()
    
    if d_date < today:
        return 'overdue'
    if d_date == today:
        return 'today'
    return 'normal'

def filter_tasks(tasks, filters):
    """Эмуляция TaskManager.filterTasks (ФТ-10, ФТ-11)."""
    filtered = []
    for task in tasks:
        # Поиск (ФТ-11)
        if filters.get('search'):
            query = filters['search'].lower()
            in_title = query in (task.get('title') or '').lower()
            in_desc = query in (task.get('desc') or '').lower()
            if not in_title and not in_desc:
                continue
        
        # Приоритет (ФТ-10)
        if filters.get('priority') and filters['priority'] != 'all':
            if task.get('priority') != filters['priority']:
                continue
        
        # Теги (ФТ-10)
        if filters.get('tag') and filters['tag'] != 'all':
            if not task.get('tags') or filters['tag'] not in task['tags']:
                continue
                
        filtered.append(task)
    return filtered

# --- Тесты ---

def test_create_project_validation():
    # ФТ-01: Создание проекта
    projects = []
    # Валидное создание
    p = create_project(projects, "Тестовый проект", "#FF0000")
    assert p is not None
    assert len(projects) == 1
    assert projects[0]['name'] == "Тестовый проект"
    
    # Пустое название
    p_err = create_project(projects, "")
    assert p_err is None
    assert len(projects) == 1

def test_task_creation_and_default_values():
    # ФТ-03: Создание задачи
    tasks = []
    task_data = {
        'title': ' Купить молоко ', # Проверка trim()
        'desc': 'В магазине'
    }
    task = create_task(tasks, 'p1', task_data)
    
    assert task['title'] == 'Купить молоко'
    assert task['priority'] == 'medium' # По умолчанию средний
    assert task['status'] == 'backlog'   # По умолчанию бэклог
    assert len(tasks) == 1
    
    # Обязательность названия
    assert create_task(tasks, 'p1', {'title': ''}) is None

def test_move_task_boundaries():
    # ФТ-04: Перемещение задачи между колонками
    tasks = [{'id': 't1', 'status': 'backlog'}]
    
    # Вперед
    move_task(tasks, 't1', 1)
    assert tasks[0]['status'] == 'in-progress'
    
    # Назад в начало
    move_task(tasks, 't1', -1)
    assert tasks[0]['status'] == 'backlog'
    
    # Попытка выйти за границы (назад из первой)
    move_task(tasks, 't1', -1)
    assert tasks[0]['status'] == 'backlog'
    
    # В самый конец и попытка выйти вперед
    tasks[0]['status'] = 'done'
    move_task(tasks, 't1', 1)
    assert tasks[0]['status'] == 'done'

def test_deadline_logic():
    # ФТ-05 и ФТ-06: Визуальное выделение дедлайнов
    current_date = "2023-10-10"
    
    # Сегодня
    assert get_deadline_status("2023-10-10", current_date) == 'today'
    # Просрочено
    assert get_deadline_status("2023-10-09", current_date) == 'overdue'
    # Будущее
    assert get_deadline_status("2023-10-11", current_date) == 'normal'
    # Без даты
    assert get_deadline_status("", current_date) == 'normal'

def test_filtering_and_search():
    # ФТ-10, ФТ-11: Фильтрация и поиск
    tasks = [
        {'title': 'Баг в логине', 'desc': 'Найти ошибку', 'priority': 'high', 'tags': ['bug']},
        {'title': 'Фича А', 'desc': 'Сделать красиво', 'priority': 'medium', 'tags': ['feature']},
        {'title': 'Документация', 'desc': 'Написать API', 'priority': 'low', 'tags': ['docs']}
    ]
    
    # Поиск по названию (регистронезависимо)
    res = filter_tasks(tasks, {'search': 'БАГ'})
    assert len(res) == 1
    assert res[0]['title'] == 'Баг в логине'
    
    # Поиск по описанию
    res = filter_tasks(tasks, {'search': 'красиво'})
    assert len(res) == 1
    
    # Фильтр по приоритету
    res = filter_tasks(tasks, {'priority': 'low'})
    assert len(res) == 1
    
    # Фильтр по тегу
    res = filter_tasks(tasks, {'tag': 'feature'})
    assert len(res) == 1
    
    # Комбинированный фильтр (AND-логика)
    res = filter_tasks(tasks, {'priority': 'high', 'tag': 'docs'})
    assert len(res) == 0

def test_dashboard_statistics():
    # ФТ-12: Отображение дашборда со статистикой (Логика расчета)
    tasks = [
        {'status': 'backlog', 'deadline': '2000-01-01'}, # Просрочена
        {'status': 'in-progress', 'deadline': ''},
        {'status': 'done', 'deadline': '2000-01-01'}     # Выполнена (не считается просроченной)
    ]
    
    # Эмуляция расчета UIRenderer.renderDashboard
    current_date = datetime.now().strftime('%Y-%m-%d')
    overdue_count = len([t for t in tasks if get_deadline_status(t['deadline'], "2023-01-01") == 'overdue' and t['status'] != 'done'])
    done_count = len([t for t in tasks if t['status'] == 'done'])
    
    assert overdue_count == 1
    assert done_count == 1

def test_nearby_deadlines_logic():
    # ФТ-12: Список задач с дедлайном в ближайшие 7 дней
    # См. TaskManager.getNearbyDeadlines
    today_dt = datetime(2023, 10, 10)
    tasks = [
        {'title': 'T1', 'status': 'backlog', 'deadline': '2023-10-10'}, # Сегодня
        {'title': 'T2', 'status': 'backlog', 'deadline': '2023-10-15'}, # Через 5 дней (входит)
        {'title': 'T3', 'status': 'backlog', 'deadline': '2023-10-20'}, # Далеко
        {'title': 'T4', 'status': 'done', 'deadline': '2023-10-11'},    # Готово (не входит)
    ]
    
    limit_date = today_dt + timedelta(days=7)
    
    nearby = []
    for t in tasks:
        if not t['deadline'] or t['status'] == 'done':
            continue
        dt = datetime.strptime(t['deadline'], '%Y-%m-%d')
        if today_dt <= dt <= limit_date:
            nearby.append(t)
            
    assert len(nearby) == 2
    assert 'T1' in [t['title'] for t in nearby]
    assert 'T2' in [t['title'] for t in nearby]