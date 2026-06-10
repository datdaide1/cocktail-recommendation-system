// Application State
let activeTab = 'cocktails'; // 'cocktails' or 'bars'
let currentSessionId = '';
let sessions = [];
let chatHistory = [];
let cocktailsData = [];
let barsData = [];
let mapInstance = null; // Leaflet map instance
let mapMarkers = [];

// Multi-User Anonymous ID Generation
function getOrGenerateUserId() {
    let uid = localStorage.getItem('cocktail_user_id');
    if (!uid) {
        uid = 'usr-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now();
        localStorage.setItem('cocktail_user_id', uid);
    }
    return uid;
}
const CLIENT_USER_ID = getOrGenerateUserId();

// DOM Elements
const chatBox = document.getElementById('chat-box');
const chatInput = document.getElementById('chat-input');
const btnSendChat = document.getElementById('btn-send-chat');
const chatSessionSelect = document.getElementById('chat-session-select');

const tabExploreCocktails = document.getElementById('tab-explore-cocktails');
const tabExploreBars = document.getElementById('tab-explore-bars');
const mainGrid = document.getElementById('main-grid');
const mapContainer = document.getElementById('map-container');

// Mobile Panel Toggle
const btnTogglePanel = document.getElementById('btn-toggle-panel');
const btnClosePanel = document.getElementById('btn-close-panel');
const discoveryPanel = document.getElementById('discovery-panel');

// Filters
const gridSearchInput = document.getElementById('grid-search-input');
const filterPanel = document.getElementById('filter-panel');
const btnToggleFilters = document.getElementById('btn-toggle-filters');
const cocktailFiltersDiv = document.getElementById('cocktail-filters');
const barFiltersDiv = document.getElementById('bar-filters');

// Detail Modal
const detailModal = document.getElementById('detail-modal');
const btnCloseDetailModal = document.getElementById('btn-close-detail-modal');

document.addEventListener('DOMContentLoaded', () => {
    setupLanguageToggle();
    setupTabSwitcher();
    setupChatWidget();
    setupFilters();
    setupMobilePanel();
    
    // Initial fetch
    fetchSession();
    fetchCocktailsDatabase();
    fetchBarsDatabase();
});

// 0. LANGUAGE TOGGLE
let currentLang = 'EN';
function setupLanguageToggle() {
    const btnToggleLang = document.getElementById('btn-toggle-lang');
    if(!btnToggleLang) return;
    
    btnToggleLang.addEventListener('click', () => {
        currentLang = currentLang === 'EN' ? 'VI' : 'EN';
        btnToggleLang.innerText = currentLang === 'EN' ? '🌐 EN | VI' : '🌐 VI | EN';
        
        // Update placeholders and static texts
        if(currentLang === 'VI') {
            document.getElementById('chat-input').placeholder = "Hỏi công thức hoặc địa điểm...";
            if(gridSearchInput) gridSearchInput.placeholder = "Tìm kiếm...";
            document.getElementById('tab-explore-cocktails').innerHTML = '<i class="fa-solid fa-martini-glass-citrus mr-2"></i> Đồ uống';
            document.getElementById('tab-explore-bars').innerHTML = '<i class="fa-solid fa-compass mr-2"></i> Địa điểm';
            document.getElementById('btn-toggle-panel').innerHTML = '<i class="fa-solid fa-compass"></i> Khám phá';
            // System prompt instruction for the LLM
            chatHistory.push({ role: "user", parts: ["Please respond in Vietnamese from now on."] });
            sendSilentChat("Please respond in Vietnamese from now on. Answer with: 'Dạ vâng, em sẽ dùng tiếng Việt ạ.'");
        } else {
            document.getElementById('chat-input').placeholder = "Ask for a recipe or venue...";
            if(gridSearchInput) gridSearchInput.placeholder = "Search...";
            document.getElementById('tab-explore-cocktails').innerHTML = '<i class="fa-solid fa-martini-glass-citrus mr-2"></i> Cocktails';
            document.getElementById('tab-explore-bars').innerHTML = '<i class="fa-solid fa-compass mr-2"></i> Venues';
            document.getElementById('btn-toggle-panel').innerHTML = '<i class="fa-solid fa-compass"></i> Discover';
            chatHistory.push({ role: "user", parts: ["Please respond in English from now on."] });
            sendSilentChat("Please respond in English from now on. Answer with: 'Certainly, I will use English.'");
        }
    });
}

