// Application State
let activeRole = 'guest'; // 'guest' or 'bartender'
let activeTab = 'cocktails'; // 'cocktails' or 'bars'
let currentSessionId = '';
let sessions = [];
let chatHistory = [];
let cocktailsData = [];
let barsData = [];
let isChatOpen = false;

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
const btnGuestMode = document.getElementById('btn-guest-mode');
const btnBartenderMode = document.getElementById('btn-bartender-mode');
const btnToggleChat = document.getElementById('btn-toggle-chat');
const btnCloseChat = document.getElementById('btn-close-chat');
const chatDrawer = document.getElementById('chat-drawer');
const chatBox = document.getElementById('chat-box');
const chatInput = document.getElementById('chat-input');
const btnSendChat = document.getElementById('btn-send-chat');

const chatTitle = document.getElementById('chat-title');
const chatSubtitle = document.getElementById('chat-subtitle');
const chatIcon = document.getElementById('chat-icon');

// Tabs & Grid
const tabExploreCocktails = document.getElementById('tab-explore-cocktails');
const tabExploreBars = document.getElementById('tab-explore-bars');
const mainGrid = document.getElementById('main-grid');

// Filters
const searchInput = document.getElementById('main-search-input');
const filterFlavor = document.getElementById('filter-flavor');
const filterAbv = document.getElementById('filter-abv');
const filterCity = document.getElementById('filter-city');
const filterStyle = document.getElementById('filter-style');
const filterPrice = document.getElementById('filter-price');

const cocktailFilters = document.querySelectorAll('.cocktail-filter');
const barFilters = document.querySelectorAll('.bar-filter');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    setupRoleSwitcher();
    setupTabSwitcher();
    setupChatWidget();
    setupFilters();
    
    // Initial fetch to load sessions and cocktail list
    fetchSession();
    fetchCocktailsDatabase();
    fetchBarsDatabase();
});

// 1. ROLE SWITCHER
function setupRoleSwitcher() {
    btnGuestMode.addEventListener('click', () => {
        if (activeRole === 'guest') return;
        activeRole = 'guest';
        btnGuestMode.className = "px-4 py-2 rounded-full font-semibold text-xs md:text-sm transition-all duration-300 flex items-center gap-2 bg-gold text-lounge-darkest shadow-md";
        btnBartenderMode.className = "px-4 py-2 rounded-full font-semibold text-xs md:text-sm transition-all duration-300 flex items-center gap-2 text-lounge-muted hover:text-lounge-text";
        updateChatPersona();
        fetchSession();
    });

    btnBartenderMode.addEventListener('click', () => {
        if (activeRole === 'bartender') return;
        activeRole = 'bartender';
        btnBartenderMode.className = "px-4 py-2 rounded-full font-semibold text-xs md:text-sm transition-all duration-300 flex items-center gap-2 bg-gold text-lounge-darkest shadow-md";
        btnGuestMode.className = "px-4 py-2 rounded-full font-semibold text-xs md:text-sm transition-all duration-300 flex items-center gap-2 text-lounge-muted hover:text-lounge-text";
        updateChatPersona();
        fetchSession();
    });
}

function updateChatPersona() {
    if (activeRole === 'guest') {
        chatTitle.innerText = "Guest Concierge";
        chatSubtitle.innerText = "AI Lounge Host";
        chatIcon.className = "fa-solid fa-bell";
    } else {
        chatTitle.innerText = "Master Bartender";
        chatSubtitle.innerText = "Technical Expert";
        chatIcon.className = "fa-solid fa-hat-cowboy-side";
    }
}

