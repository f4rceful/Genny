class UIRenderer {
    constructor(container) {
        this.container = container;
    }

    renderSidebar(projects, activeId) {
        const list = document.getElementById('projects-list');
        if (!list) return;
        list.innerHTML = '';
        projects.forEach(p => {
            if (p.archived) return;
            const div = document.createElement('div');
            div.className = `project-link ${p.id === activeId ? 'active' : ''}`;
            div.dataset.id = p.id;
            
            const dot = document.createElement('span');
            dot.className = 'project-dot';
            dot.style.backgroundColor = p.color || 'var(--accent)';
            
            const name = document.createElement('span');
            name.className = 'project-name';
            name.textContent = p.name;
            
            div.appendChild(dot);
            div.appendChild(name);
            list.appendChild(div);
        });
    }

    renderDashboard(data) {
        const { projects, tasks } = data;
        const overdue = tasks.filter(t => TaskManager.isOverdue(t.deadline) && t.status !== 'done').length;
        const inWork = tasks.filter(t => t.status === 'in-progress').length;
        const inReview = tasks.filter(t => t.status === 'review').length;
        const done = tasks.filter(t => t.status === 'done').length;

        let html = `
            <h2>Общий дашборд</h2>
            <div class="dashboard-grid">
                <div class="metric-card"><div class="metric-value">${tasks.length}</div><div class="metric-label">Всего задач</div></div>
                <div class="metric-card"><div class="metric-value">${inWork}</div><div class="metric-label">В работе</div></div>
                <div class="metric-card"><div class="metric-value">${inReview}</div><div class="metric-label">На проверке</div></div>
                <div class="metric-card"><div class="metric-value">${done}</div><div class="metric-label">Готово</div></div>
                <div class="metric-card"><div class="metric-value" style="color:#ef4444">${overdue}</div><div class="metric-label">Просрочено</div></div>
            </div>
            <h3>Прогресс проектов</h3>
            <table class="stats-table">
                <thead><tr><th>Проект</th><th>Задачи</th><th>Прогресс</th></tr></thead>
                <tbody>
        `;

        projects.forEach(p => {
            const pTasks = tasks.filter(t => t.projectId === p.id);
            if (pTasks.length === 0) return;
            const pDone = pTasks.filter(t => t.status === 'done').length;
            const percent = Math.round((pDone / pTasks.length) * 100);
            html += `
                <tr>
                    <td>${this.escapeHTML(p.name)}</td>
                    <td>${pDone} / ${pTasks.length}</td>
                    <td>
                        <div class="progress-bar-container"><div class="progress-bar-fill" style="width: ${percent}%"></div></div>
                        <span style="font-size:10px">${percent}%</span>
                    </td>
                </tr>
            `;
        });

        html += `</tbody></table><h3>Ближайшие дедлайны (7 дней)</h3><div id="nearby-deadlines">`;
        const nearby = TaskManager.getNearbyDeadlines(tasks);
        
        if (nearby.length === 0) {
            html += '<p style="color:var(--text-muted)">Нет срочных задач</p>';
        } else {
            nearby.forEach(t => {
                const proj = projects.find(p => p.id === t.projectId);
                html += `<div style="padding: 10px; background: var(--card-bg); margin-bottom: 8px; border-radius: 6px; display: flex; justify-content: space-between;">
                    <span style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-right: 10px;">${this.escapeHTML(t.title)} <small>(${proj ? this.escapeHTML(proj.name) : ''})</small></span>
                    <span class="${TaskManager.isToday(t.deadline) ? 'date-today' : ''}" style="flex-shrink:0">${t.deadline}</span>
                </div>`;
            });
        }
        
        html += `</div>`;
        this.container.innerHTML = html;
    }

    renderKanban(tasks) {
        const columns = [
            { id: 'backlog', title: 'Бэклог' },
            { id: 'in-progress', title: 'В работе' },
            { id: 'review', title: 'На проверке' },
            { id: 'done', title: 'Готово' }
        ];

        let html = `<div class="kanban-board">`;
        columns.forEach(col => {
            const colTasks = tasks.filter(t => t.status === col.id);
            html += `
                <div class="kanban-col" data-status="${col.id}">
                    <div class="col-header">
                        <span class="col-title">${col.title}</span>
                        <span class="task-count">${colTasks.length}</span>
                        <button class="btn-add-task" data-status="${col.id}">+</button>
                    </div>
                    <div class="task-list">`;
            colTasks.forEach(task => {
                html += this.getTaskCardHTML(task);
            });
            html += `</div></div>`;
        });
        html += `</div>`;
        this.container.innerHTML = html;
    }

    getTaskCardHTML(task) {
        const dlStatus = TaskManager.getDeadlineStatus(task.deadline);
        let dlClass = '';
        let dlLabel = task.deadline || '';
        if (dlStatus === 'overdue') { dlClass = 'date-overdue'; dlLabel += ' (Просрочено)'; }
        if (dlStatus === 'today') { dlClass = 'date-today'; dlLabel = 'СЕГОДНЯ'; }

        const tagsHtml = (task.tags || []).map(tag => 
            `<span class="tag" style="background: ${TaskManager.generateTagColor(tag)}">${this.escapeHTML(tag)}</span>`
        ).join('');

        const isFirst = task.status === 'backlog';
        const isLast = task.status === 'done';

        return `
            <div class="task-card priority-${task.priority}" data-id="${task.id}">
                <div class="task-header">${this.escapeHTML(task.title)}</div>
                <div class="task-desc">${this.escapeHTML(task.desc)}</div>
                <div class="task-tags">${tagsHtml}</div>
                <div class="task-footer">
                    <div class="task-date ${dlClass}">${dlLabel ? '🕒 ' + dlLabel : ''}</div>
                    <div class="task-actions">
                        ${!isFirst ? `<button class="action-btn move-btn" data-dir="-1" title="Назад">←</button>` : ''}
                        <button class="action-btn edit-btn" title="Изменить">✎</button>
                        <button class="action-btn delete-btn" title="Удалить">✕</button>
                        ${!isLast ? `<button class="action-btn move-btn" data-dir="1" title="Вперед">→</button>` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    renderListView(tasks) {
        if (tasks.length === 0) {
            this.container.innerHTML = '<p style="text-align:center; padding: 40px; color: var(--text-muted)">Нет задач, удовлетворяющих фильтрам</p>';
            return;
        }

        let html = `
            <table class="task-table">
                <thead>
                    <tr>
                        <th style="width: 50px">Приор.</th>
                        <th>Название</th>
                        <th style="width: 120px">Статус</th>
                        <th style="width: 120px">Дедлайн</th>
                        <th>Теги</th>
                        <th style="width: 100px">Действия</th>
                    </tr>
                </thead>
                <tbody>
        `;
        tasks.forEach(task => {
            html += `
                <tr data-id="${task.id}">
                    <td><span class="priority-dot" style="background: var(--${task.priority}-priority)"></span></td>
                    <td title="${this.escapeHTML(task.title)}"><strong>${this.escapeHTML(task.title)}</strong></td>
                    <td>${task.status}</td>
                    <td>${task.deadline || '-'}</td>
                    <td title="${(task.tags || []).join(', ')}">${this.escapeHTML((task.tags || []).join(', '))}</td>
                    <td>
                        <button class="action-btn edit-btn">✎</button>
                        <button class="action-btn delete-btn">✕</button>
                    </td>
                </tr>
            `;
        });
        html += `</tbody></table>`;
        this.container.innerHTML = html;
    }

    escapeHTML(str) {
        if (!str) return '';
        return str.replace(/[&<>"']/g, m => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
        }[m]));
    }
}