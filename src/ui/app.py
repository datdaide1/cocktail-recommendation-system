import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Append src to path
src_path = Path(__file__).resolve().parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

# Set page configs
st.set_page_config(
    page_title="🍸 AI Lounge - Cocktail & Bar Assistant",
    page_icon="🍸",
    layout="wide"
)

# Custom CSS for Luxury Dark Mode
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
        color: #F0F2F6;
    }
    .stButton>button {
        background-color: #D4AF37;
        color: #0E1117;
        font-weight: bold;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #AA7C11;
        color: #F0F2F6;
    }
    .sidebar .sidebar-content {
        background-color: #1A1F2C;
    }
    .card {
        background-color: #1F2635;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #D4AF37;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🍸 AI Lounge - Cocktail & Bar Assistant")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("Configuration")
    role = st.sidebar.radio("Choose Role:", ["🍸 Guest (Customer)", "🤵 Bartender (Professional)"])
    
    # UI Layout based on Role
    if role == "🍸 Guest (Customer)":
        st.subheader("Welcome to Guest Mode")
        st.markdown("Chat with the AI Concierge to find cocktails matching your mood, or discover top-rated bars in Hanoi & Ho Chi Minh City.")
        
        tab1, tab2 = st.tabs(["💬 Chat with AI Concierge", "📍 Discover Bars"])
        
        with tab1:
            st.markdown("#### Chat")
            user_msg = st.text_input("Enter your request (e.g. 'I want a sour gin cocktail for tonight'):")
            if st.button("Send"):
                st.info(f"AI Concierge Skeleton received message: '{user_msg}'. Agent implementation will be activated in the next step.")
                
        with tab2:
            st.markdown("#### Explore Premium Bars")
            city = st.selectbox("City:", ["Hanoi", "Ho Chi Minh City"])
            district = st.text_input("District (e.g. Hoan Kiem, District 1):")
            style = st.selectbox("Style/Vibe:", ["Any", "Speakeasy", "Rooftop", "Cozy Lounge", "Jazz Bar"])
            
            if st.button("Search Bars"):
                st.write("Search results from `bars_vietnam.csv` will be displayed here.")
                
    else:
        st.subheader("Welcome to Bartender Mode")
        st.markdown("A specialized toolkit for professional bartenders to lookup recipes, calculate ABV, and compile menus.")
        
        tab1, tab2, tab3 = st.tabs(["📜 Recipes & Mixology", "⚗️ ABV Calculator", "📋 Menu Builder"])
        
        with tab1:
            st.markdown("#### Recipe Lookup")
            search_name = st.text_input("Enter cocktail name:")
            if st.button("Find Recipe"):
                st.write("Detailed recipe and instructions will be shown here.")
                
        with tab2:
            st.markdown("#### Automatic ABV Calculator")
            st.write("Enter ingredients details to estimate the overall ABV percentage of your mix.")
            
        with tab3:
            st.markdown("#### Menu Builder")
            st.write("Select cocktails to compile and export a beautiful custom menu.")

if __name__ == "__main__":
    main()
