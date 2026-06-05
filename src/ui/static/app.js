// Application State
let activeRole = 'guest'; // 'guest' or 'bartender'
let currentGuestSessionId = '';
let currentBartenderSessionId = '';
let guestSessions = [];
let bartenderSessions = [];
let guestHistory = [];
let bartenderHistory = [];
let abvIngredients = [
    { name: 'Gin', volume_ml: 45, abv: 40 },
    { name: 'Sweet Vermouth', volume_ml: 30, abv: 16 },
    { name: 'Campari', volume_ml: 30, abv: 25 }
];
let cocktailsList = [];
let compiledMenuHtml = '';

// DOM Elements
const btnGuestMode = document.getElementById('btn-guest-mode');
const btnBartenderMode = document.getElementById('btn-bartender-mode');
const guestView = document.getElementById('guest-view');
const bartenderView = document.getElementById('bartender-view');

const guestChatBox = document.getElementById('guest-chat-box');
const guestUserInput = document.getElementById('guest-user-input');
const btnSendGuest = document.getElementById('btn-send-guest');

const bartenderChatBox = document.getElementById('bartender-chat-box');
const bartenderUserInput = document.getElementById('bartender-user-input');
const btnSendBartender = document.getElementById('btn-send-bartender');

// Bar Finder Elements
const barCity = document.getElementById('bar-city');
const barStyle = document.getElementById('bar-style');
const barPrice = document.getElementById('bar-price');
const barDistrict = document.getElementById('bar-district');
const btnSearchBars = document.getElementById('btn-search-bars');
const barsResultsContainer = document.getElementById('bars-results-container');

// Bartender Sub-Tabs
const tabRecipeSearch = document.getElementById('tab-recipe-search');
const tabAbvCalc = document.getElementById('tab-abv-calc');
const tabMenuBuilder = document.getElementById('tab-menu-builder');
const toolRecipeSearchContent = document.getElementById('tool-recipe-search-content');
const toolAbvCalcContent = document.getElementById('tool-abv-calc-content');
const toolMenuBuilderContent = document.getElementById('tool-menu-builder-content');

// Recipe Finder Elements
const recipeSearchInput = document.getElementById('recipe-search-input');
const btnSearchRecipes = document.getElementById('btn-search-recipes');
const recipesResultsContainer = document.getElementById('recipes-results-container');

// ABV Calc Elements
const abvIngredientsList = document.getElementById('abv-ingredients-list');
const btnAbvAddRow = document.getElementById('btn-abv-add-row');
const btnAbvCalculate = document.getElementById('btn-abv-calculate');
const abvResultBox = document.getElementById('abv-result-box');

// Menu Builder Elements
const menuTitleInput = document.getElementById('menu-title-input');
const menuCocktailsChecklist = document.getElementById('menu-cocktails-checklist');
const btnCompileMenu = document.getElementById('btn-compile-menu');
const menuPreviewContainer = document.getElementById('menu-preview-container');
const menuPreviewIframe = document.getElementById('menu-preview-iframe');
const btnDownloadMenu = document.getElementById('btn-download-menu');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    setupRoleSwitcher();
    setupChatSystem();
    setupBarFinder();
    setupBartenderTabs();
    setupRecipeFinder();
    setupAbvCalculator();
    setupMenuBuilder();
    
    // Initial fetch to load sessions and cocktail list
    fetchSessions('guest');
    fetchSessions('bartender');
    fetchCocktailsForMenu();
});

