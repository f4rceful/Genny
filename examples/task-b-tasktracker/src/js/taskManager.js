class TaskManager {
    static filterTasks(tasks, filters) {
        if (!Array.isArray(tasks)) return [];
        
        return tasks.filter(task => {
            if (filters.search) {
                const query = filters.search.toLowerCase();
                const inTitle = (task.title || '').toLowerCase().includes(query);
                const inDesc = (task.desc || '').toLowerCase().includes(query);
                if (!inTitle && !inDesc) return false;
            }

            if (filters.priority && filters.priority !== 'all') {
                if (task.priority !== filters.priority) return false;
            }

            if (filters.tag && filters.tag !== 'all') {
                if (!task.tags || !task.tags.includes(filters.tag)) return false;
            }

            return true;
        });
    }

    static isOverdue(deadline) {
        if (!deadline) return false;
        const dDate = new Date(deadline).setHours(0,0,0,0);
        const today = new Date().setHours(0,0,0,0);
        return dDate < today;
    }

    static isToday(deadline) {
        if (!deadline) return false;
        const dDate = new Date(deadline).setHours(0,0,0,0);
        const today = new Date().setHours(0,0,0,0);
        return dDate === today;
    }

    static getDeadlineStatus(deadline) {
        if (this.isOverdue(deadline)) return 'overdue';
        if (this.isToday(deadline)) return 'today';
        return 'normal';
    }

    static generateTagColor(tag) {
        let hash = 0;
        const tagStr = String(tag);
        for (let i = 0; i < tagStr.length; i++) {
            hash = tagStr.charCodeAt(i) + ((hash << 5) - hash);
        }
        const h = Math.abs(hash) % 360;
        return `hsl(${h}, 60%, 45%)`;
    }

    static getNearbyDeadlines(tasks, days = 7) {
        const today = new Date().setHours(0,0,0,0);
        const limit = new Date();
        limit.setDate(limit.getDate() + days);
        const limitTime = limit.setHours(23,59,59,999);

        return tasks.filter(t => {
            if (!t.deadline || t.status === 'done') return false;
            const dt = new Date(t.deadline).getTime();
            return dt >= today && dt <= limitTime;
        }).sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
    }
}