// 1.5 TAB SWITCHER
function setupTabSwitcher() {
    tabExploreCocktails.addEventListener('click', () => {
        activeTab = 'cocktails';
        tabExploreCocktails.className = "flex-1 py-3 text-center border-b-2 border-gold font-bold text-sm text-gold transition-colors";
        tabExploreBars.className = "flex-1 py-3 text-center border-b-2 border-transparent font-semibold text-sm text-lounge-muted hover:text-lounge-text transition-colors";
        
        // Toggle filters
        cocktailFilters.forEach(f => f.classList.remove('hidden'));
        barFilters.forEach(f => f.classList.add('hidden'));
        searchInput.placeholder = "Search drinks...";
        
        applyFilters();
    });

    tabExploreBars.addEventListener('click', () => {
        activeTab = 'bars';
        tabExploreBars.className = "flex-1 py-3 text-center border-b-2 border-gold font-bold text-sm text-gold transition-colors";
        tabExploreCocktails.className = "flex-1 py-3 text-center border-b-2 border-transparent font-semibold text-sm text-lounge-muted hover:text-lounge-text transition-colors";
        
        // Toggle filters
        cocktailFilters.forEach(f => f.classList.add('hidden'));
        barFilters.forEach(f => f.classList.remove('hidden'));
        searchInput.placeholder = "Search venues or cities...";
        
        applyFilters();
    });
}

// 2. CHAT WIDGET
function setupChatWidget() {
    btnToggleChat.addEventListener('click', () => {
        isChatOpen = !isChatOpen;
        if (isChatOpen) {
            chatDrawer.classList.remove('translate-y-8', 'opacity-0', 'pointer-events-none');
            chatDrawer.classList.add('translate-y-0', 'opacity-100');
            btnToggleChat.innerHTML = '<i class="fa-solid fa-xmark"></i>';
            chatInput.focus();
        } else {
            chatDrawer.classList.add('translate-y-8', 'opacity-0', 'pointer-events-none');
            chatDrawer.classList.remove('translate-y-0', 'opacity-100');
            btnToggleChat.innerHTML = '<i class="fa-solid fa-message"></i>';
        }
    });

    btnCloseChat.addEventListener('click', () => {
        isChatOpen = false;
        chatDrawer.classList.add('translate-y-8', 'opacity-0', 'pointer-events-none');
        chatDrawer.classList.remove('translate-y-0', 'opacity-100');
        btnToggleChat.innerHTML = '<i class="fa-solid fa-message"></i>';
    });

    btnSendChat.addEventListener('click', () => sendChatMessage());
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
}