// 1. ROLE SWITCHER
function setupRoleSwitcher() {
    btnGuestMode.addEventListener('click', () => {
        if (activeRole === 'guest') return;
        activeRole = 'guest';
        
        // Update Buttons Classes
        btnGuestMode.className = "px-5 py-2 rounded-full font-semibold text-sm transition-all duration-300 flex items-center gap-2 bg-gold text-lounge-darkest shadow-md";
        btnBartenderMode.className = "px-5 py-2 rounded-full font-semibold text-sm transition-all duration-300 flex items-center gap-2 text-lounge-muted hover:text-lounge-text";
        
        // Switch Views
        guestView.classList.remove('hidden');
        bartenderView.classList.add('hidden');
        
        // Render lists for guest
        renderSessionsList('guest');
    });

    btnBartenderMode.addEventListener('click', () => {
        if (activeRole === 'bartender') return;
        activeRole = 'bartender';
        
        // Update Buttons Classes
        btnBartenderMode.className = "px-5 py-2 rounded-full font-semibold text-sm transition-all duration-300 flex items-center gap-2 bg-gold text-lounge-darkest shadow-md";
        btnGuestMode.className = "px-5 py-2 rounded-full font-semibold text-sm transition-all duration-300 flex items-center gap-2 text-lounge-muted hover:text-lounge-text";
        
        // Switch Views
        bartenderView.classList.remove('hidden');
        guestView.classList.add('hidden');
        
        // Render lists for bartender
        renderSessionsList('bartender');
    });
}

// 1.5 SESSIONS PERSISTENCE LOGIC
async function fetchSessions(role) {
    try {
        const response = await fetch(`/api/sessions?role=${role}`);
        const data = await response.json();
        const sessions = data.sessions || [];
        
        if (role === 'guest') {
            guestSessions = sessions;
            renderSessionsList('guest');
            if (sessions.length === 0) {
                await createNewSession('guest');
            } else if (!currentGuestSessionId) {
                selectSession(sessions[0].id, 'guest');
            }
        } else {
            bartenderSessions = sessions;
            renderSessionsList('bartender');
            if (sessions.length === 0) {
                await createNewSession('bartender');
            } else if (!currentBartenderSessionId) {
                selectSession(sessions[0].id, 'bartender');
            }
        }
    } catch (err) {
        console.error("Error fetching sessions:", err);
    }
}

function renderSessionsList(role) {
    const listContainer = document.getElementById(`${role}-sessions-list`);
    const sessions = role === 'guest' ? guestSessions : bartenderSessions;
    const currentId = role === 'guest' ? currentGuestSessionId : currentBartenderSessionId;
    
    if (!listContainer) return;
    
    listContainer.innerHTML = '';
    sessions.forEach(s => {
        const item = document.createElement('div');
        const isSelected = s.id === currentId;
        
        item.className = `p-2 rounded-lg text-xs cursor-pointer truncate transition-all duration-200 border ${
            isSelected 
            ? 'bg-lounge-card border-gold text-gold font-bold shadow-md' 
            : 'border-transparent text-lounge-muted hover:text-lounge-text hover:bg-lounge-card hover:bg-opacity-50'
        }`;
        
        item.innerHTML = `
            <div class="flex justify-between items-center gap-1">
                <span class="truncate flex-grow"><i class="fa-solid fa-message mr-1.5 opacity-70"></i>${s.title}</span>
            </div>
        `;
        
        item.addEventListener('click', () => {
            selectSession(s.id, role);
        });
        
        listContainer.appendChild(item);
    });
}

async function createNewSession(role) {
    try {
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role: role })
        });
        const session = await response.json();
        
        if (role === 'guest') {
            currentGuestSessionId = session.id;
            guestSessions.unshift(session);
            renderSessionsList('guest');
            loadSessionHistory(session, 'guest');
        } else {
            currentBartenderSessionId = session.id;
            bartenderSessions.unshift(session);
            renderSessionsList('bartender');
            loadSessionHistory(session, 'bartender');
        }
    } catch (err) {
        console.error("Error creating session:", err);
    }
}

async function selectSession(sessionId, role) {
    if (role === 'guest') {
        currentGuestSessionId = sessionId;
        renderSessionsList('guest');
    } else {
        currentBartenderSessionId = sessionId;
        renderSessionsList('bartender');
    }
    
    try {
        const response = await fetch(`/api/sessions/${sessionId}`);
        const session = await response.json();
        loadSessionHistory(session, role);
    } catch (err) {
        console.error("Error loading session:", err);
    }
}

