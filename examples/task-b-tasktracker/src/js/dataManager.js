class DataManager {
    constructor() {
        this.storageKey = 'taskflow_data';
        this.projects = [];
        this.tasks = [];
        this.loadData();
    }

    loadData() {
        try {
            const raw = localStorage.getItem(this.storageKey);
            if (raw) {
                const parsed = JSON.parse(raw);
                this.projects = Array.isArray(parsed.projects) ? parsed.projects : [];
                this.tasks = Array.isArray(parsed.tasks) ? parsed.tasks : [];
            } else {
                this.createDemoData();
            }
        } catch (e) {
            console.error("Failed to load data from localStorage", e);
            this.createDemoData();
        }
    }

    saveData() {
        try {
            const data = {
                projects: this.projects,
                tasks: this.tasks
            };
            localStorage.setItem(this.storageKey, JSON.stringify(data));
        } catch (e) {
            console.error("Failed to save data to localStorage", e);
        }
    }

    createDemoData() {
        const demoProject = {
            id: 'demo-1',
            name: 'Мой первый проект',
            color: '#6366f1',
            archived: false
        };
        this.projects = [demoProject];
        
        const now = new Date();
        const tomorrow = new Date(now);
        tomorrow.setDate(now.getDate() + 1);

        this.tasks = [
            { id: 't1', projectId: 'demo-1', title: 'Изучить TaskFlow', desc: 'Понять основные функции системы', priority: 'high', status: 'backlog', deadline: now.toISOString().split('T')[0], tags: ['обучение'] },
            { id: 't2', projectId: 'demo-1', title: 'Создать задачу', desc: 'Тестовое создание задачи', priority: 'medium', status: 'in-progress', deadline: tomorrow.toISOString().split('T')[0], tags: ['тест'] },
            { id: 't3', projectId: 'demo-1', title: 'Завершить этап', desc: 'Переместить задачу в Готово', priority: 'low', status: 'done', deadline: '', tags: [] }
        ];
        this.saveData();
    }

    addProject(name, color) {
        if (!name || typeof name !== 'string') return null;
        const project = {
            id: 'p-' + Date.now(),
            name: name.trim(),
            color: color || '#6366f1',
            archived: false
        };
        this.projects.push(project);
        this.saveData();
        return project;
    }

    addTask(projectId, taskData) {
        if (!projectId || !taskData.title) return null;
        const task = {
            id: 't-' + Date.now(),
            projectId,
            title: taskData.title.trim(),
            desc: (taskData.desc || '').trim(),
            priority: taskData.priority || 'medium',
            status: taskData.status || 'backlog',
            deadline: taskData.deadline || '',
            tags: Array.isArray(taskData.tags) ? taskData.tags : []
        };
        this.tasks.push(task);
        this.saveData();
        return task;
    }

    updateTask(taskId, updates) {
        const index = this.tasks.findIndex(t => t.id === taskId);
        if (index !== -1) {
            this.tasks[index] = { ...this.tasks[index], ...updates };
            this.saveData();
        }
    }

    removeTask(taskId) {
        this.tasks = this.tasks.filter(t => t.id !== taskId);
        this.saveData();
    }

    moveTask(taskId, direction) {
        const statuses = ['backlog', 'in-progress', 'review', 'done'];
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) return;

        const currentIndex = statuses.indexOf(task.status);
        const newIndex = currentIndex + direction;

        if (newIndex >= 0 && newIndex < statuses.length) {
            task.status = statuses[newIndex];
            this.saveData();
        }
    }

    getProjects() {
        return [...this.projects];
    }

    getTasksByProject(projectId) {
        return this.tasks.filter(t => t.projectId === projectId);
    }
}