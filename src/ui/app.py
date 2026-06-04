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
    role = st.sidebar.radio("Chọn vai trò:", ["🍸 Guest (Khách hàng)", "🤵 Bartender (Chuyên gia)"])
    
    # UI Layout based on Role
    if role == "🍸 Guest (Khách hàng)":
        st.subheader("Chào mừng đến với Chế độ Khách hàng (Guest Mode)")
        st.markdown("Hãy trò chuyện với AI Concierge để tìm kiếm ly cocktail phù hợp với tâm trạng hoặc tìm các quán bar cực chất tại Hà Nội & TP.HCM.")
        
        tab1, tab2 = st.tabs(["💬 Chat với AI Concierge", "📍 Tìm kiếm Quán Bar"])
        
        with tab1:
            st.markdown("#### Chat")
            user_msg = st.text_input("Nhập yêu cầu của bạn (ví dụ: 'Tôi muốn tìm cocktail vị chua nhẹ cho tối nay'):")
            if st.button("Gửi"):
                st.info(f"AI Concierge Skeleton nhận tin nhắn: '{user_msg}'. Tính năng AI hoàn thiện sẽ sẵn sàng ở bước tiếp theo.")
                
        with tab2:
            st.markdown("#### Khám phá Quán Bar nổi tiếng")
            city = st.selectbox("Thành phố:", ["Hanoi", "Ho Chi Minh City"])
            district = st.text_input("Quận (ví dụ: Hoan Kiem, District 1):")
            style = st.selectbox("Phong cách:", ["Bất kỳ", "Speakeasy", "Rooftop", "Cozy Lounge", "Jazz Bar"])
            
            if st.button("Tìm kiếm Quán Bar"):
                st.write("Kết quả tìm kiếm mẫu từ `bars_vietnam.csv`...")
                
    else:
        st.subheader("Chào mừng đến với Chế độ Bartender (Bartender Mode)")
        st.markdown("Chuyên trang công cụ hỗ trợ Bartender tìm kiếm công thức chuẩn xác, tính toán ABV và thiết kế Menu.")
        
        tab1, tab2, tab3 = st.tabs(["📜 Công thức & Kỹ thuật", "⚗️ Tính toán ABV", "📋 Menu Builder"])
        
        with tab1:
            st.markdown("#### Tra cứu Công thức")
            search_name = st.text_input("Nhập tên cocktail:")
            if st.button("Tìm công thức"):
                st.write("Chi tiết công thức sẽ được hiển thị ở đây.")
                
        with tab2:
            st.markdown("#### Tính toán ABV tự động")
            st.write("Nhập thông tin các nguyên liệu để tính toán ABV của ly cocktail tự chế.")
            
        with tab3:
            st.markdown("#### Menu Builder")
            st.write("Tích chọn các ly cocktail để xuất bản thực đơn cocktail PDF/HTML cho quán của bạn.")

if __name__ == "__main__":
    main()