function loadSessionHistory(session, role) {
    const chatBox = role === 'guest' ? guestChatBox : bartenderChatBox;
    const titleDisplay = document.querySelector(`.${role}-chat-title-display`);
    
    if (titleDisplay) {
        titleDisplay.innerText = session.title || (role === 'guest' ? "Lounge Host" : "Master Mixologist");
    }
    
    chatBox.innerHTML = '';
    const history = session.chat_history || [];
    
    if (role === 'guest') {
        guestHistory = history;
    } else {
        bartenderHistory = history;
    }
    
    if (history.length === 0) {
        // Render Initial Welcome Message
        const welcomeBubble = document.createElement('div');
        welcomeBubble.className = "flex gap-3 max-w-[85%] fade-in";
        if (role === 'guest') {
            welcomeBubble.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0">
                    <i class="fa-solid fa-bell"></i>
                </div>
                <div class="bg-lounge-dark p-3 rounded-2xl rounded-tl-none border border-lounge-border text-sm leading-relaxed">
                    Good evening. Welcome to the **AI Lounge**. I am your Guest Concierge. Tell me, what kind of flavor profile are you craving tonight, or are you looking for an exceptional bar venue in Hanoi or Ho Chi Minh City?
                </div>
            `;
        } else {
            welcomeBubble.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0">
                    <i class="fa-solid fa-hat-cowboy-side"></i>
                </div>
                <div class="bg-lounge-dark p-3 rounded-2xl rounded-tl-none border border-lounge-border text-sm leading-relaxed">
                    Hello. I am the **Master Bartender**. I can help you compile classic recipes, troubleshoot flavor profiles, recommend professional substitutes for missing ingredients, and calculate precise ABV rates.
                </div>
            `;
        }
        chatBox.appendChild(welcomeBubble);
    } else {
        // Render History messages
        history.forEach(msg => {
            const bubble = document.createElement('div');
            if (msg.role === 'user') {
                bubble.className = "flex gap-3 max-w-[85%] ml-auto justify-end fade-in";
                bubble.innerHTML = `
                    <div class="bg-lounge-border p-3 rounded-2xl rounded-tr-none border border-gold border-opacity-10 text-sm leading-relaxed">
                        ${msg.parts[0]}
                    </div>
                    <div class="w-8 h-8 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0">
                        <i class="fa-solid fa-user"></i>
                    </div>
                `;
            } else {
                bubble.className = "flex gap-3 max-w-[85%] fade-in";
                bubble.innerHTML = `
                    <div class="w-8 h-8 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0">
                        <i class="fa-solid ${role === 'guest' ? 'fa-bell' : 'fa-hat-cowboy-side'}"></i>
                    </div>
                    <div class="bg-lounge-dark p-3 rounded-2xl rounded-tl-none border border-lounge-border text-sm leading-relaxed">
                        ${parseMarkdown(msg.parts[0])}
                    </div>
                `;
            }
            chatBox.appendChild(bubble);
        });
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function deleteCurrentSession(role) {
    const sessionId = role === 'guest' ? currentGuestSessionId : currentBartenderSessionId;
    if (!sessionId) {
        alert("No active session to delete.");
        return;
    }
    
    if (!confirm("Are you sure you want to delete this chat session?")) return;
    
    try {
        const response = await fetch(`/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            if (role === 'guest') {
                currentGuestSessionId = '';
            } else {
                currentBartenderSessionId = '';
            }
            await fetchSessions(role);
        } else {
            const errData = await response.json();
            alert(`Failed to delete session: ${errData.error || response.statusText}`);
        }
    } catch (err) {
        console.error("Error deleting session:", err);
        alert(`Error deleting session: ${err.message}`);
    }
}

// 2. CHAT SYSTEM SETUP
function setupChatSystem() {
    // Guest Chat send triggers
    btnSendGuest.addEventListener('click', () => sendChatMessage('guest'));
    guestUserInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage('guest');
    });

    // Bartender Chat send triggers
    btnSendBartender.addEventListener('click', () => sendChatMessage('bartender'));
    bartenderUserInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage('bartender');
    });

    // Delete Current Chat Hook
    document.querySelectorAll('.btn-delete-current-chat').forEach(btn => {
        btn.addEventListener('click', () => {
            const role = btn.getAttribute('data-role');
            deleteCurrentSession(role);
        });
    });

    // New Chat Click Hook
    document.querySelectorAll('.btn-new-chat').forEach(btn => {
        btn.addEventListener('click', () => {
            const role = btn.getAttribute('data-role');
            createNewSession(role);
        });
    });

    // Suggestion chips listeners
    document.querySelectorAll('.chip-query').forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.innerText.trim();
            if (activeRole === 'guest') {
                guestUserInput.value = query;
                sendChatMessage('guest');
            } else {
                bartenderUserInput.value = query;
                sendChatMessage('bartender');
            }
        });
    });
}

function parseMarkdown(text) {
    let parsed = text;
    
    // Bold **text**
    parsed = parsed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Bullet Points starting with * or -
    parsed = parsed.split('\n').map(line => {
        const trimmed = line.trim();
        if (trimmed.startsWith('*') && !trimmed.startsWith('***')) {
            return `<li class="ml-4 list-disc text-sm">${trimmed.substring(1).trim()}</li>`;
        }
        if (trimmed.startsWith('-')) {
            return `<li class="ml-4 list-disc text-sm">${trimmed.substring(1).trim()}</li>`;
        }
        if (trimmed.startsWith('###')) {
            return `<h4 class="font-bold text-gold text-sm mt-3 mb-1 uppercase">${trimmed.substring(3).trim()}</h4>`;
        }
        return line;
    }).join('\n');

    // Replace linebreaks with <br/> except within list tag constructs
    parsed = parsed.replace(/\n/g, '<br/>');
    return parsed;
}

async function sendChatMessage(role) {
    const inputField = role === 'guest' ? guestUserInput : bartenderUserInput;
    const chatBox = role === 'guest' ? guestChatBox : bartenderChatBox;
    const history = role === 'guest' ? guestHistory : bartenderHistory;
    const sessionId = role === 'guest' ? currentGuestSessionId : currentBartenderSessionId;
    
    const message = inputField.value.trim();
    if (!message) return;
    
    // Clear Input
    inputField.value = '';
    
    // Append User Message to UI
    const userBubble = document.createElement('div');
    userBubble.className = "flex gap-3 max-w-[85%] ml-auto justify-end fade-in";
    userBubble.innerHTML = `
        <div class="bg-lounge-border p-3 rounded-2xl rounded-tr-none border border-gold border-opacity-10 text-sm leading-relaxed">
            ${message}
        </div>
        <div class="w-8 h-8 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0">
            <i class="fa-solid fa-user"></i>
        </div>
    `;
    chatBox.appendChild(userBubble);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // Update history storage
    history.push({
        role: "user",
        parts: [message]
    });
    
    // Render Loading/Typing Indicator
    const typingBubble = document.createElement('div');
    typingBubble.className = "flex gap-3 max-w-[85%] fade-in";
    typingBubble.id = `${role}-typing-indicator`;
    typingBubble.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0">
            <i class="fa-solid fa-hourglass-half animate-spin"></i>
        </div>
        <div class="bg-lounge-dark p-3 rounded-2xl rounded-tl-none border border-lounge-border flex gap-1 items-center">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
    `;
    chatBox.appendChild(typingBubble);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // Send API Request
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                chat_history: history.slice(0, -1),
                role: role,
                session_id: sessionId
            })
        });
        
        const data = await response.json();
        
        // Remove Typing Indicator
        const indicator = document.getElementById(`${role}-typing-indicator`);
        if (indicator) indicator.remove();
        
        if (response.ok) {
            // Append Model response
            const responseText = data.message;
            const modelBubble = document.createElement('div');
            modelBubble.className = "flex gap-3 max-w-[85%] fade-in";
            modelBubble.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-gold bg-opacity-20 flex items-center justify-center text-gold flex-shrink-0">
                    <i class="fa-solid ${role === 'guest' ? 'fa-bell' : 'fa-hat-cowboy-side'}"></i>
                </div>
                <div class="bg-lounge-dark p-3 rounded-2xl rounded-tl-none border border-lounge-border text-sm leading-relaxed">
                    ${parseMarkdown(responseText)}
                </div>
            `;
            chatBox.appendChild(modelBubble);
            
            // Save to state
            history.push({
                role: "model",
                parts: [responseText]
            });
            
            // Trigger background reload of sessions metadata to update the title
            fetchSessions(role);
        } else {
            throw new Error(data.message || "Failed to query backend agents.");
        }
    } catch (err) {
        console.error(err);
        const indicator = document.getElementById(`${role}-typing-indicator`);
        if (indicator) indicator.remove();
        
        const errorBubble = document.createElement('div');
        errorBubble.className = "flex gap-3 max-w-[85%] fade-in";
        errorBubble.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-red-900 bg-opacity-20 flex items-center justify-center text-red-500 flex-shrink-0">
                <i class="fa-solid fa-triangle-exclamation"></i>
            </div>
            <div class="bg-red-950 bg-opacity-40 p-3 rounded-2xl rounded-tl-none border border-red-900 text-sm text-red-400">
                Error: ${err.message}. Please verify your configurations and try again.
            </div>
        `;
        chatBox.appendChild(errorBubble);
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

// 3. BAR FINDER SEARCH
function setupBarFinder() {
    btnSearchBars.addEventListener('click', searchBars);
    
    // Initial search
    searchBars();
}

async function searchBars() {
    const city = barCity.value;
    const style = barStyle.value;
    const price = barPrice.value;
    const district = barDistrict.value.trim();
    
    barsResultsContainer.innerHTML = `
        <div class="text-center py-8 text-lounge-muted text-sm">
            <i class="fa-solid fa-circle-notch animate-spin text-xl text-gold mb-2 block"></i> Seeking venues...
        </div>
    `;
    
    try {
        const queryParams = new URLSearchParams({
            city: city,
            style: style,
            price_range: price,
            district: district
        });
        
        const response = await fetch(`/api/bars?${queryParams.toString()}`);
        const data = await response.json();
        
        const bars = data.bars || [];
        if (bars.length === 0) {
            barsResultsContainer.innerHTML = `
                <div class="text-center py-8 text-lounge-muted text-sm border border-dashed border-lounge-border rounded-2xl">
                    No matching venues found. Try adjusting filters.
                </div>
            `;
            return;
        }
        
        barsResultsContainer.innerHTML = '';
        bars.forEach(bar => {
            const card = document.createElement('div');
            card.className = "bg-lounge-card border border-lounge-border rounded-2xl p-5 shadow-xl fade-in hover:border-gold hover:border-opacity-30 transition-all duration-300";
            card.innerHTML = `
                <div class="flex justify-between items-start mb-2">
                    <h3 class="font-cinzel font-bold text-gold text-base">✨ ${bar.name}</h3>
                    <span class="text-xs bg-lounge-border px-2 py-1 rounded text-lounge-muted">${bar.price_range}</span>
                </div>
                <div class="text-xs text-lounge-muted mb-3">
                    <i class="fa-solid fa-location-dot"></i> ${bar.address}, ${bar.district}, ${bar.city}
                </div>
                <div class="text-xs text-lounge-text space-y-2">
                    <div><strong>Vibe Vibe:</strong> <span class="text-gold bg-gold bg-opacity-5 px-2 py-0.5 rounded border border-gold border-opacity-10">${bar.style}</span></div>
                    <div><strong>Signature Drink:</strong> ${bar.signature_cocktail}</div>
                    <div class="italic text-lounge-muted mt-2">"${bar.vibe_description}"</div>
                </div>
            `;
            barsResultsContainer.appendChild(card);
        });
        
    } catch (err) {
        console.error(err);
        barsResultsContainer.innerHTML = `
            <div class="bg-red-950 bg-opacity-35 border border-red-900 text-red-400 p-4 rounded-xl text-sm">
                Failed to load bar results: ${err.message}
            </div>
        `;
    }
}

// 4. BARTENDER SUB-TABS
function setupBartenderTabs() {
    tabRecipeSearch.addEventListener('click', () => {
        switchTab('recipe');
    });
    tabAbvCalc.addEventListener('click', () => {
        switchTab('abv');
    });
    tabMenuBuilder.addEventListener('click', () => {
        switchTab('menu');
    });
}

function switchTab(tab) {
    // Reset borders
    tabRecipeSearch.className = "flex-1 py-3 text-center border-b-2 border-transparent font-semibold text-sm text-lounge-muted hover:text-lounge-text";
    tabAbvCalc.className = "flex-1 py-3 text-center border-b-2 border-transparent font-semibold text-sm text-lounge-muted hover:text-lounge-text";
    tabMenuBuilder.className = "flex-1 py-3 text-center border-b-2 border-transparent font-semibold text-sm text-lounge-muted hover:text-lounge-text";
    
    // Hide all
    toolRecipeSearchContent.classList.add('hidden');
    toolAbvCalcContent.classList.add('hidden');
    toolMenuBuilderContent.classList.add('hidden');
    
    if (tab === 'recipe') {
        tabRecipeSearch.className = "flex-1 py-3 text-center border-b-2 border-gold font-bold text-sm text-gold";
        toolRecipeSearchContent.classList.remove('hidden');
    } else if (tab === 'abv') {
        tabAbvCalc.className = "flex-1 py-3 text-center border-b-2 border-gold font-bold text-sm text-gold";
        toolAbvCalcContent.classList.remove('hidden');
    } else if (tab === 'menu') {
        tabMenuBuilder.className = "flex-1 py-3 text-center border-b-2 border-gold font-bold text-sm text-gold";
        toolMenuBuilderContent.classList.remove('hidden');
    }
}

// 5. RECIPE FINDER
function setupRecipeFinder() {
    btnSearchRecipes.addEventListener('click', searchRecipes);
    recipeSearchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchRecipes();
    });
    
    // Initial load
    searchRecipes();
}

