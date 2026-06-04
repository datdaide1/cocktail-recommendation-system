# 🍸 AI Cocktail Assistant & Vietnam Bar Directory

Hệ thống gợi ý Cocktail & đề xuất Quán Bar thông minh dựa trên kiến trúc **Multi-Agent (Orchestrator-Specialist)** kết hợp công nghệ **Gemini API Function Calling (Tool Use)** và **Hybrid RAG (Tìm kiếm Ngữ nghĩa kết hợp Metadata)**.

---

## 🌟 Tính Năng Nổi Bật

1. **Kiến Trúc Multi-Agent Phân Nhiệm**:
   - **Guest Concierge Agent**: Đóng vai trò Host/Lễ tân thấu hiểu khách hàng, gợi ý đồ uống phù hợp tâm trạng và giới thiệu các quán bar thực tế tại Hà Nội/TP.HCM.
   - **Master Bartender Agent**: Chuyên gia kỹ thuật pha chế cung cấp công thức chuẩn xác, đề xuất nguyên liệu thay thế và phân tích nồng độ cồn (ABV).
2. **Hệ Thống Tool Call Tự Động (Gemini Function Calling)**:
   - Tự động gọi cơ sở dữ liệu để tìm kiếm đồ uống, quán bar, phân tích ABV và tìm nguyên liệu thay thế dựa trên nội dung hội thoại của người dùng.
3. **Pipeline Tự Động Làm Giàu Dữ Liệu (Offline Enrichment Pipeline)**:
   - Sử dụng Gemini API để mở rộng bộ dữ liệu Cocktail truyền thống (Thêm trường Lịch sử, Ý nghĩa, Loại ly chuẩn và Hồ sơ hương vị).
4. **Giao Diện Luxury Dark-Mode**:
   - Thiết kế tối sang trọng mang hơi hướng một Lounge cao cấp với 2 chế độ chuyển đổi mượt mà.
   - Tính năng **Menu Builder**: Tạo thực đơn và in menu PDF/HTML trực quan.

---

## 📂 Cấu Trúc Thư Mục Dự Án

```text
cocktail-recommendation-system/
├── data/
│   ├── raw/                       # File dữ liệu cocktail gốc (final_cocktails.csv)
│   ├── enriched_cocktails.csv     # File dữ liệu đã được AI làm giàu
│   └── bars_vietnam.csv           # Cơ sở dữ liệu quán bar Việt Nam thực tế
├── scripts/
│   └── data_enricher.py           # Script chạy offline để làm giàu dữ liệu qua Gemini
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── cocktail_agents.py     # Lõi xử lý Agents (Orchestrator, Guest, Bartender)
│   ├── tools/
│   │   ├── __init__.py
│   │   └── cocktail_tools.py      # Bộ công cụ (Search DB, ABV Calculator, Substitutions)
│   ├── ui/
│   │   └── app.py                 # Giao diện Streamlit (Dark Theme, Menu Builder)
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # Đọc cấu hình từ file .env
│       └── menu_exporter.py       # Xuất Menu PDF/HTML cho Bartender
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Chuẩn Bị Môi Trường
Tạo môi trường ảo Python và cài đặt các thư viện cần thiết:
```bash
python -m venv venv
# Trên Windows:
.\venv\Scripts\activate
# Trên macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Thiết Lập Cấu Hình
Sao chép file `.env.example` thành `.env` và điền khóa API Gemini của bạn:
```bash
cp .env.example .env
```
Mở file `.env` và điền:
```env
GEMINI_API_KEY=AIzaSy... # Khóa API của bạn
```

### 3. Làm Giàu Dữ Liệu (Offline)
Chạy script làm giàu dữ liệu để nâng cấp bộ dữ liệu cocktail gốc (nếu chưa có sẵn file `enriched_cocktails.csv`):
```bash
python scripts/data_enricher.py
```

### 4. Khởi Chạy Ứng Dụng
```bash
streamlit run src/ui/app.py
```
Ứng dụng sẽ tự động mở tại địa chỉ `http://localhost:8501`.
