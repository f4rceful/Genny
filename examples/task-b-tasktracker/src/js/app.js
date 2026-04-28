document.addEventListener('DOMContentLoaded', () => {
    const dataManager = new DataManager();
    const contentArea = document.getElementById('content-area');
    if (!contentArea) return;
    
    const renderer = new UIRenderer(contentArea);
    
    let currentProjectId = 'dashboard';
    let currentViewMode = 'kanban';
    let filters = { search: '', priority: 'all', tag: 'all' };

    function init() {
        renderAll();
        setupGlobalEvents();
    }

    function renderAll() {
        const projects = dataManager.getProjects();
        renderer.renderSidebar(projects, currentProjectId);
        
        const viewControls = document.getElementById('view-controls');
        const filtersBar = document.getElementById('filters-bar');

        if (currentProjectId === 'dashboard') {
            if (viewControls) viewControls.style.display = 'none';
            if (filtersBar) filtersBar.style.display = 'none';
            renderer.renderDashboard({
                projects: projects,
                tasks: dataManager.tasks
            });
        } else {
            if (viewControls) viewControls.style.display = 'flex';
            if (filtersBar) filtersBar.style.display = 'flex';
            
            let tasks = dataManager.getTasksByProject(currentProjectId);
            updateTagFilter(tasks);
            tasks = TaskManager.filterTasks(tasks, filters);
            
            if (currentViewMode === 'kanban') {
                renderer.renderKanban(tasks);
            } else {
                renderer.renderListView(tasks);
            }
            updateResetButtonStatus();
        }
    }

    function updateTagFilter(projectTasks) {
        const tagSelect = document.getElementById('filter-tag');
        if (!tagSelect) return;
        const currentVal = tagSelect.value;
        const tags = new Set();
        projectTasks.forEach(t => {
            if (t.tags) t.tags.forEach(tag => tags.add(tag));
        });
        
        tagSelect.innerHTML = '<option value="all">Все теги</option>';
        tags.forEach(tag => {
            const opt = document.createElement('option');
            opt.value = tag;
            opt.textContent = tag;
            tagSelect.appendChild(opt);
        });
        tagSelect.value = tags.has(currentVal) ? currentVal : 'all';
    }

    function updateResetButtonStatus() {
        const count = [filters.priority !== 'all', filters.tag !== 'all', filters.search !== ''].filter(Boolean).length;
        const btn = document.getElementById('reset-filters');
        const countSpan = document.getElementById('filter-count');
        if (btn) btn.style.display = count > 0 ? 'inline-block' : 'none';
        if (countSpan) countSpan.textContent = count;
    }

    function setupGlobalEvents() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.addEventListener('click', (e) => {
                const navItem = e.target.closest('.nav-item');
                const projectLink = e.target.closest('.project-link');
                
                if (navItem) {
                    currentProjectId = 'dashboard';
                    document.querySelectorAll('.nav-item, .project-link').forEach(el => el.classList.remove('active'));
                    navItem.classList.add('active');
                    renderAll();
                } else if (projectLink) {
                    currentProjectId = projectLink.dataset.id;
                    document.querySelectorAll('.nav-item, .project-link').forEach(el => el.classList.remove('active'));
                    projectLink.classList.add('active');
                    renderAll();
                }
            });
        }

        const addProjectBtn = document.getElementById('add-project-btn');
        if (addProjectBtn) {
            addProjectBtn.addEventListener('click', () => {
                const modal = document.getElementById('project-modal');
                if (modal) modal.classList.add('active');
            });
        }

        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
            });
        });

        const projectForm = document.getElementById('project-form');
        if (projectForm) {
            projectForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const nameInput = document.getElementById('project-name');
                const activeColor = document.querySelector('.color-option.active');
                if (nameInput && nameInput.value.trim()) {
                    const color = activeColor ? activeColor.dataset.color : '#6366f1';
                    const p = dataManager.addProject(nameInput.value, color);
                    document.getElementById('project-modal').classList.remove('active');
                    projectForm.reset();
                    if (p) {
                        currentProjectId = p.id;
                        renderAll();
                    }
                }
            });
        }

        const colorPalette = document.getElementById('color-palette');
        if (colorPalette) {
            colorPalette.addEventListener('click', (e) => {
                if (e.target.classList.contains('color-option')) {
                    document.querySelectorAll('.color-option').forEach(o => o.classList.remove('active'));
                    e.target.classList.add('active');
                }
            });
        }

        contentArea.addEventListener('click', (e) => {
            const btn = e.target.closest('button');
            if (!btn) return;

            const card = e.target.closest('[data-id]');
            const taskId = card ? card.dataset.id : null;

            if (btn.classList.contains('btn-add-task')) {
                openTaskModal(null, btn.dataset.status);
            } else if (btn.classList.contains('move-btn')) {
                dataManager.moveTask(taskId, parseInt(btn.dataset.dir));
                renderAll();
            } else if (btn.classList.contains('delete-btn')) {
                if (confirm('Удалить задачу?')) {
                    dataManager.removeTask(taskId);
                    renderAll();
                }
            } else if (btn.classList.contains('edit-btn')) {
                openTaskModal(taskId);
            }
        });

        const taskForm = document.getElementById('task-form');
        if (taskForm) {
            taskForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const id = document.getElementById('task-id').value;
                const titleInput = document.getElementById('task-title');
                const submitBtn = document.getElementById('task-submit-btn');

                if (!titleInput.value.trim()) return;

                const tagsVal = document.getElementById('task-tags').value;
                const data = {
                    title: titleInput.value,
                    desc: document.getElementById('task-desc').value,
                    priority: document.getElementById('task-priority').value,
                    deadline: document.getElementById('task-deadline').value,
                    tags: tagsVal ? tagsVal.split(',').map(t => t.trim()).filter(Boolean) : [],
                    status: submitBtn.dataset.status || 'backlog'
                };

                if (id) {
                    dataManager.updateTask(id, data);
                } else {
                    dataManager.addTask(currentProjectId, data);
                }

                document.getElementById('task-modal').classList.remove('active');
                renderAll();
            });
        }

        const ghostInp = (id, key) => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('input', (e) => { filters[key] = e.target.value; renderAll(); });
        };
        const ghostChg = (id, key) => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', (e) => { filters[key] = e.target.value; renderAll(); });
        };

        ghostInp('global-search', 'search');
        ghostChg('filter-priority', 'priority');
        ghostChg('filter-tag', 'tag');

        const resetBtn = document.getElementById('reset-filters');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                filters = { search: '', priority: 'all', tag: 'all' };
                document.getElementById('global-search').value = '';
                document.getElementById('filter-priority').value = 'all';
                document.getElementById('filter-tag').value = 'all';
                renderAll();
            });
        }

        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentViewMode = btn.dataset.mode;
                renderAll();
            });
        });
    }

    function openTaskModal(taskId = null, defaultStatus = 'backlog') {
        const form = document.getElementById('task-form');
        if (!form) return;
        form.reset();
        
        const modalTitle = document.getElementById('task-modal-title');
        const submitBtn = document.getElementById('task-submit-btn');
        const taskIdHidden = document.getElementById('task-id');

        if (taskId) {
            const task = dataManager.tasks.find(t => t.id === taskId);
            if (!task) return;
            modalTitle.textContent = 'Редактировать задачу';
            submitBtn.textContent = 'Сохранить';
            taskIdHidden.value = task.id;
            document.getElementById('task-title').value = task.title;
            document.getElementById('task-desc').value = task.desc;
            document.getElementById('task-priority').value = task.priority;
            document.getElementById('task-deadline').value = task.deadline;
            document.getElementById('task-tags').value = (task.tags || []).join(', ');
            submitBtn.dataset.status = task.status;
        } else {
            modalTitle.textContent = 'Новая задача';
            submitBtn.textContent = 'Создать';
            taskIdHidden.value = '';
            submitBtn.dataset.status = defaultStatus;
        }
        
        const modal = document.getElementById('task-modal');
        if (modal) modal.classList.add('active');
    }

    init();
});