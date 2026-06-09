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

const tabExploreCocktails = document.getElementById('tab-explore-cocktails');
const tabExploreBars = document.getElementById('tab-explore-bars');
const mainGrid = document.getElementById('main-grid');
const mapContainer = document.getElementById('map-container');

// Mobile Panel Toggle
const btnTogglePanel = document.getElementById('btn-toggle-panel');
const btnClosePanel = document.getElementById('btn-close-panel');
const discoveryPanel = document.getElementById('discovery-panel');

// Filters
const filterFlavor = document.getElementById('filter-flavor');
const filterCity = document.getElementById('filter-city');

// Detail Modal
const detailModal = document.getElementById('detail-modal');
const btnCloseDetailModal = document.getElementById('btn-close-detail-modal');

document.addEventListener('DOMContentLoaded', () => {
    setupTabSwitcher();
    setupChatWidget();
    setupFilters();
    setupMobilePanel();
    
    // Initial fetch
    fetchSession();
    fetchCocktailsDatabase();
    fetchBarsDatabase();
});

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
        
        filterFlavor.classList.remove('hidden');
        filterCity.classList.add('hidden');
        mapContainer.classList.add('hidden');
        
        applyFilters();
    });

    tabExploreBars.addEventListener('click', () => {
        activeTab = 'bars';
        tabExploreBars.className = "py-2 px-4 rounded-lg bg-lounge-dark border border-gold text-gold font-bold text-sm shadow-sm transition-all";
        tabExploreCocktails.className = "py-2 px-4 rounded-lg bg-transparent border border-transparent text-lounge-muted font-bold text-sm hover:text-lounge-text transition-all";
        
        filterFlavor.classList.add('hidden');
        filterCity.classList.remove('hidden');
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
    // Default center to Vietnam
    mapInstance = L.map('map-container').setView([16.047079, 108.206230], 5);
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
    
    bars.forEach(bar => {
        // Very basic coordinate mocking based on city if actual coords don't exist
        // In a real app, `bar` should have lat/lng from the database.
        // We will fake some coordinates for demonstration.
        let lat = bar.city.includes('Ho Chi Minh') ? 10.7769 + (Math.random()-0.5)*0.05 : 21.0285 + (Math.random()-0.5)*0.05;
        let lng = bar.city.includes('Ho Chi Minh') ? 106.7009 + (Math.random()-0.5)*0.05 : 105.8542 + (Math.random()-0.5)*0.05;
        
        const marker = L.marker([lat, lng]).addTo(mapInstance);
        marker.bindPopup(`<b>${bar.name}</b><br>${bar.district}, ${bar.city}`);
        mapMarkers.push(marker);
        bounds.extend([lat, lng]);
    });
    
    mapInstance.fitBounds(bounds, { padding: [30, 30] });
}

// 4. CHAT WIDGET
function setupChatWidget() {
    btnSendChat.addEventListener('click', () => sendChatMessage());
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
}

// 5. SESSIONS PERSISTENCE
async function fetchSession() {
    try {
        const response = await fetch(`/api/sessions?role=guest&user_id=${CLIENT_USER_ID}`);
        const data = await response.json();
        sessions = data.sessions || [];
        
        if (sessions.length === 0) {
            await createNewSession();
        } else {
            currentSessionId = sessions[0].id;
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

function appendMessageToUI(role, text, scrollToBottom = true) {
    const bubble = document.createElement('div');
    if (role === 'user') {
        bubble.className = "flex gap-4 max-w-[90%] ml-auto justify-end fade-in mt-4";
        bubble.innerHTML = `
            <div class="bg-gold bg-opacity-10 p-4 rounded-2xl rounded-tr-none border border-gold border-opacity-30 text-sm leading-relaxed shadow-lg">
                ${text}
            </div>
        `;
    } else {
        bubble.className = "flex gap-4 max-w-[90%] fade-in mt-4";
        bubble.innerHTML = `
            <div class="w-10 h-10 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0 border border-gold border-opacity-30">
                <i class="fa-solid fa-bell"></i>
            </div>
            <div class="bg-lounge-card p-4 rounded-2xl rounded-tl-none border border-lounge-border text-sm leading-relaxed shadow-lg">
                ${parseMarkdown(text)}
            </div>
        `;
    }
    chatBox.appendChild(bubble);
    if (scrollToBottom) chatBox.scrollTop = chatBox.scrollHeight;
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
    chatBox.scrollTop = chatBox.scrollHeight;
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                chat_history: chatHistory.slice(0, -1),
                role: 'guest', // ignored by backend anyway
                session_id: currentSessionId,
                user_id: CLIENT_USER_ID
            })
        });
        const data = await response.json();
        document.getElementById("typing-indicator")?.remove();
        
        if (response.ok && !data.error) {
            const responseText = data.message || "No response generated.";
            appendMessageToUI('model', responseText);
            chatHistory.push({ role: "model", parts: [responseText] });
            smartFilterGrid(responseText);
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

        if (type === 'cocktails') {
            let imageHtml = '';
            if (item.image_url && item.image_url.trim() !== '') {
                imageHtml = `<img src="${item.image_url}" alt="${item.name}" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110">`;
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
            const imageHtml = `<div class="w-full h-full bg-gradient-to-br from-zinc-900 to-zinc-800 flex items-center justify-center transition-transform duration-700 group-hover:scale-110"><i class="fa-solid fa-compass text-gold opacity-50 text-4xl"></i></div>`;

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
function setupFilters() {
    filterFlavor.addEventListener('change', applyFilters);
    filterCity.addEventListener('change', applyFilters);
}

function applyFilters() {
    if (activeTab === 'cocktails') {
        const flavor = filterFlavor.value.toLowerCase();
        const filtered = cocktailsData.filter(item => {
            return flavor === '' || (item.flavor_profile && item.flavor_profile.toLowerCase().includes(flavor));
        });
        renderGrid(filtered, 'cocktails');
    } else {
        const city = filterCity.value.toLowerCase();
        const filtered = barsData.filter(item => {
            return city === '' || item.city.toLowerCase() === city;
        });
        renderGrid(filtered, 'bars');
    }
}

function smartFilterGrid(aiResponse) {
    const text = aiResponse.toLowerCase();
    let foundBar = false;
    
    // Check bars
    const matchedBars = barsData.filter(b => text.includes(b.name.toLowerCase()));
    if (matchedBars.length > 0) {
        if (activeTab !== 'bars') document.getElementById('tab-explore-bars').click();
        renderGrid(matchedBars, 'bars');
        foundBar = true;
    }
    
    if (!foundBar) {
        const matchedDrinks = cocktailsData.filter(d => text.includes(d.name.toLowerCase()));
        if (matchedDrinks.length > 0) {
            if (activeTab !== 'cocktails') document.getElementById('tab-explore-cocktails').click();
            renderGrid(matchedDrinks, 'cocktails');
        }
    }
    
    // Auto open panel on mobile
    if (window.innerWidth < 1024) {
        discoveryPanel.classList.remove('translate-x-full');
    }
}

// 9. MODALS & UTILS
btnCloseDetailModal.addEventListener('click', () => {
    detailModal.classList.add('hidden');
    detailModal.classList.remove('flex');
});

function openDetailModal(item, type) {
    document.getElementById('detail-modal-image-container').innerHTML = type === 'cocktails' 
        ? (item.image_url ? `<img src="${item.image_url}" class="w-full h-full object-cover">` : `<div class="w-full h-full bg-gradient-to-br from-zinc-900 to-zinc-800 flex items-center justify-center"><i class="fa-solid fa-martini-glass-citrus text-gold text-6xl opacity-50"></i></div>`)
        : `<div class="w-full h-full bg-gradient-to-br from-zinc-900 to-zinc-800 flex items-center justify-center"><i class="fa-solid fa-compass text-gold text-6xl opacity-50"></i></div>`;
        
    document.getElementById('detail-modal-title').innerText = item.name;
    
    if (type === 'cocktails') {
        document.getElementById('detail-modal-subtitle').innerHTML = `<i class="fa-solid fa-glass-water"></i> ${item.category}`;
        document.getElementById('detail-modal-description').innerHTML = parseMarkdown(item.meaning_and_history || '');
        document.getElementById('detail-modal-content-area').innerHTML = `
            <h4 class="font-cinzel text-gold text-lg border-b border-lounge-border pb-1 mb-2">Instructions</h4>
            <div class="text-sm bg-lounge-darkest p-4 rounded-xl border border-lounge-border">${parseMarkdown(item.instructions || '')}</div>
        `;
    } else {
        document.getElementById('detail-modal-subtitle').innerHTML = `<i class="fa-solid fa-location-dot"></i> ${item.address}`;
        document.getElementById('detail-modal-description').innerHTML = item.vibe_description || '';
        document.getElementById('detail-modal-content-area').innerHTML = `
            <div class="bg-gold bg-opacity-10 p-4 rounded-xl border border-gold border-opacity-30">
                <h4 class="font-cinzel text-gold text-sm uppercase tracking-wider mb-2">Signature Drink</h4>
                <p class="text-sm text-gold font-bold">${item.signature_cocktail}</p>
            </div>
            <a href="https://grab.com" target="_blank" class="block w-full text-center bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-xl mt-4 transition-colors">
                <i class="fa-solid fa-car mr-2"></i> Book a Ride to Venue
            </a>
        `;
    }
    
    detailModal.classList.remove('hidden');
    detailModal.classList.add('flex');
}

function parseMarkdown(text) {
    let parsed = text;
    // Handle inline images generated by Generative Hack
    parsed = parsed.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="w-full rounded-xl my-4 border border-lounge-border shadow-lg">');
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
