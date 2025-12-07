// Główny plik JavaScript aplikacji
// Zawiera wspólne funkcje używane w całej aplikacji

// Konfiguracja API
const API_BASE_URL = '/api';

// Utility functions
const utils = {
    /**
     * Wykonuje zapytanie do API
     */
    async apiRequest(endpoint, method = 'GET', data = null) {
        // TODO: Implementować uniwersalną funkcję do komunikacji z API
        // TODO: Obsługa tokenów JWT (localStorage/sessionStorage)
        // TODO: Obsługa błędów
        // TODO: Loading states
        
        const token = localStorage.getItem('access_token');
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const options = {
            method,
            headers,
        };
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
            // TODO: Obsługa odpowiedzi
            return response;
        } catch (error) {
            // TODO: Obsługa błędów
            console.error('API Error:', error);
            throw error;
        }
    },
    
    /**
     * Formatuje datę
     */
    formatDate(dateString) {
        // TODO: Implementować formatowanie dat
        // TODO: Użyć polskiego formatu
        return dateString;
    },
    
    /**
     * Wyświetla toast notification
     */
    showToast(message, type = 'info') {
        // TODO: Implementować system powiadomień toast
        console.log(`[${type}] ${message}`);
    },
    
    /**
     * Sprawdza czy użytkownik jest zalogowany
     */
    isAuthenticated() {
        // TODO: Implementować sprawdzanie autentykacji
        return !!localStorage.getItem('access_token');
    },
    
    /**
     * Wylogowuje użytkownika
     */
    logout() {
        // TODO: Implementować wylogowanie
        localStorage.removeItem('access_token');
        window.location.href = '/auth/login';
    }
};

// Eksport dla innych modułów
if (typeof module !== 'undefined' && module.exports) {
    module.exports = utils;
}

// TODO: Dodać event listeners dla nawigacji
// TODO: Dodać sprawdzanie autentykacji przy ładowaniu strony