async function searchRecipes() {
    const search = recipeSearchInput.value.trim();
    recipesResultsContainer.innerHTML = `
        <div class="text-center py-8 text-lounge-muted text-sm">
            <i class="fa-solid fa-circle-notch animate-spin text-xl text-gold mb-2 block"></i> Fetching recipes...
        </div>
    `;
    
    try {
        const response = await fetch(`/api/cocktails?search=${encodeURIComponent(search)}`);
        const data = await response.json();
        
        const cocktails = data.cocktails || [];
        if (cocktails.length === 0) {
            recipesResultsContainer.innerHTML = `
                <div class="text-center py-8 text-lounge-muted text-sm border border-dashed border-lounge-border rounded-2xl">
                    No matching recipes found.
                </div>
            `;
            return;
        }
        
        recipesResultsContainer.innerHTML = '';
        cocktails.forEach(c => {
            const card = document.createElement('div');
            card.className = "bg-lounge-card border border-lounge-border rounded-2xl p-5 shadow-xl fade-in hover:border-gold hover:border-opacity-30 transition-all duration-300";
            
            // Format ingredients
            const ingredientsHtml = c.ingredients.map(ing => `<li class="list-disc ml-4 text-xs text-lounge-text">${ing}</li>`).join('');
            
            card.innerHTML = `
                <div class="flex justify-between items-start mb-2">
                    <h3 class="font-cinzel font-bold text-gold text-base">🍹 ${c.name}</h3>
                    <span class="text-[10px] bg-gold bg-opacity-10 border border-gold border-opacity-25 px-2 py-0.5 rounded font-bold text-gold uppercase">${c.abv_category}</span>
                </div>
                <div class="text-xs text-lounge-muted mb-3">
                    Glassware: <strong>${c.glassware_recommendation}</strong> | Category: <strong>${c.category}</strong>
                </div>
                <div class="space-y-2 mt-2">
                    <div>
                        <strong class="text-xs text-lounge-muted uppercase">Ingredients:</strong>
                        <ul class="mt-1">${ingredientsHtml}</ul>
                    </div>
                    <div class="text-xs text-lounge-text mt-2">
                        <strong class="text-xs text-lounge-muted uppercase block">Instructions:</strong>
                        ${c.instructions}
                    </div>
                    ${c.meaning_and_history ? `
                    <div class="text-xs text-lounge-muted border-t border-lounge-border pt-2 mt-2 italic">
                        "History: ${c.meaning_and_history}"
                    </div>` : ''}
                </div>
            `;
            recipesResultsContainer.appendChild(card);
        });
        
    } catch (err) {
        console.error(err);
        recipesResultsContainer.innerHTML = `
            <div class="bg-red-950 bg-opacity-35 border border-red-900 text-red-400 p-4 rounded-xl text-sm">
                Failed to query recipes: ${err.message}
            </div>
        `;
    }
}