// Helper to silently change language mode on the backend
async function sendSilentChat(message) {
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                chat_history: chatHistory.slice(0, -1),
                role: 'guest',
                session_id: currentSessionId,
                user_id: CLIENT_USER_ID
            })
        });
        const data = await response.json();
        if (response.ok && !data.error) {
            chatHistory.push({ role: "model", parts: [data.message] });
            appendMessageToUI('model', data.message);
        }
    } catch(err) {
        console.error(err);
    }
}

// 1. MOBILE RESPONSIVE PANEL
function setupMobilePanel() {
    btnTogglePanel.addEventListener('click', () => {
        discoveryPanel.classList.remove('translate-x-full');
    });
    btnClosePanel.addEventListener('click', () => {
        discoveryPanel.classList.add('translate-x-full');
    });
}

// 2. TAB SWITCHER
function setupTabSwitcher() {
    tabExploreCocktails.addEventListener('click', () => {
        activeTab = 'cocktails';
        tabExploreCocktails.className = "py-2 px-4 rounded-lg bg-lounge-dark border border-gold text-gold font-bold text-sm shadow-sm transition-all";
        tabExploreBars.className = "py-2 px-4 rounded-lg bg-transparent border border-transparent text-lounge-muted font-bold text-sm hover:text-lounge-text transition-all";
        
        if (cocktailFiltersDiv) cocktailFiltersDiv.classList.remove('hidden');
        if (barFiltersDiv) barFiltersDiv.classList.add('hidden');
        mapContainer.classList.add('hidden');
        
        applyFilters();
    });

    tabExploreBars.addEventListener('click', () => {
        activeTab = 'bars';
        tabExploreBars.className = "py-2 px-4 rounded-lg bg-lounge-dark border border-gold text-gold font-bold text-sm shadow-sm transition-all";
        tabExploreCocktails.className = "py-2 px-4 rounded-lg bg-transparent border border-transparent text-lounge-muted font-bold text-sm hover:text-lounge-text transition-all";
        
        if (cocktailFiltersDiv) cocktailFiltersDiv.classList.add('hidden');
        if (barFiltersDiv) barFiltersDiv.classList.remove('hidden');
        mapContainer.classList.remove('hidden');
        
        // Initialize map if not yet created
        if (!mapInstance) {
            initMap();
        }
        
        applyFilters();
    });
}

// 3. MAP LOGIC
function initMap() {
    // Default center to Hanoi
    mapInstance = L.map('map-container').setView([21.0285, 105.8542], 13);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    }).addTo(mapInstance);
}

function updateMapMarkers(bars) {
    if (!mapInstance) return;
    
    // Clear old markers
    mapMarkers.forEach(m => mapInstance.removeLayer(m));
    mapMarkers = [];
    
    if (bars.length === 0) return;
    
    const bounds = L.latLngBounds();
    
    // Coordinates for Hanoi districts to generate realistic pin locations
    const districtCoords = {
        "hoàn kiếm": [21.0285, 105.8542],
        "tây hồ": [21.0625, 105.8152],
        "ba đình": [21.0355, 105.8282],
        "đống đa": [21.0125, 105.8252],
        "hai bà trưng": [21.0065, 105.8522],
        "cầu giấy": [21.0285, 105.7822],
        "long biên": [21.0455, 105.8752]
    };
    
    // Custom Gold Pulsing DivIcon
    const goldIcon = L.divIcon({
        className: 'custom-gold-marker',
        html: "<div class='gold-map-pin'></div>",
        iconSize: [16, 16],
        iconAnchor: [8, 8],
        popupAnchor: [0, -8]
    });
    
    bars.forEach((bar, idx) => {
        const dist = bar.district ? bar.district.toLowerCase().trim() : '';
        const baseCoords = districtCoords[dist] || [21.0285, 105.8542];
        
        // Add a deterministic offset so pins for the same district don't overlap completely
        const offsetLat = (Math.sin(idx) * 0.003);
        const offsetLng = (Math.cos(idx) * 0.003);
        
        const lat = baseCoords[0] + offsetLat;
        const lng = baseCoords[1] + offsetLng;
        
        const marker = L.marker([lat, lng], { icon: goldIcon }).addTo(mapInstance);
        
        // Custom popup content styled with premium card style
        const popupContent = `
            <div class="p-2 min-w-[180px]">
                <h4 class="font-cinzel text-gold font-bold text-sm mb-1">${bar.name}</h4>
                <p class="text-[10px] text-lounge-muted uppercase tracking-wider mb-2"><i class="fa-solid fa-martini-glass-citrus"></i> ${bar.style}</p>
                <p class="text-[11px] leading-relaxed text-lounge-text mb-2">${bar.address}, ${bar.district}</p>
                <div class="flex justify-between items-center text-[10px]">
                    <span class="text-gold font-bold">${bar.price_range}</span>
                    <span class="text-green-500"><i class="fa-solid fa-circle-check"></i> Active</span>
                </div>
            </div>
        `;
        
        marker.bindPopup(popupContent);
        mapMarkers.push(marker);
        bounds.extend([lat, lng]);
    });
    
    mapInstance.fitBounds(bounds, { padding: [30, 30], maxZoom: 14 });
}