// 3. SESSIONS PERSISTENCE
async function fetchSession() {
    try {
        const response = await fetch(`/api/sessions?role=${activeRole}&user_id=${CLIENT_USER_ID}`);
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
            body: JSON.stringify({ role: activeRole, user_id: CLIENT_USER_ID })
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
        chatBox.innerHTML = '';
        chatHistory = session.chat_history || [];
        
        if (chatHistory.length === 0) {
            const welcomeBubble = document.createElement('div');
            welcomeBubble.className = "flex gap-3 max-w-[85%] fade-in";
            const text = activeRole === 'guest' 
                ? "Good evening. Welcome to the **AI Lounge**. Tell me, what kind of flavor profile are you craving tonight, or what kind of venue are you looking for?"
                : "Hello. I am the **Master Bartender**. I can help you compile classic recipes, troubleshoot flavor profiles, and calculate precise ABV rates.";
            
            welcomeBubble.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0">
                    <i class="fa-solid ${activeRole === 'guest' ? 'fa-bell' : 'fa-hat-cowboy-side'}"></i>
                </div>
                <div class="bg-lounge-dark p-3 rounded-2xl rounded-tl-none border border-lounge-border text-sm leading-relaxed shadow-md">
                    ${parseMarkdown(text)}
                </div>
            `;
            chatBox.appendChild(welcomeBubble);
        } else {
            chatHistory.forEach(msg => {
                const bubble = document.createElement('div');
                if (msg.role === 'user') {
                    bubble.className = "flex gap-3 max-w-[85%] ml-auto justify-end fade-in mt-2";
                    bubble.innerHTML = `
                        <div class="bg-lounge-border p-3 rounded-2xl rounded-tr-none border border-gold border-opacity-10 text-sm leading-relaxed shadow-md">
                            ${msg.parts[0]}
                        </div>
                    `;
                } else {
                    bubble.className = "flex gap-3 max-w-[85%] fade-in mt-2";
                    bubble.innerHTML = `
                        <div class="w-8 h-8 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0">
                            <i class="fa-solid ${activeRole === 'guest' ? 'fa-bell' : 'fa-hat-cowboy-side'}"></i>
                        </div>
                        <div class="bg-lounge-dark p-3 rounded-2xl rounded-tl-none border border-lounge-border text-sm leading-relaxed shadow-md">
                            ${parseMarkdown(msg.parts[0])}
                        </div>
                    `;
                }
                chatBox.appendChild(bubble);
            });
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (err) {
        console.error("Error loading session:", err);
    }
}

// 4. CHAT SENDING
async function sendChatMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    
    chatInput.value = '';
    
    // Append User Message to UI
    const userBubble = document.createElement('div');
    userBubble.className = "flex gap-3 max-w-[85%] ml-auto justify-end fade-in mt-2";
    userBubble.innerHTML = `
        <div class="bg-lounge-border p-3 rounded-2xl rounded-tr-none border border-gold border-opacity-10 text-sm leading-relaxed shadow-md">
            ${message}
        </div>
    `;
    chatBox.appendChild(userBubble);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    chatHistory.push({ role: "user", parts: [message] });
    
    // Loading Indicator
    const typingBubble = document.createElement('div');
    typingBubble.className = "flex gap-3 max-w-[85%] fade-in mt-2";
    typingBubble.id = "typing-indicator";
    typingBubble.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0">
            <i class="fa-solid fa-hourglass-half animate-spin"></i>
        </div>
        <div class="bg-lounge-dark p-3 rounded-2xl rounded-tl-none border border-lounge-border flex gap-1 items-center shadow-md">
            <span class="w-1.5 h-1.5 bg-lounge-muted rounded-full animate-bounce"></span>
            <span class="w-1.5 h-1.5 bg-lounge-muted rounded-full animate-bounce" style="animation-delay: 0.2s"></span>
            <span class="w-1.5 h-1.5 bg-lounge-muted rounded-full animate-bounce" style="animation-delay: 0.4s"></span>
        </div>
    `;
    chatBox.appendChild(typingBubble);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // API Call
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                chat_history: chatHistory.slice(0, -1),
                role: activeRole,
                session_id: currentSessionId,
                user_id: CLIENT_USER_ID
            })
        });
        const data = await response.json();
        const indicator = document.getElementById("typing-indicator");
        if (indicator) indicator.remove();
        
        if (response.ok && !data.error) {
            const responseText = data.message || "No response generated.";
            const modelBubble = document.createElement('div');
            modelBubble.className = "flex gap-3 max-w-[85%] fade-in mt-2";
            modelBubble.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0">
                    <i class="fa-solid ${activeRole === 'guest' ? 'fa-bell' : 'fa-hat-cowboy-side'}"></i>
                </div>
                <div class="bg-lounge-dark p-3 rounded-2xl rounded-tl-none border border-lounge-border text-sm leading-relaxed shadow-md">
                    ${parseMarkdown(responseText)}
                </div>
            `;
            chatBox.appendChild(modelBubble);
            chatHistory.push({ role: "model", parts: [responseText] });
            
            // If AI recommended something, try to filter the grid!
            smartFilterGrid(responseText);
        } else {
            throw new Error(data.error || "Failed to query AI.");
        }
    } catch (err) {
        const indicator = document.getElementById("typing-indicator");
        if (indicator) indicator.remove();
        const errorBubble = document.createElement('div');
        errorBubble.className = "flex gap-3 max-w-[85%] fade-in mt-2";
        errorBubble.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-red-900 bg-opacity-20 flex items-center justify-center text-red-500 flex-shrink-0">
                <i class="fa-solid fa-triangle-exclamation"></i>
            </div>
            <div class="bg-red-950 bg-opacity-40 p-3 rounded-2xl rounded-tl-none border border-red-900 text-sm text-red-400">
                Error: ${err.message}
            </div>
        `;
        chatBox.appendChild(errorBubble);
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

// 5. VISUAL EXPLORER (DATABASE CARDS)
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
        return;
    }
    
    items.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = "bg-lounge-card rounded-2xl overflow-hidden border border-lounge-border shadow-lg group hover:shadow-[0_0_20px_rgba(197,160,89,0.15)] transition-all duration-300 flex flex-col h-full fade-in";
        card.style.animationDelay = `${(index % 10) * 50}ms`;

        if (type === 'cocktails') {
            // Render Cocktail Card
            let imageHtml = '';
            if (item.image_url && item.image_url.trim() !== '') {
                imageHtml = `<img src="${item.image_url}" alt="${item.name}" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110">`;
            } else {
                const colors = ['from-gray-900 to-gray-800', 'from-slate-900 to-slate-800', 'from-zinc-900 to-zinc-800', 'from-neutral-900 to-neutral-800'];
                const randomColor = colors[index % colors.length];
                imageHtml = `<div class="w-full h-full bg-gradient-to-br ${randomColor} flex items-center justify-center transition-transform duration-700 group-hover:scale-110"><i class="fa-solid fa-martini-glass-citrus text-gold opacity-50 text-6xl"></i></div>`;
            }
            
            card.innerHTML = `
                <div class="h-48 relative overflow-hidden pointer-events-none">
                    ${imageHtml}
                    <div class="absolute top-3 right-3 bg-lounge-darkest bg-opacity-80 backdrop-blur-md px-2.5 py-1 rounded-lg border border-gold border-opacity-30">
                        <span class="text-[10px] font-bold text-gold uppercase tracking-wider">${item.abv_category || 'N/A'}</span>
                    </div>
                </div>
                <div class="p-5 flex flex-col flex-grow pointer-events-none">
                    <h3 class="font-cinzel font-bold text-gold text-lg mb-1 truncate">${item.name}</h3>
                    <p class="text-xs text-lounge-muted mb-4 uppercase tracking-wide">
                        <i class="fa-solid fa-glass-water text-[10px]"></i> ${item.glassware_recommendation || 'Classic Glass'}
                    </p>
                    <p class="text-sm text-lounge-text line-clamp-3 mb-4 flex-grow opacity-90 leading-relaxed">
                        ${item.meaning_and_history || 'A premium selection crafted with the finest ingredients.'}
                    </p>
                    <div class="pt-4 border-t border-lounge-border flex flex-wrap gap-1.5">
                        ${(item.flavor_profile || 'Balanced').split(',').slice(0, 2).map(f => `<span class="text-[10px] bg-lounge-dark px-2 py-1 rounded text-lounge-muted border border-lounge-border whitespace-nowrap">${f.trim()}</span>`).join('')}
                        <span class="text-[10px] bg-lounge-dark px-2 py-1 rounded text-lounge-muted border border-lounge-border"><i class="fa-solid fa-layer-group text-[9px] mr-1"></i>${item.category || 'Cocktail'}</span>
                    </div>
                </div>
            `;
            
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => openDetailModal(item, 'cocktails'));
            
        } else {
            // Render Bar Card
            const colors = ['from-gray-900 to-gray-800', 'from-slate-900 to-slate-800', 'from-zinc-900 to-zinc-800', 'from-neutral-900 to-neutral-800'];
            const randomColor = colors[index % colors.length];
            const imageHtml = `<div class="w-full h-full bg-gradient-to-br ${randomColor} flex items-center justify-center transition-transform duration-700 group-hover:scale-110"><i class="fa-solid fa-compass text-gold opacity-50 text-6xl"></i></div>`;

            card.innerHTML = `
                <div class="h-32 relative overflow-hidden border-b border-lounge-border pointer-events-none">
                    ${imageHtml}
                    <div class="absolute top-3 right-3 bg-lounge-darkest bg-opacity-80 backdrop-blur-md px-2.5 py-1 rounded-lg border border-gold border-opacity-30">
                        <span class="text-[10px] font-bold text-gold uppercase tracking-wider">${item.price_range || '$$'}</span>
                    </div>
                </div>
                <div class="p-5 flex flex-col flex-grow pointer-events-none">
                    <h3 class="font-cinzel font-bold text-gold text-lg mb-1 truncate">${item.name}</h3>
                    <p class="text-[10px] text-lounge-muted mb-4 uppercase tracking-wide">
                        <i class="fa-solid fa-location-dot text-[9px] mr-1"></i> ${item.district}, ${item.city}
                    </p>
                    <p class="text-sm text-lounge-text line-clamp-3 mb-4 flex-grow opacity-90 leading-relaxed italic">
                        "${item.vibe_description || 'A stunning venue to experience premium mixology.'}"
                    </p>
                    <div class="pt-4 border-t border-lounge-border flex flex-wrap gap-1.5">
                        <span class="text-[10px] bg-lounge-dark px-2 py-1 rounded text-lounge-muted border border-lounge-border whitespace-nowrap"><i class="fa-solid fa-star text-[9px] mr-1"></i>${item.style}</span>
                        <span class="text-[10px] bg-gold bg-opacity-10 px-2 py-1 rounded text-gold border border-gold border-opacity-30"><i class="fa-solid fa-martini-glass text-[9px] mr-1"></i>${item.signature_cocktail}</span>
                    </div>
                </div>
            `;
            
            card.style.cursor = 'pointer';
            card.addEventListener('click', () => openDetailModal(item, 'bars'));
        }
        
        mainGrid.appendChild(card);
    });
}

