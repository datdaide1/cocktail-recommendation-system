import streamlit as st
import pandas as pd
import json
import sys
from pathlib import Path

# Append src to path
src_path = Path(__file__).resolve().parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from src.agents.cocktail_agents import CocktailAgentSystem
from src.tools.cocktail_tools import get_cocktails_df, get_bars_df
from src.utils.menu_exporter import MenuExporter

# Set page configs
st.set_page_config(
    page_title="🍸 AI Lounge - Cocktail & Bar Assistant",
    page_icon="🍸",
    layout="wide"
)

# Custom CSS for Luxury Dark Mode with Gold Highlights
st.markdown("""
<style>
    .main {
        background-color: #0c0f17;
        color: #f1f3f8;
    }
    .stApp {
        background-color: #0c0f17;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #121622;
        padding: 8px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: #1a2035;
        border-radius: 4px;
        color: #8b9bb4;
        padding-left: 20px;
        padding-right: 20px;
        font-weight: 500;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #c5a059 !important;
        color: #0c0f17 !important;
        font-weight: bold;
    }
    .stButton>button {
        background-color: #c5a059;
        color: #0c0f17;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #e5c158;
        color: #0c0f17;
        box-shadow: 0 4px 15px rgba(197, 160, 89, 0.4);
    }
    .card {
        background-color: #121622;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #1c2335;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .card-title {
        font-family: 'Cinzel', serif;
        color: #c5a059;
        font-size: 1.3em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .card-meta {
        font-size: 0.85em;
        color: #8b9bb4;
        margin-bottom: 12px;
    }
    .card-content {
        font-size: 0.95em;
        color: #d1d9e6;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session States
if "agent_system" not in st.session_state:
    try:
        st.session_state.agent_system = CocktailAgentSystem()
    except Exception as e:
        st.session_state.agent_system = None
        st.error(f"Failed to initialize Agent System: {e}")

if "guest_chat_history" not in st.session_state:
    st.session_state.guest_chat_history = []

if "bartender_chat_history" not in st.session_state:
    st.session_state.bartender_chat_history = []

if "abv_ingredients" not in st.session_state:
    st.session_state.abv_ingredients = [{"name": "", "volume_ml": 45.0, "abv": 40.0}]

def main():
    st.title("🍸 AI Lounge - Cocktail & Bar Assistant")
    st.markdown("<p style='color: #8b9bb4;'>A premium multi-agent system powered by Gemini API for guests and mixology experts.</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar Role Configurator
    st.sidebar.markdown("<h2 style='color: #c5a059; font-family: Cinzel;'>SETTINGS</h2>", unsafe_allow_html=True)
    role_selection = st.sidebar.radio(
        "Choose Persona Vibe:",
        ["🍸 Guest Concierge", "🤵 Master Bartender"]
    )
    
    # Quick reset button for current chat history
    if st.sidebar.button("Clear Chat History"):
        if role_selection == "🍸 Guest Concierge":
            st.session_state.guest_chat_history = []
        else:
            st.session_state.bartender_chat_history = []
        st.sidebar.success("Chat history cleared!")
        
    st.sidebar.markdown("---")
    st.sidebar.info(
        "💡 **Dual Mode Agent System**\n\n"
        "- **Guest Mode** searches real bars in Vietnam, analyzes taste profiles, and suggests cocktails.\n"
        "- **Bartender Mode** calculates ABV, gives recipe details, and suggests replacements."
    )
    
    # Ensure system is loaded
    if not st.session_state.agent_system:
        st.error("Gemini Agent System is offline. Please configure GEMINI_API_KEY in .env.")
        return
        
    # Render Role Views
    if role_selection == "🍸 Guest Concierge":
        st.subheader("Welcome to the Guest Concierge Mode")
        
        tab1, tab2 = st.tabs(["💬 Chat with Host", "📍 Vietnam Bar Directory"])
        
        with tab1:
            st.markdown("#### Converse with your Lounge Concierge")
            st.write("Tell the concierge what vibe, mood, flavor, or spirits you are looking for.")
            
            # Conversation starter suggestions
            st.markdown("**Try asking:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Suggest a sour cocktail"):
                    # Inject query
                    st.session_state.guest_query = "Suggest a refreshing sour cocktail."
            with col2:
                if st.button("Recommend Speakeasies in Hanoi"):
                    st.session_state.guest_query = "Can you recommend some speakeasy bars in Hoan Kiem district?"
            with col3:
                if st.button("Fruity drinks in District 1 HCMC"):
                    st.session_state.guest_query = "Find some bars in District 1 Ho Chi Minh City that serve good signature drinks."
                    
            # Chat Interface
            chat_container = st.container()
            with chat_container:
                for msg in st.session_state.guest_chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["parts"][0])
            
            user_input = st.text_input(
                "Your request:",
                key="guest_text_input",
                value=st.session_state.get("guest_query", "")
            )
            
            if st.button("Send", key="send_guest"):
                if user_input.strip():
                    with st.spinner("Concierge is responding..."):
                        # Clear target query
                        if "guest_query" in st.session_state:
                            del st.session_state["guest_query"]
                        
                        # Add user message
                        st.session_state.guest_chat_history.append({
                            "role": "user",
                            "parts": [user_input]
                        })
                        
                        # Run Agent
                        res = st.session_state.agent_system.run_chat(
                            user_input,
                            st.session_state.guest_chat_history[:-1],
                            "guest"
                        )
                        
                        # Save model response
                        st.session_state.guest_chat_history.append({
                            "role": "model",
                            "parts": [res["message"]]
                        })
                        
                        st.rerun()
                        
        with tab2:
            st.markdown("#### Explore Curated Premium Venues")
            st.write("Manually browse high-end lounges, speakeasies, and rooftop bars in Vietnam.")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                city = st.selectbox("Select City", ["Hanoi", "Ho Chi Minh City"])
            with col2:
                style = st.selectbox("Vibe Style", ["Any", "Speakeasy", "Rooftop", "Cozy Lounge", "Jazz Bar", "Craft Bar"])
            with col3:
                price = st.selectbox("Price Range", ["Any", "$", "$$", "$$$"])
            with col4:
                district_search = st.text_input("District (e.g. Hoan Kiem, District 1)")
                
            if st.button("Filter Directory"):
                df = get_bars_df()
                if not df.empty:
                    # Filter matching rows
                    filtered_df = df[df['city'].str.lower() == city.lower()]
                    if style != "Any":
                        filtered_df = filtered_df[filtered_df['style'].str.lower().str.contains(style.lower())]
                    if price != "Any":
                        filtered_df = filtered_df[filtered_df['price_range'] == price]
                    if district_search:
                        filtered_df = filtered_df[filtered_df['district'].str.lower().str.contains(district_search.lower())]
                        
                    if filtered_df.empty:
                        st.warning("No venues match your filtering criteria. Try expanding your search.")
                    else:
                        st.write(f"Showing {len(filtered_df)} premium venues:")
                        for _, row in filtered_df.iterrows():
                            st.markdown(f"""
                            <div class="card">
                                <div class="card-title">✨ {row['name']}</div>
                                <div class="card-meta">📍 {row['address']}, {row['district']}, {row['city']} | Vibe: {row['style']} | Price: {row['price_range']}</div>
                                <div class="card-content">
                                    <strong>Signature Cocktail:</strong> {row['signature_cocktail']}<br/>
                                    <strong>Atmosphere:</strong> {row['vibe_description']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
    else:
        st.subheader("Welcome to the Master Bartender Toolkit")
        
        tab1, tab2, tab3, tab4 = st.tabs(["💬 Consult Expert", "📜 Recipe Lookup", "⚗️ ABV Calculator", "📋 Custom Menu Builder"])
        
        with tab1:
            st.markdown("#### Expert Mixology Chat")
            st.write("Consult the Master Bartender about cocktail histories, substitute ingredients, or specific preparation methods.")
            
            # Suggestions
            st.markdown("**Quick Prompts:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Margarita story & recipe"):
                    st.session_state.bartender_query = "Tell me the story of the Margarita and search its recipe details."
            with col2:
                if st.button("Bourbon substitute in Mint Julep"):
                    st.session_state.bartender_query = "What is a professional substitute for Bourbon if I am making a Mint Julep?"
            with col3:
                if st.button("How to shake/stir correctly"):
                    st.session_state.bartender_query = "Explain the rules of shaking vs stirring cocktails."
            
            chat_container = st.container()
            with chat_container:
                for msg in st.session_state.bartender_chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["parts"][0])
                        
            user_input = st.text_input(
                "Ask the expert:",
                key="bartender_text_input",
                value=st.session_state.get("bartender_query", "")
            )
            
            if st.button("Send", key="send_bartender"):
                if user_input.strip():
                    with st.spinner("Bartender is writing..."):
                        if "bartender_query" in st.session_state:
                            del st.session_state["bartender_query"]
                            
                        st.session_state.bartender_chat_history.append({
                            "role": "user",
                            "parts": [user_input]
                        })
                        
                        res = st.session_state.agent_system.run_chat(
                            user_input,
                            st.session_state.bartender_chat_history[:-1],
                            "bartender"
                        )
                        
                        st.session_state.bartender_chat_history.append({
                            "role": "model",
                            "parts": [res["message"]]
                        })
                        st.rerun()
                        
        with tab2:
            st.markdown("#### Premium Recipe Search")
            st.write("Browse complete cocktail records in the database.")
            search_query = st.text_input("Search by Cocktail Name or Main Ingredient:")
            
            if search_query:
                df = get_cocktails_df()
                if not df.empty:
                    # Filter
                    matches = df[
                        df['name'].str.lower().str.contains(search_query.lower()) |
                        df['ingredients'].str.lower().str.contains(search_query.lower())
                    ]
                    
                    if matches.empty:
                        st.warning("No cocktails found matching your query.")
                    else:
                        st.success(f"Found {len(matches)} cocktails:")
                        for _, row in matches.head(10).iterrows():
                            # Format ingredients list
                            try:
                                ing_list = eval(row['ingredients'])
                                ing_str = ", ".join(ing_list)
                            except:
                                ing_str = row['ingredients']
                                
                            st.markdown(f"""
                            <div class="card">
                                <div class="card-title">🍹 {row['name']}</div>
                                <div class="card-meta">Category: {row['category']} | Glassware: {row['glassware_recommendation']} | Strength: {row['abv_category']}</div>
                                <div class="card-content">
                                    <strong>Ingredients:</strong> {ing_str}<br/>
                                    <strong>Instructions:</strong> {row['instructions']}<br/>
                                    <strong>Meaning/Vibe:</strong> {row['meaning_and_history']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
        with tab3:
            st.markdown("#### Dynamic ABV Calculator")
            st.write("Build a custom drink formula and estimate its overall Alcohol By Volume (ABV).")
            
            # Render rows
            ingredients_to_calculate = []
            for idx, ing in enumerate(st.session_state.abv_ingredients):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    ing_name = st.text_input(f"Ingredient {idx+1} Name", value=ing["name"], key=f"abv_name_{idx}")
                with col2:
                    ing_vol = st.number_input(f"Volume (ml)", min_value=1.0, value=ing["volume_ml"], key=f"abv_vol_{idx}")
                with col3:
                    ing_abv = st.number_input(f"ABV (%)", min_value=0.0, max_value=100.0, value=ing["abv"], key=f"abv_pct_{idx}")
                with col4:
                    # Delete button
                    st.write("")
                    st.write("")
                    if st.button("❌", key=f"abv_del_{idx}"):
                        st.session_state.abv_ingredients.pop(idx)
                        st.rerun()
                        
                ingredients_to_calculate.append({"name": ing_name, "volume_ml": ing_vol, "abv": ing_abv})
                
            if st.button("➕ Add Ingredient"):
                st.session_state.abv_ingredients.append({"name": "", "volume_ml": 45.0, "abv": 40.0})
                st.rerun()
                
            if st.button("🧪 Calculate ABV"):
                # Run math locally
                total_vol = 0.0
                total_alc = 0.0
                for ing in ingredients_to_calculate:
                    total_vol += ing["volume_ml"]
                    total_alc += (ing["volume_ml"] * ing["abv"] / 100.0)
                    
                if total_vol > 0:
                    final_abv = (total_alc / total_vol) * 100.0
                    
                    if final_abv == 0:
                        strength = "Mocktail (Non-alcoholic)"
                        color = "#4CAF50"
                    elif final_abv < 10:
                        strength = "Low ABV"
                        color = "#2196F3"
                    elif final_abv < 20:
                        strength = "Medium ABV"
                        color = "#FF9800"
                    else:
                        strength = "Strong ABV"
                        color = "#F44336"
                        
                    st.markdown(f"""
                    <div class="card" style="border-left: 5px solid {color};">
                        <div class="card-title" style="color: {color};">CALCULATION RESULT</div>
                        <div class="card-content">
                            <strong>Total Drink Volume:</strong> {round(total_vol, 1)} ml<br/>
                            <strong>Estimated ABV:</strong> <span style="font-size: 1.5em; font-weight: bold; color: {color};">{round(final_abv, 1)}%</span><br/>
                            <strong>Strength Category:</strong> {strength}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Please enter a total volume greater than 0.")
                    
        with tab4:
            st.markdown("#### Custom Cocktail Menu Builder")
            st.write("Select cocktails from the database to compile into a premium, styled HTML menu.")
            
            df = get_cocktails_df()
            if not df.empty:
                # Multiselect list of cocktails
                cocktail_names = df["name"].tolist()
                selected_names = st.multiselect("Select Drinks for Menu:", cocktail_names)
                
                menu_title = st.text_input("Menu Title:", "THE ARTISAN LOUNGE")
                
                if selected_names:
                    # Filter df rows matching selection
                    selected_df = df[df["name"].isin(selected_names)]
                    selected_list = selected_df.to_dict('records')
                    
                    # Generate Menu HTML
                    exporter = MenuExporter(menu_title=menu_title)
                    html_menu = exporter.generate_html_menu(selected_list)
                    
                    st.success(f"{len(selected_names)} drinks compiled!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        # Preview HTML in frame
                        st.markdown("##### Menu Preview")
                        st.components.v1.html(html_menu, height=500, scrolling=True)
                    with col2:
                        st.markdown("##### Download Exported Menu")
                        st.write("Click below to download the responsive, styled HTML menu file. You can open it in any web browser and print it directly to PDF.")
                        st.download_button(
                            label="📥 Download HTML Menu",
                            data=html_menu,
                            file_name="premium_cocktail_menu.html",
                            mime="text/html"
                        )
            else:
                st.warning("No cocktail data loaded. Run the enrichment pipeline first.")

if __name__ == "__main__":
    main()
