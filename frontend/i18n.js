const translations = {
    "en": {
        "nav_home": "Home",
        "nav_chat": "Chat Assistant",
        "nav_dashboard": "Dashboard",
        "nav_menu": "Menu Builder",
        "btn_understand": "I Understand, Let's Go",
        "welcome_title": "Welcome to Nightlife Concierge",
        "welcome_sub": "Your personal AI assistant for discovering the perfect night out.",
        "t0_title": "T0: Onboarding & Limitations",
        "t0_1": "I use aggregated data from Google Maps and social media to suggest venues.",
        "t0_2": "I cannot automatically book a table or guarantee seating availability.",
        "t0_3": "I am here to understand your mood and recommend, not to aggressively sell.",
        "choose_persona": "Who are you today?",
        "persona_guest": "I am a Guest",
        "persona_guest_sub": "Looking for the perfect venue and drinks",
        "persona_bartender": "I am a Bartender",
        "persona_bartender_sub": "Looking to create menus and manage F&B",
        "chat_placeholder": "Tell me your mood, or what you're looking for...",
        "dashboard_title": "Bar Management Dashboard",
        "dashboard_inventory": "Inventory Overview",
        "dashboard_trends": "Trending Cocktails",
        "menu_title": "AI Menu Builder",
        "menu_generate": "Generate PDF Menu",
        "mixology_title": "Mixology Assistant",
        "mixology_calculate": "Calculate Cost & ABV",
        "venue_details": "Venue Details",
        "venue_book": "Get Directions"
    },
    "vi": {
        "nav_home": "Trang chủ",
        "nav_chat": "Trợ lý Chat",
        "nav_dashboard": "Bảng điều khiển",
        "nav_menu": "Tạo Menu",
        "btn_understand": "Tôi đã hiểu, Bắt đầu nào",
        "welcome_title": "Chào mừng đến với Trợ lý Nightlife",
        "welcome_sub": "Trợ lý AI cá nhân giúp bạn tìm kiếm một đêm đi chơi hoàn hảo.",
        "t0_title": "T0: Hướng dẫn & Giới hạn",
        "t0_1": "Tôi sử dụng dữ liệu tổng hợp từ Google Maps và MXH để gợi ý quán.",
        "t0_2": "Tôi không thể tự động đặt bàn hoặc đảm bảo quán còn chỗ.",
        "t0_3": "Tôi ở đây để hiểu tâm trạng của bạn và gợi ý, không nhằm mục đích chèo kéo.",
        "choose_persona": "Hôm nay bạn là ai?",
        "persona_guest": "Tôi là Khách",
        "persona_guest_sub": "Tìm kiếm quán bar và đồ uống hoàn hảo",
        "persona_bartender": "Tôi là Bartender",
        "persona_bartender_sub": "Sáng tạo menu và quản lý F&B",
        "chat_placeholder": "Hãy kể cho tôi nghe tâm trạng của bạn...",
        "dashboard_title": "Bảng điều khiển Quán Bar",
        "dashboard_inventory": "Tổng quan Kho",
        "dashboard_trends": "Cocktail Đang Thịnh Hành",
        "menu_title": "Tạo Menu bằng AI",
        "menu_generate": "Xuất PDF Menu",
        "mixology_title": "Trợ lý Pha chế",
        "mixology_calculate": "Tính giá vốn & Độ cồn",
        "venue_details": "Chi tiết Quán",
        "venue_book": "Chỉ đường"
    }
};

const textFallbackMapping = {
    "Home": "nav_home",
    "Chat Assistant": "nav_chat",
    "Dashboard": "nav_dashboard",
    "Menu Builder": "nav_menu",
    "I Understand, Let's Go": "btn_understand",
    "Welcome to Nightlife Concierge": "welcome_title",
    "Your personal AI assistant for discovering the perfect night out.": "welcome_sub",
    "T0: Onboarding & Limitations": "t0_title",
    "I use aggregated data from Google Maps and social media to suggest venues.": "t0_1",
    "I cannot automatically book a table or guarantee seating availability.": "t0_2",
    "I am here to understand your mood and recommend, not to aggressively sell.": "t0_3",
    "Who are you today?": "choose_persona",
    "I am a Guest": "persona_guest",
    "Looking for the perfect venue and drinks": "persona_guest_sub",
    "I am a Bartender": "persona_bartender",
    "Looking to create menus and manage F&B": "persona_bartender_sub",
    "Bar Management Dashboard": "dashboard_title",
    "Inventory Overview": "dashboard_inventory",
    "Trending Cocktails": "dashboard_trends",
    "AI Menu Builder": "menu_title",
    "Generate PDF Menu": "menu_generate",
    "Mixology Assistant": "mixology_title",
    "Calculate Cost & ABV": "mixology_calculate",
    "Venue Details": "venue_details",
    "Get Directions": "venue_book"
};

let currentLang = localStorage.getItem("app_lang") || "en";

function initI18n() {
    updateDOM();
}

function toggleLanguage() {
    currentLang = currentLang === "en" ? "vi" : "en";
    localStorage.setItem("app_lang", currentLang);
    updateDOM();
}

function updateDOM() {
    // 1. Update elements with data-i18n
    const elements = document.querySelectorAll("[data-i18n]");
    elements.forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (translations[currentLang][key]) {
            // Check if it's an input with placeholder
            if (el.tagName === "INPUT" && el.hasAttribute("placeholder")) {
                el.setAttribute("placeholder", translations[currentLang][key]);
            } else {
                // Keep inner HTML structure (e.g. icons) if possible, or just replace text
                // For safety in prototypes, replace text but keep icons if we marked them properly
                // Here we simply replace text.
                el.innerText = translations[currentLang][key];
            }
        }
    });

    // 2. Update language toggle button text
    const toggleBtn = document.querySelector(".lang-toggle");
    if (toggleBtn) {
        toggleBtn.innerText = currentLang === "en" ? "EN / VI" : "VI / EN";
    }

    // 3. Fallback for text nodes (Hack for quick prototype translation)
    translateTextNodes(document.body);
}

function translateTextNodes(node) {
    if (node.nodeType === 3) { // Text node
        let text = node.nodeValue.trim();
        // Remove trailing icons or arrows for matching
        let cleanText = text.replace(/<[^>]*>?/gm, '').trim();
        
        // Exact match with fallback dictionary
        for (let [enText, key] of Object.entries(textFallbackMapping)) {
            if (cleanText === enText || cleanText === translations["vi"][key]) {
                node.nodeValue = node.nodeValue.replace(cleanText, translations[currentLang][key]);
            }
        }
    } else if (node.nodeType === 1 && node.className !== "lang-toggle" && !node.hasAttribute("data-i18n")) { // Element node
        for (let i = 0; i < node.childNodes.length; i++) {
            translateTextNodes(node.childNodes[i]);
        }
    }
}

// Auto-init on load
document.addEventListener("DOMContentLoaded", initI18n);