// Detail Modal Logic
const detailModal = document.getElementById('detail-modal');
const btnCloseDetailModal = document.getElementById('btn-close-detail-modal');
const dmImageContainer = document.getElementById('detail-modal-image-container');
const dmTags = document.getElementById('detail-modal-tags');
const dmTitle = document.getElementById('detail-modal-title');
const dmSubtitle = document.getElementById('detail-modal-subtitle');
const dmDescription = document.getElementById('detail-modal-description');
const dmContentArea = document.getElementById('detail-modal-content-area');

btnCloseDetailModal.addEventListener('click', () => {
    detailModal.classList.add('hidden');
    detailModal.classList.remove('flex');
});

function openDetailModal(item, type) {
    // Reset contents
    dmImageContainer.innerHTML = '';
    dmTags.innerHTML = '';
    dmContentArea.innerHTML = '';
    
    if (type === 'cocktails') {
        // Image
        if (item.image_url && item.image_url.trim() !== '') {
            dmImageContainer.innerHTML = `<img src="${item.image_url}" alt="${item.name}" class="w-full h-full object-cover">`;
        } else {
            dmImageContainer.innerHTML = `<div class="w-full h-full bg-gradient-to-br from-zinc-900 to-zinc-800 flex items-center justify-center"><i class="fa-solid fa-martini-glass-citrus text-gold opacity-50 text-6xl"></i></div>`;
        }
        
        // Tags
        const tags = (item.flavor_profile || 'Balanced').split(',').slice(0, 3);
        tags.push(item.abv_category || 'N/A');
        tags.forEach(t => {
            dmTags.innerHTML += `<span class="text-xs bg-lounge-darkest bg-opacity-80 px-2.5 py-1 rounded-lg text-gold border border-gold border-opacity-30 whitespace-nowrap">${t.trim()}</span>`;
        });
        
        // Text
        dmTitle.innerText = item.name;
        dmSubtitle.innerHTML = `<i class="fa-solid fa-glass-water"></i> ${item.glassware_recommendation || 'Classic Glass'} &bull; ${item.category || 'Cocktail'}`;
        dmDescription.innerHTML = parseMarkdown(item.meaning_and_history || 'A premium selection crafted with the finest ingredients.');
        
        // Ingredients & Instructions
        let ingHtml = `<h4 class="font-cinzel text-gold text-lg mb-3 border-b border-lounge-border pb-1">Ingredients</h4><ul class="space-y-2 mb-6">`;
        if (item.ingredients && Array.isArray(item.ingredients)) {
            item.ingredients.forEach(ing => {
                ingHtml += `<li class="text-sm text-lounge-text flex items-start gap-2"><i class="fa-solid fa-check text-gold mt-1 text-xs"></i><span>${ing}</span></li>`;
            });
        }
        ingHtml += `</ul>`;
        
        let instHtml = `<h4 class="font-cinzel text-gold text-lg mb-3 border-b border-lounge-border pb-1">Instructions</h4><div class="text-sm text-lounge-text leading-relaxed bg-lounge-dark p-4 rounded-xl border border-lounge-border shadow-inner">`;
        instHtml += parseMarkdown(item.instructions || 'Combine ingredients and serve.');
        instHtml += `</div>`;
        
        dmContentArea.innerHTML = ingHtml + instHtml;
        
    } else {
        // Image
        dmImageContainer.innerHTML = `<div class="w-full h-full bg-gradient-to-br from-zinc-900 to-zinc-800 flex items-center justify-center"><i class="fa-solid fa-compass text-gold opacity-50 text-6xl"></i></div>`;
        
        // Tags
        dmTags.innerHTML = `
            <span class="text-xs bg-lounge-darkest bg-opacity-80 px-2.5 py-1 rounded-lg text-gold border border-gold border-opacity-30"><i class="fa-solid fa-star mr-1"></i>${item.style}</span>
            <span class="text-xs bg-lounge-darkest bg-opacity-80 px-2.5 py-1 rounded-lg text-gold border border-gold border-opacity-30">${item.price_range || '$$'}</span>
        `;
        
        // Text
        dmTitle.innerText = item.name;
        dmSubtitle.innerHTML = `<i class="fa-solid fa-location-dot"></i> ${item.district}, ${item.city}`;
        dmDescription.innerHTML = parseMarkdown(item.vibe_description || 'A stunning venue to experience premium mixology.');
        
        // Address & Signature
        let contentHtml = `
            <div class="bg-lounge-dark p-4 rounded-xl border border-lounge-border shadow-inner mb-6">
                <h4 class="font-cinzel text-gold text-sm uppercase tracking-wider mb-2">Location</h4>
                <p class="text-sm text-lounge-text"><i class="fa-solid fa-map-pin text-lounge-muted mr-2"></i>${item.address}</p>
            </div>
            <div class="bg-gold bg-opacity-10 p-4 rounded-xl border border-gold border-opacity-30 shadow-inner">
                <h4 class="font-cinzel text-gold text-sm uppercase tracking-wider mb-2">Signature Cocktail</h4>
                <p class="text-sm text-gold font-bold"><i class="fa-solid fa-martini-glass text-gold mr-2"></i>${item.signature_cocktail}</p>
            </div>
        `;
        dmContentArea.innerHTML = contentHtml;
    }
    
    detailModal.classList.remove('hidden');
    detailModal.classList.add('flex');
}

