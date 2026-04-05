const translations = {
    en: {
        "title_book": "Book Ticket",
        "bus_no": "Bus No",
        "route": "Route",
        "from_stop": "From Stop",
        "to_stop": "To Stop",
        "pass_name": "Passenger Name",
        "pass_phone": "Phone Number",
        "pay_now": "Pay Now",
        "select_stop": "-- Select Stop --",
        "live_fare": "Fare",
        "status_title": "Ticket Status",
        "download_pdf": "Download PDF",
        "save_qr": "Save QR Image",
        "dashboard_title": "Conductor Dashboard",
        "live_passengers": "Active Passengers",
        "scan_btn": "Scan Ticket QR",
        "logout": "Logout",
        "verify_success": "Valid Ticket",
        "verify_error": "Invalid/Used Ticket",
        "mark_used": "Mark as Used",
        "login_title": "Conductor Login",
        "username": "Username",
        "password": "Password",
        "select_bus": "Select Bus",
        "login_btn": "Sign In",
        "ticket_id": "Ticket ID",
        "date_time": "Date/Time",
        "end_trip": "End Trip",
    },
    ta: {
        "title_book": "டிக்கெட் முன்பதிவு",
        "bus_no": "பேருந்து எண்",
        "route": "வழித்தடம்",
        "from_stop": "புறப்படும் இடம்",
        "to_stop": "சேருமிடம்",
        "pass_name": "பயணியின் பெயர்",
        "pass_phone": "தொலைபேசி எண்",
        "pay_now": "பணத்தை செலுத்துக",
        "select_stop": "-- நிறுத்தம் --",
        "live_fare": "கட்டணம்",
        "status_title": "டிக்கெட் நிலை",
        "download_pdf": "PDF பதிவிறக்கம்",
        "save_qr": "QR ஐ சேமிக்கவும்",
        "dashboard_title": "நடத்துனர் தளம்",
        "live_passengers": "பயணிகள் எண்ணிக்கை",
        "scan_btn": "QR ஸ்கேன் செய்",
        "logout": "வெளியேறு",
        "verify_success": "செல்லுபடியாகும்",
        "verify_error": "ஏற்கனவே பயன்படுத்தப்பட்டது",
        "mark_used": "பயன்படுத்தியதாக மாற்று",
        "login_title": "நடத்துனர் நுழைவு",
        "username": "பயனர்பெயர்",
        "password": "கடவுச்சொல்",
        "select_bus": "பேருந்தை தேர்ந்தெடு",
        "login_btn": "உள்நுழைய",
        "ticket_id": "டிக்கெட் எண்",
        "date_time": "தேதி/நேரம்",
        "end_trip": "பயணத்தை முடி",
    }
};

let currentLang = localStorage.getItem('lang') || 'en';

function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'ta' : 'en';
    localStorage.setItem('lang', currentLang);
    applyTranslations();
    
    // Dispatch custom event so other scripts can react (like rebuilding dropdowns)
    window.dispatchEvent(new Event('languageChanged'));
}

function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[currentLang][key]) {
            el.innerText = translations[currentLang][key];
        }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (translations[currentLang][key]) {
            el.setAttribute('placeholder', translations[currentLang][key]);
        }
    });
}

document.addEventListener("DOMContentLoaded", applyTranslations);