// 6. ABV CALCULATOR
function setupAbvCalculator() {
    renderAbvRows();
    
    btnAbvAddRow.addEventListener('click', () => {
        abvIngredients.push({ name: '', volume_ml: 45, abv: 40 });
        renderAbvRows();
    });

    btnAbvCalculate.addEventListener('click', calculateAbvRate);
}

function renderAbvRows() {
    abvIngredientsList.innerHTML = '';
    abvIngredients.forEach((ing, idx) => {
        const row = document.createElement('div');
        row.className = "flex gap-2 items-center fade-in bg-lounge-dark p-3 rounded-xl border border-lounge-border";
        row.innerHTML = `
            <div class="flex-grow">
                <input type="text" value="${ing.name}" placeholder="Ingredient name (e.g. Gin)" class="w-full bg-lounge-card text-lounge-text border border-lounge-border rounded-lg px-2.5 py-1 text-xs focus:outline-none focus:border-gold" onchange="updateAbvRow(${idx}, 'name', this.value)">
            </div>
            <div class="w-24">
                <input type="number" value="${ing.volume_ml}" placeholder="Vol (ml)" class="w-full bg-lounge-card text-lounge-text border border-lounge-border rounded-lg px-2.5 py-1 text-xs focus:outline-none focus:border-gold" onchange="updateAbvRow(${idx}, 'volume_ml', this.value)">
            </div>
            <div class="w-20">
                <input type="number" value="${ing.abv}" placeholder="ABV %" class="w-full bg-lounge-card text-lounge-text border border-lounge-border rounded-lg px-2.5 py-1 text-xs focus:outline-none focus:border-gold" onchange="updateAbvRow(${idx}, 'abv', this.value)">
            </div>
            <button class="text-red-400 hover:text-red-300 p-1 transition-colors text-sm" onclick="removeAbvRow(${idx})">
                <i class="fa-solid fa-circle-minus"></i>
            </button>
        `;
        abvIngredientsList.appendChild(row);
    });
}