// 6. FILTERS AND SEARCH
function setupFilters() {
    searchInput.addEventListener('input', applyFilters);
    filterFlavor.addEventListener('change', applyFilters);
    filterAbv.addEventListener('change', applyFilters);
    filterCity.addEventListener('change', applyFilters);
    filterStyle.addEventListener('change', applyFilters);
    filterPrice.addEventListener('change', applyFilters);
}

function applyFilters() {
    const q = searchInput.value.toLowerCase();
    
    if (activeTab === 'cocktails') {
        const flavor = filterFlavor.value.toLowerCase();
        const abv = filterAbv.value.toLowerCase();
        
        const filtered = cocktailsData.filter(item => {
            const matchesQuery = item.name.toLowerCase().includes(q) || (item.ingredients && item.ingredients.join(' ').toLowerCase().includes(q));
            const matchesFlavor = flavor === '' || (item.flavor_profile && item.flavor_profile.toLowerCase().includes(flavor));
            const matchesAbv = abv === '' || (item.abv_category && item.abv_category.toLowerCase().includes(abv));
            return matchesQuery && matchesFlavor && matchesAbv;
        });
        renderGrid(filtered, 'cocktails');
    } else {
        const city = filterCity.value.toLowerCase();
        const style = filterStyle.value.toLowerCase();
        const price = filterPrice.value;
        
        const filtered = barsData.filter(item => {
            const matchesQuery = item.name.toLowerCase().includes(q) || item.district.toLowerCase().includes(q) || item.address.toLowerCase().includes(q);
            const matchesCity = city === '' || item.city.toLowerCase() === city;
            const matchesStyle = style === '' || item.style.toLowerCase() === style;
            const matchesPrice = price === '' || item.price_range === price;
            return matchesQuery && matchesCity && matchesStyle && matchesPrice;
        });
        renderGrid(filtered, 'bars');
    }
}