// 4. CHAT WIDGET
function setupChatWidget() {
    btnSendChat.addEventListener('click', () => sendChatMessage());
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
    
    // Chat Session Selector
    if (chatSessionSelect) {
        chatSessionSelect.addEventListener('change', async (e) => {
            const selectedId = e.target.value;
            if (selectedId) {
                currentSessionId = selectedId;
                // Reset UI before loading
                chatBox.innerHTML = `
                    <div class="flex gap-4 max-w-[90%] fade-in">
                        <div class="w-10 h-10 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0 border border-gold border-opacity-30">
                            <i class="fa-solid fa-bell"></i>
                        </div>
                        <div class="bg-lounge-card p-4 rounded-2xl rounded-tl-none border border-lounge-border text-sm leading-relaxed shadow-lg">
                            ${currentLang === 'VI' ? 'Chào mừng trở lại. Bạn muốn tiếp tục câu chuyện hay khám phá điều mới?' : 'Welcome back. Would you like to continue our chat or discover something new?'}
                        </div>
                    </div>
                `;
                chatHistory = [];
                await loadSessionHistory(currentSessionId);
            }
        });
    }

    // Add New Chat & Clear Chat functionality
    const btnNewChat = document.getElementById('btn-new-chat');
    const btnClearChat = document.getElementById('btn-clear-chat');
    
    if (btnNewChat) {
        btnNewChat.addEventListener('click', async () => {
            // Reset UI
            chatBox.innerHTML = `
                <div class="flex gap-4 max-w-[90%] fade-in">
                    <div class="w-10 h-10 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0 border border-gold border-opacity-30">
                        <i class="fa-solid fa-bell"></i>
                    </div>
                    <div class="bg-lounge-card p-4 rounded-2xl rounded-tl-none border border-lounge-border text-sm leading-relaxed shadow-lg">
                        ${currentLang === 'VI' ? 'Chào quý khách. Tôi là AI Mixologist. Tôi có thể giúp gì cho ngài tối nay?' : 'Good evening. I am your AI Mixologist & Host. What are you in the mood for tonight?'}
                    </div>
                </div>
            `;
            chatHistory = [];
            await createNewSession();
        });
    }
    
    if (btnClearChat) {
        btnClearChat.addEventListener('click', () => {
            if(confirm(currentLang === 'VI' ? "Xóa lịch sử chat hiện tại?" : "Clear current chat history?")) {
                chatBox.innerHTML = `
                    <div class="flex gap-4 max-w-[90%] fade-in">
                        <div class="w-10 h-10 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0 border border-gold border-opacity-30">
                            <i class="fa-solid fa-bell"></i>
                        </div>
                        <div class="bg-lounge-card p-4 rounded-2xl rounded-tl-none border border-lounge-border text-sm leading-relaxed shadow-lg">
                            ${currentLang === 'VI' ? 'Lịch sử đã được xóa. Tôi có thể giúp gì tiếp theo?' : 'History cleared. How can I help you next?'}
                        </div>
                    </div>
                `;
                chatHistory = [];
            }
        });
    }
}

// 5. SESSIONS PERSISTENCE
function renderSessionSelect() {
    if (!chatSessionSelect) return;
    chatSessionSelect.innerHTML = '';
    sessions.forEach(session => {
        const option = document.createElement('option');
        option.value = session.id;
        option.className = "bg-lounge-dark text-gold";
        
        let title = session.title || "New Chat";
        // Convert to local time string if timestamp exists
        if (session.timestamp) {
            try {
                const date = new Date(session.timestamp);
                title = `${date.toLocaleDateString()} - ${title}`;
            } catch(e) {}
        }
        
        option.textContent = title;
        if (session.id === currentSessionId) {
            option.selected = true;
        }
        chatSessionSelect.appendChild(option);
    });
}

