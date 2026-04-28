/**
 * Менеджер управления кешем в localStorage
 */
class CacheManager {
    constructor() {
        this.storageKey = 'courses_cache';
        this.ttlMs = 60 * 60 * 1000; // 1 час
    }

    save(rates, timestamp) {
        try {
            const data = { rates, timestamp };
            localStorage.setItem(this.storageKey, JSON.stringify(data));
        } catch (e) {
            console.error('Failed to save cache', e);
        }
    }

    load() {
        const raw = localStorage.getItem(this.storageKey);
        if (!raw) return null;
        try {
            const parsed = JSON.parse(raw);
            if (parsed && typeof parsed === 'object' && parsed.rates) {
                return parsed;
            }
            return null;
        } catch (e) {
            return null;
        }
    }

    isValid() {
        const data = this.load();
        if (!data || !data.timestamp) return false;
        
        const age = Date.now() - data.timestamp;
        return age < this.ttlMs;
    }
}