window.updateAbvRow = function(idx, field, value) {
    if (field === 'volume_ml' || field === 'abv') {
        abvIngredients[idx][field] = parseFloat(value) || 0;
    } else {
        abvIngredients[idx][field] = value;
    }
};

window.removeAbvRow = function(idx) {
    abvIngredients.splice(idx, 1);
    renderAbvRows();
};

async function calculateAbvRate() {
    if (abvIngredients.length === 0) {
        alert("Please add at least one ingredient!");
        return;
    }
    
    btnAbvCalculate.innerHTML = `<i class="fa-solid fa-circle-notch animate-spin"></i> Calculating...`;
    
    try {
        const response = await fetch('/api/abv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ingredients: abvIngredients
            })
        });
        
        const data = await response.json();
        btnAbvCalculate.innerHTML = `<i class="fa-solid fa-square-root-variable text-xs"></i> Calculate ABV`;
        
        if (response.ok) {
            abvResultBox.classList.remove('hidden');
            abvResultBox.innerHTML = `
                <div class="border-l-4 p-4 rounded-xl bg-lounge-dark fade-in" style="border-color: ${data.color_code}">
                    <h4 class="font-bold text-xs uppercase tracking-wider text-lounge-muted mb-1">Resulting Formula Profile</h4>
                    <div class="text-2xl font-bold font-cinzel text-gold mt-1">${data.estimated_abv}% ABV</div>
                    <div class="text-xs text-lounge-text mt-1">Classification: <strong>${data.abv_category}</strong></div>
                    <p class="text-xs text-lounge-muted mt-2">${data.description}</p>
                </div>
            `;
        } else {
            throw new Error(data.error || "Failed to run calculation math.");
        }
        
    } catch (err) {
        btnAbvCalculate.innerHTML = `<i class="fa-solid fa-square-root-variable text-xs"></i> Calculate ABV`;
        alert(`Calculation Error: ${err.message}`);
    }
}