async function fetchSession() {
    try {
        const response = await fetch(`/api/sessions?role=guest`);
        const data = await response.json();
        sessions = data.sessions || [];
        
        if (sessions.length === 0) {
            await createNewSession();
        } else {
            currentSessionId = sessions[0].id;
            renderSessionSelect();
            await loadSessionHistory(currentSessionId);
        }
    } catch (err) {
        console.error("Error fetching sessions:", err);
    }
}

async function createNewSession() {
    try {
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role: 'guest', user_id: CLIENT_USER_ID })
        });
        const session = await response.json();
        currentSessionId = session.id;
        sessions.unshift(session);
        renderSessionSelect();
        await loadSessionHistory(currentSessionId);
    } catch (err) {
        console.error("Error creating session:", err);
    }
}

async function loadSessionHistory(sessionId) {
    try {
        const response = await fetch(`/api/sessions/${sessionId}`);
        const session = await response.json();
        // Skip Welcome Message appending if we already have history to avoid duplicates
        chatHistory = session.chat_history || [];
        
        if (chatHistory.length > 0) {
            // Keep the hardcoded welcome message, but add history below it
            chatHistory.forEach(msg => {
                appendMessageToUI(msg.role, msg.parts[0], false);
            });
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    } catch (err) {
        console.error("Error loading session:", err);
    }
}

function appendMessageToUI(role, text, scrollToBottom = true, stream = false) {
    const bubble = document.createElement('div');
    
    let spiritTag = 'drink';
    const lowerText = text.toLowerCase();
    if (lowerText.includes('whiskey') || lowerText.includes('bourbon') || lowerText.includes('scotch')) spiritTag = 'whiskey';
    else if (lowerText.includes('gin')) spiritTag = 'gin';
    else if (lowerText.includes('rum')) spiritTag = 'rum';
    else if (lowerText.includes('tequila')) spiritTag = 'tequila';
    else if (lowerText.includes('vodka')) spiritTag = 'vodka';

    if (role === 'user') {
        bubble.className = "flex gap-4 max-w-[90%] ml-auto justify-end fade-in mt-4";
        bubble.innerHTML = `
            <div class="bg-gold bg-opacity-10 p-4 rounded-2xl rounded-tr-none border border-gold border-opacity-30 text-sm leading-relaxed shadow-lg">
                ${text}
            </div>
        `;
        chatBox.appendChild(bubble);
        if (scrollToBottom) chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });
    } else {
        bubble.className = "flex gap-4 max-w-[90%] fade-in mt-4";
        bubble.innerHTML = `
            <div class="w-10 h-10 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0 border border-gold border-opacity-30">
                <i class="fa-solid fa-bell"></i>
            </div>
            <div class="bg-lounge-card p-4 rounded-2xl rounded-tl-none border border-lounge-border text-sm leading-relaxed shadow-lg message-content">
            </div>
        `;
        chatBox.appendChild(bubble);
        const contentDiv = bubble.querySelector('.message-content');
        
        if (stream) {
            let i = 0;
            const words = text.split(/(\s+)/);
            const cursor = document.createElement('span');
            cursor.className = 'typing-cursor';
            contentDiv.appendChild(cursor);
            
            let accumulatedText = '';
            
            function typeNextWord() {
                if (i < words.length) {
                    accumulatedText += words[i];
                    i++;
                    
                    contentDiv.innerHTML = parseMarkdown(accumulatedText, spiritTag);
                    contentDiv.appendChild(cursor);
                    
                    if (scrollToBottom) chatBox.scrollTop = chatBox.scrollHeight;
                    setTimeout(typeNextWord, 10 + Math.random() * 20);
                } else {
                    cursor.remove();
                    contentDiv.innerHTML = parseMarkdown(text, spiritTag);
                    if (scrollToBottom) chatBox.scrollTop = chatBox.scrollHeight;
                }
            }
            typeNextWord();
        } else {
            contentDiv.innerHTML = parseMarkdown(text, spiritTag);
            if (scrollToBottom) chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });
        }
    }
}

