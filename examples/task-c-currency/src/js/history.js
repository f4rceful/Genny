/**
 * Управление историей операций (бизнес-логика + хранение)
 */
class HistoryManager {
    constructor() {
        this.storageKey = 'conversion_history';
        this.maxEntries = 10;
    }

    addEntry(entry) {
        const history = this.getAll();
        
        const cleanEntry = {
            from: String(entry.from || ''),
            to: String(entry.to || ''),
            amount: Number(entry.amount) || 0,
            result: Number(entry.result) || 0,
            date: Date.now()
        };

        history.unshift(cleanEntry);
        const limitedHistory = history.slice(0, this.maxEntries);
        
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(limitedHistory));
        } catch (e) {
            console.error('Failed to save history', e);
        }
        
        return limitedHistory;
    }

    getAll() {
        const raw = localStorage.getItem(this.storageKey);
        if (!raw) return [];
        try {
            const parsed = JSON.parse(raw);
            return Array.isArray(parsed) ? parsed : [];
        } catch (e) {
            return [];
        }
    }
}