// Smart feature: If AI recommends a specific drink or bar, search for it
function smartFilterGrid(aiResponse) {
    const text = aiResponse.toLowerCase();
    
    // Check bars first (they are usually proper nouns)
    const activeBars = barsData.filter(b => text.includes(b.name.toLowerCase()));
    if (activeBars.length > 0) {
        if (activeTab !== 'bars') switchTab('bars');
        searchInput.value = activeBars[0].name;
        applyFilters();
        // Optional: Open modal directly
        // openDetailModal(activeBars[0], 'bars');
        return;
    }
    
    // Check cocktails
    const activeDrinks = cocktailsData.filter(d => text.includes(d.name.toLowerCase()));
    if (activeDrinks.length > 0) {
        if (activeTab !== 'cocktails') switchTab('cocktails');
        searchInput.value = activeDrinks[0].name;
        applyFilters();
        return;
    }
}

// 7. MENU COMPILER
const btnCompileMenu = document.getElementById('btn-compile-menu');
const menuModal = document.getElementById('menu-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const menuIframe = document.getElementById('menu-iframe');
const btnDownloadMenuModal = document.getElementById('btn-download-menu-modal');
let compiledMenuHtml = '';

// Unhide compile button when in cocktails tab
tabExploreCocktails.addEventListener('click', () => {
    btnCompileMenu.classList.remove('hidden');
});
tabExploreBars.addEventListener('click', () => {
    btnCompileMenu.classList.add('hidden');
});

// Initially show compile button
btnCompileMenu.classList.remove('hidden');

btnCompileMenu.addEventListener('click', async () => {
    // Gather currently visible cocktails
    const currentItems = [];
    document.querySelectorAll('#main-grid > div').forEach(card => {
        const titleEl = card.querySelector('h3');
        if (titleEl) {
            currentItems.push(titleEl.innerText);
        }
    });
    
    if (currentItems.length === 0) {
        alert("No cocktails on the screen to compile. Please adjust your filters.");
        return;
    }
    
    const menuTitle = prompt("Enter a title for your custom menu:", "THE ARTISAN LOUNGE");
    if (!menuTitle) return;
    
    btnCompileMenu.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin mr-2"></i> Compiling...`;
    
    try {
        const response = await fetch('/api/export-menu', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: menuTitle,
                cocktails: currentItems
            })
        });
        
        const data = await response.json();
        btnCompileMenu.innerHTML = `<i class="fa-solid fa-file-export mr-2"></i> Compile Menu`;
        
        if (response.ok && data.html) {
            compiledMenuHtml = data.html;
            const blob = new Blob([compiledMenuHtml], { type: 'text/html' });
            menuIframe.src = URL.createObjectURL(blob);
            menuModal.classList.remove('hidden');
            menuModal.classList.add('flex');
        } else {
            alert(data.error || "Failed to generate menu.");
        }
    } catch (err) {
        btnCompileMenu.innerHTML = `<i class="fa-solid fa-file-export mr-2"></i> Compile Menu`;
        alert(`Error compiling menu: ${err.message}`);
    }
});

btnCloseModal.addEventListener('click', () => {
    menuModal.classList.add('hidden');
    menuModal.classList.remove('flex');
});

btnDownloadMenuModal.addEventListener('click', () => {
    if (!compiledMenuHtml) return;
    const blob = new Blob([compiledMenuHtml], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'premium_menu.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});

// Utility: Markdown Parser
function parseMarkdown(text) {
    let parsed = text;
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