// 6. CHAT SENDING
async function sendChatMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    
    chatInput.value = '';
    appendMessageToUI('user', message);
    chatHistory.push({ role: "user", parts: [message] });
    
    // Loading Indicator
    const typingBubble = document.createElement('div');
    typingBubble.className = "flex gap-4 max-w-[90%] fade-in mt-4";
    typingBubble.id = "typing-indicator";
    typingBubble.innerHTML = `
        <div class="w-10 h-10 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0 border border-gold border-opacity-30">
            <i class="fa-solid fa-circle-notch fa-spin"></i>
        </div>
        <div class="bg-lounge-card p-4 rounded-2xl rounded-tl-none border border-lounge-border shadow-lg">
            Generating...
        </div>
    `;
    chatBox.appendChild(typingBubble);
    chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                chat_history: chatHistory.slice(0, -1),
                role: 'guest',
                session_id: currentSessionId,
                user_id: CLIENT_USER_ID
            })
        });
        const data = await response.json();
        document.getElementById("typing-indicator")?.remove();
        
        if (response.ok && !data.error) {
            const responseText = data.message || "No response generated.";
            appendMessageToUI('model', responseText, true, true);
            chatHistory.push({ role: "model", parts: [responseText] });
            smartFilterGrid(responseText);
            
            // Refresh title quietly
            fetch(`/api/sessions?role=guest`)
                .then(r => r.json())
                .then(d => {
                    sessions = d.sessions || [];
                    renderSessionSelect();
                });
        } else {
            throw new Error(data.error || "Failed to query AI.");
        }
    } catch (err) {
        document.getElementById("typing-indicator")?.remove();
        appendMessageToUI('model', `**Error:** ${err.message}`);
    }
}

// 7. VISUAL EXPLORER (DATABASE CARDS)
async function fetchCocktailsDatabase() {
    try {
        const response = await fetch(`/api/cocktails?search=`);
        const data = await response.json();
        cocktailsData = data.cocktails || [];
        if (activeTab === 'cocktails') renderGrid(cocktailsData, 'cocktails');
    } catch (err) {
        console.error("Error loading cocktails database.");
    }
}

async function fetchBarsDatabase() {
    try {
        const response = await fetch(`/api/bars`);
        const data = await response.json();
        barsData = data.bars || [];
        if (activeTab === 'bars') renderGrid(barsData, 'bars');
    } catch (err) {
        console.error("Error loading bars database.");
    }
}

function renderGrid(items, type) {
    mainGrid.innerHTML = '';
    if (items.length === 0) {
        mainGrid.innerHTML = `<div class="col-span-full text-center py-20 text-lounge-muted">No items matched your filters.</div>`;
        if (type === 'bars') updateMapMarkers([]);
        return;
    }
    
    items.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = "bg-lounge-card rounded-2xl overflow-hidden border border-lounge-border shadow-lg group hover:border-gold transition-all duration-300 flex flex-col h-full fade-in cursor-pointer";
        card.style.animationDelay = `${(index % 10) * 50}ms`;

        // Determine base spirit for fallback images
        let gridSpirit = 'drink';
        if (item.ingredients) {
            const ingStr = Array.isArray(item.ingredients) ? item.ingredients.join(' ').toLowerCase() : String(item.ingredients).toLowerCase();
            if (ingStr.includes('whiskey') || ingStr.includes('bourbon') || ingStr.includes('scotch')) gridSpirit = 'whiskey';
            else if (ingStr.includes('gin')) gridSpirit = 'gin';
            else if (ingStr.includes('rum')) gridSpirit = 'rum';
            else if (ingStr.includes('tequila')) gridSpirit = 'tequila';
            else if (ingStr.includes('vodka')) gridSpirit = 'vodka';
        }

        if (type === 'cocktails') {
            let imageHtml = '';
            if (item.image_url && item.image_url.trim() !== '') {
                imageHtml = `<img src="${item.image_url}" onerror="this.onerror=null; this.src='https://loremflickr.com/600/600/cocktail,${gridSpirit}';" alt="${item.name}" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110">`;
            } else {
                imageHtml = `<div class="w-full h-full bg-gradient-to-br from-zinc-900 to-zinc-800 flex items-center justify-center transition-transform duration-700 group-hover:scale-110"><i class="fa-solid fa-martini-glass-citrus text-gold opacity-50 text-4xl"></i></div>`;
            }
            
            card.innerHTML = `
                <div class="h-40 relative overflow-hidden pointer-events-none">
                    ${imageHtml}
                </div>
                <div class="p-4 flex flex-col flex-grow pointer-events-none">
                    <h3 class="font-cinzel font-bold text-gold text-base mb-1 truncate">${item.name}</h3>
                    <p class="text-[10px] text-lounge-muted mb-2 uppercase tracking-wide"><i class="fa-solid fa-glass-water"></i> ${item.category || 'Cocktail'}</p>
                    <div class="flex flex-wrap gap-1 mt-auto">
                        ${(item.flavor_profile || 'Balanced').split(',').slice(0, 2).map(f => `<span class="text-[10px] bg-lounge-darkest px-2 py-1 rounded text-lounge-muted border border-lounge-border whitespace-nowrap">${f.trim()}</span>`).join('')}
                    </div>
                </div>
            `;
            card.addEventListener('click', () => openDetailModal(item, 'cocktails'));
            
        } else {
            // Display beautiful location-themed images for bars too using loremflickr
            const imageHtml = `<img src="https://loremflickr.com/600/400/lounge,bar,vintage?random=${index}" onerror="this.onerror=null; this.src='https://loremflickr.com/600/400/lounge,bar';" alt="${item.name}" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110">`;

            card.innerHTML = `
                <div class="h-32 relative overflow-hidden pointer-events-none border-b border-lounge-border">
                    ${imageHtml}
                </div>
                <div class="p-4 flex flex-col flex-grow pointer-events-none">
                    <h3 class="font-cinzel font-bold text-gold text-base mb-1 truncate">${item.name}</h3>
                    <p class="text-[10px] text-lounge-muted mb-2 uppercase tracking-wide"><i class="fa-solid fa-location-dot"></i> ${item.district}, ${item.city}</p>
                    <p class="text-[10px] text-lounge-text line-clamp-2 italic flex-grow">${item.vibe_description}</p>
                </div>
            `;
            card.addEventListener('click', () => openDetailModal(item, 'bars'));
        }
        mainGrid.appendChild(card);
    });
    
    if (type === 'bars') {
        updateMapMarkers(items);
    }
}