// 7. MENU BUILDER
function setupMenuBuilder() {
    btnCompileMenu.addEventListener('click', compileMenu);
    btnDownloadMenu.addEventListener('click', downloadMenu);
}

async function fetchCocktailsForMenu() {
    try {
        const response = await fetch('/api/cocktails');
        const data = await response.json();
        
        cocktailsList = data.cocktails || [];
        
        menuCocktailsChecklist.innerHTML = '';
        if (cocktailsList.length === 0) {
            menuCocktailsChecklist.innerHTML = `<div class="text-xs text-lounge-muted text-center py-4">No cocktails found in database.</div>`;
            return;
        }
        
        cocktailsList.forEach((c, idx) => {
            const item = document.createElement('label');
            item.className = "flex items-center gap-3 py-1.5 px-2 hover:bg-lounge-card rounded-lg cursor-pointer text-xs text-lounge-text transition-all duration-150";
            item.innerHTML = `
                <input type="checkbox" value="${c.name}" class="rounded accent-gold text-lounge-darkest bg-lounge-card border-lounge-border" id="chk-menu-cocktail-${idx}">
                <span class="font-semibold">${c.name}</span>
                <span class="text-[9px] text-lounge-muted ml-auto bg-lounge-border px-1.5 py-0.5 rounded">${c.abv_category}</span>
            `;
            menuCocktailsChecklist.appendChild(item);
        });
        
    } catch (err) {
        console.error(err);
        menuCocktailsChecklist.innerHTML = `<div class="text-xs text-red-400 text-center py-4">Failed to load: ${err.message}</div>`;
    }
}

