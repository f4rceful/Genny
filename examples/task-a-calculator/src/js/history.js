class HistoryManager {
    constructor() {
        this.storageKey = 'mathbox_history';
        this.entries = this.loadFromStorage();
    }

    addEntry(entry) {
        const sanitizedEntry = {
            op1: String(entry.op1),
            op: String(entry.op),
            op2: String(entry.op2),
            res: entry.res === null ? 'Ошибка' : String(entry.res),
            timestamp: Date.now()
        };

        this.entries.unshift(sanitizedEntry);
        
        if (this.entries.length > 10) {
            this.entries.pop();
        }

        this.saveToStorage();
        return this.entries;
    }

    getEntries() {
        return this.entries;
    }

    saveToStorage() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.entries));
        } catch (e) {
            console.error("Failed to save history", e);
        }
    }

    loadFromStorage() {
        const data = localStorage.getItem(this.storageKey);
        if (!data) return [];
        try {
            const parsed = JSON.parse(data);
            return Array.isArray(parsed) ? parsed : [];
        } catch (e) {
            console.error("Ошибка парсинга истории", e);
            return [];
        }
    }
}