// 8. FILTERS AND SMART ROUTING
let semanticSearchTimeout = null;

function setupFilters() {
    // Toggle filter panel visibility
    if (btnToggleFilters) {
        btnToggleFilters.addEventListener('click', () => {
            if (filterPanel) filterPanel.classList.toggle('hidden');
        });
    }
    
    // Setup chip click handlers
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            chip.classList.toggle('active');
            applyFilters();
        });
    });
    
    // Semantic search with debounce
    if (gridSearchInput) {
        gridSearchInput.addEventListener('input', () => {
            const query = gridSearchInput.value.trim();
            if (semanticSearchTimeout) clearTimeout(semanticSearchTimeout);
            
            if (query.length === 0) {
                applyFilters();
                return;
            }
            
            semanticSearchTimeout = setTimeout(async () => {
                if (activeTab === 'cocktails' && query.length >= 2) {
                    try {
                        const response = await fetch(`/api/semantic_search?q=${encodeURIComponent(query)}`);
                        const data = await response.json();
                        if (data.cocktails && data.cocktails.length > 0) {
                            renderGrid(data.cocktails, 'cocktails');
                            return;
                        }
                    } catch(e) {
                        console.error("Semantic search error:", e);
                    }
                }
                applyFilters();
            }, 500);
        });
    }
}

function getActiveChipValues(group, chipClass) {
    const active = document.querySelectorAll(`.${chipClass}.active[data-group="${group}"]`);
    return Array.from(active).map(c => c.dataset.value.toLowerCase());
}

function applyFilters() {
    const searchTerm = gridSearchInput ? gridSearchInput.value.toLowerCase().trim() : '';
    
    if (activeTab === 'cocktails') {
        const spirits = getActiveChipValues('spirit', 'cocktail-chip');
        const flavors = getActiveChipValues('flavor', 'cocktail-chip');
        const categories = getActiveChipValues('category', 'cocktail-chip');
        const abvs = getActiveChipValues('abv', 'cocktail-chip');
        
        const filtered = cocktailsData.filter(item => {
            const matchesSearch = searchTerm === '' || 
                item.name.toLowerCase().includes(searchTerm) || 
                (item.category && item.category.toLowerCase().includes(searchTerm));
            
            const ingredientsStr = Array.isArray(item.ingredients) ? item.ingredients.join(' ').toLowerCase() : (item.ingredients || '').toLowerCase();
            const matchesSpirit = spirits.length === 0 || spirits.some(s => ingredientsStr.includes(s));
            
            const flavorStr = (item.flavor_profile || '').toLowerCase();
            const matchesFlavor = flavors.length === 0 || flavors.some(f => flavorStr.includes(f));
            
            const catStr = (item.category || '').toLowerCase();
            const matchesCategory = categories.length === 0 || categories.some(c => catStr.includes(c));
            
            const abvStr = (item.abv_category || '').toLowerCase();
            const matchesAbv = abvs.length === 0 || abvs.some(a => abvStr.includes(a));
            
            return matchesSearch && matchesSpirit && matchesFlavor && matchesCategory && matchesAbv;
        });
        renderGrid(filtered, 'cocktails');
    } else {
        const cities = getActiveChipValues('city', 'bar-chip');
        const districts = getActiveChipValues('district', 'bar-chip');
        const styles = getActiveChipValues('style', 'bar-chip');
        const prices = getActiveChipValues('price', 'bar-chip');
        
        const filtered = barsData.filter(item => {
            const matchesSearch = searchTerm === '' || 
                item.name.toLowerCase().includes(searchTerm) || 
                item.district.toLowerCase().includes(searchTerm);
            
            const matchesCity = cities.length === 0 || cities.some(c => item.city.toLowerCase().includes(c));
            const matchesDistrict = districts.length === 0 || districts.some(d => item.district.toLowerCase().includes(d));
            const matchesStyle = styles.length === 0 || styles.some(s => item.style.toLowerCase().includes(s));
            const matchesPrice = prices.length === 0 || prices.some(p => item.price_range === p || item.price_range.toLowerCase() === p);
            
            return matchesSearch && matchesCity && matchesDistrict && matchesStyle && matchesPrice;
        });
        renderGrid(filtered, 'bars');
    }
}