async function compileMenu() {
    // Get all checked checkboxes
    const checkedBoxes = menuCocktailsChecklist.querySelectorAll('input[type="checkbox"]:checked');
    const selectedNames = Array.from(checkedBoxes).map(box => box.value);
    
    if (selectedNames.length === 0) {
        alert("Please select at least one drink to compile a menu!");
        return;
    }
    
    const menuTitle = menuTitleInput.value.trim() || "THE ARTISAN LOUNGE";
    
    // Filter cocktails from the cached list
    const selectedCocktails = cocktailsList.filter(c => selectedNames.includes(c.name));
    
    btnCompileMenu.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i> Compiling...`;
    
    try {
        const response = await fetch('/api/export-menu', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: menuTitle,
                cocktails: selectedCocktails
            })
        });
        
        const data = await response.json();
        btnCompileMenu.innerHTML = `Compile & Preview`;
        
        if (response.ok) {
            compiledMenuHtml = data.html;
            
            // Set source doc on preview iframe
            menuPreviewContainer.classList.remove('hidden');
            menuPreviewIframe.srcdoc = compiledMenuHtml;
            
            // Scroll down to preview
            menuPreviewContainer.scrollIntoView({ behavior: 'smooth' });
        } else {
            throw new Error("Failed to export HTML menu template.");
        }
        
    } catch (err) {
        btnCompileMenu.innerHTML = `Compile & Preview`;
        alert(`Compilation Error: ${err.message}`);
    }
}

function downloadMenu() {
    if (!compiledMenuHtml) {
        alert("Please compile the menu first!");
        return;
    }
    
    const blob = new Blob([compiledMenuHtml], { type: 'text/html' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'premium_lounge_menu.html';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