function smartFilterGrid(aiResponse) {
    const text = aiResponse.toLowerCase();
    
    // Check bars — multiple matches
    const matchedBars = barsData.filter(b => text.includes(b.name.toLowerCase()));
    if (matchedBars.length > 0) {
        if (activeTab !== 'bars') document.getElementById('tab-explore-bars').click();
        if (gridSearchInput) gridSearchInput.value = matchedBars[0].name;
        renderGrid(matchedBars, 'bars');
        if (window.innerWidth < 1024) discoveryPanel.classList.remove('translate-x-full');
        return;
    }
    
    // Check drinks — multiple matches
    const matchedDrinks = cocktailsData.filter(d => text.includes(d.name.toLowerCase()));
    if (matchedDrinks.length > 0) {
        if (activeTab !== 'cocktails') document.getElementById('tab-explore-cocktails').click();
        if (gridSearchInput) gridSearchInput.value = matchedDrinks[0].name;
        renderGrid(matchedDrinks, 'cocktails');
        if (window.innerWidth < 1024) discoveryPanel.classList.remove('translate-x-full');
    }
}

// 9. MODALS & UTILS
btnCloseDetailModal.addEventListener('click', () => {
    detailModal.classList.add('hidden');
    detailModal.classList.remove('flex');
});

function openDetailModal(item, type) {
    // Determine base spirit for fallback images
    let detailSpirit = 'drink';
    if (item.ingredients) {
        const ingStr = Array.isArray(item.ingredients) ? item.ingredients.join(' ').toLowerCase() : String(item.ingredients).toLowerCase();
        if (ingStr.includes('whiskey') || ingStr.includes('bourbon') || ingStr.includes('scotch')) detailSpirit = 'whiskey';
        else if (ingStr.includes('gin')) detailSpirit = 'gin';
        else if (ingStr.includes('rum')) detailSpirit = 'rum';
        else if (ingStr.includes('tequila')) detailSpirit = 'tequila';
        else if (ingStr.includes('vodka')) detailSpirit = 'vodka';
    }

    document.getElementById('detail-modal-image-container').innerHTML = type === 'cocktails' 
        ? (item.image_url ? `<img src="${item.image_url}" onerror="this.onerror=null; this.src='https://loremflickr.com/600/600/cocktail,${detailSpirit}';" class="w-full h-full object-cover">` : `<div class="w-full h-full bg-gradient-to-br from-zinc-900 to-zinc-800 flex items-center justify-center"><i class="fa-solid fa-martini-glass-citrus text-gold text-6xl opacity-50"></i></div>`)
        : `<div class="w-full h-full bg-gradient-to-br from-zinc-900 to-zinc-800 flex items-center justify-center"><i class="fa-solid fa-compass text-gold text-6xl opacity-50"></i></div>`;
        
    document.getElementById('detail-modal-title').innerText = item.name;
    
    if (type === 'cocktails') {
        const subtitleParts = [];
        if (item.category) subtitleParts.push(item.category);
        if (item.abv_category) subtitleParts.push(item.abv_category);
        if (item.flavor_profile) subtitleParts.push(item.flavor_profile);
        document.getElementById('detail-modal-subtitle').innerHTML = `<i class="fa-solid fa-glass-water"></i> ${subtitleParts.join(' · ')}`;
        
        document.getElementById('detail-modal-description').innerHTML = parseMarkdown(item.meaning_and_history || '', detailSpirit);
        
        let ingredientsHtml = '';
        if (item.ingredients && Array.isArray(item.ingredients) && item.ingredients.length > 0) {
            const measures = item.ingredientMeasures || [];
            ingredientsHtml = `
                <h4 class="font-cinzel text-gold text-lg border-b border-lounge-border pb-1 mb-3"><i class="fa-solid fa-flask mr-2"></i>Ingredients</h4>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-6">
                    ${item.ingredients.map((ing, i) => {
                        const measure = measures[i] || '';
                        return `<div class="flex items-center gap-2 bg-lounge-darkest p-2 rounded-lg border border-lounge-border text-sm">
                            <span class="text-gold font-bold text-xs whitespace-nowrap">${measure}</span>
                            <span class="text-lounge-text">${ing}</span>
                        </div>`;
                    }).join('')}
                </div>`;
        }
        
        let instructionsHtml = '';
        if (item.instructions) {
            instructionsHtml = `
                <h4 class="font-cinzel text-gold text-lg border-b border-lounge-border pb-1 mb-2"><i class="fa-solid fa-list-ol mr-2"></i>Instructions</h4>
                <div class="text-sm bg-lounge-darkest p-4 rounded-xl border border-lounge-border leading-relaxed">${parseMarkdown(item.instructions, detailSpirit)}</div>`;
        }
        
        let glasswareHtml = '';
        if (item.glassware_recommendation) {
            glasswareHtml = `
                <div class="mt-4 bg-gold bg-opacity-10 p-3 rounded-xl border border-gold border-opacity-30 text-sm">
                    <span class="text-gold font-bold"><i class="fa-solid fa-wine-glass mr-1"></i> Glassware:</span> 
                    <span class="text-lounge-text">${item.glassware_recommendation}</span>
                </div>`;
        }
        
        document.getElementById('detail-modal-content-area').innerHTML = ingredientsHtml + instructionsHtml + glasswareHtml;
    } else {
        document.getElementById('detail-modal-subtitle').innerHTML = `<i class="fa-solid fa-location-dot"></i> ${item.address}`;
        document.getElementById('detail-modal-description').innerHTML = item.vibe_description || '';
        
        let tagsHtml = '';
        if (item.style) tagsHtml += `<span class="text-[10px] bg-lounge-darkest px-2 py-1 rounded text-gold border border-gold border-opacity-30">${item.style}</span>`;
        if (item.price_range) tagsHtml += `<span class="text-[10px] bg-lounge-darkest px-2 py-1 rounded text-lounge-muted border border-lounge-border">${item.price_range}</span>`;
        
        document.getElementById('detail-modal-content-area').innerHTML = `
            <div class="flex gap-2 mb-4">${tagsHtml}</div>
            <div class="bg-gold bg-opacity-10 p-4 rounded-xl border border-gold border-opacity-30">
                <h4 class="font-cinzel text-gold text-sm uppercase tracking-wider mb-2">Signature Drink</h4>
                <p class="text-sm text-gold font-bold">${item.signature_cocktail}</p>
            </div>
            <a href="https://grab.com" target="_blank" class="block w-full text-center bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-xl mt-4 transition-colors">
                <i class="fa-solid fa-car mr-2"></i> Book a Ride to Venue
            </a>`;
    }
    
    detailModal.classList.remove('hidden');
    detailModal.classList.add('flex');
}

function parseMarkdown(text, spiritTag = 'drink') {
    let parsed = text;
    // Handle inline images generated by Generative Hack
    parsed = parsed.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, `<img src="$2" alt="$1" onerror="this.onerror=null; this.src='https://loremflickr.com/600/600/cocktail,${spiritTag}';" class="w-full rounded-xl my-4 border border-lounge-border shadow-lg">`);
    parsed = parsed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    parsed = parsed.split('\n').map(line => {
        const trimmed = line.trim();
        if (trimmed.startsWith('*') && !trimmed.startsWith('***')) return `<li class="ml-4 list-disc text-sm">${trimmed.substring(1).trim()}</li>`;
        if (trimmed.startsWith('-')) return `<li class="ml-4 list-disc text-sm">${trimmed.substring(1).trim()}</li>`;
        if (trimmed.startsWith('###')) return `<h4 class="font-bold text-gold text-sm mt-3 mb-1 uppercase">${trimmed.substring(3).trim()}</h4>`;
        return line;
    }).join('\n');
    parsed = parsed.replace(/\n/g, '<br/>');
    return parsed;
}
