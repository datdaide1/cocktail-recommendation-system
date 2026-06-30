# Phase 2 Evaluation Notes

## Những việc đã hoàn thành
1. **Thay đổi công cụ chấm điểm**: Bỏ thư viện `autoevals` của Braintrust vì bị dính proxy (Braintrust Proxy chặn các model chưa được hỗ trợ, gây ra lỗi 404/401). Đã viết lại pipeline chấm điểm độc lập bằng cách dùng thẳng LangChain gọi trực tiếp API.
2. **Cấu hình Model**:
   - **Người thi (Agent)**: Sử dụng mô hình `gemini-3.1-flash-lite` với 3 API keys fallback để chịu tải.
   - **Giám khảo (Evaluator)**: Sử dụng mô hình `deepseek-v4-pro` thông qua NVIDIA NIM.
3. **Mở rộng Metrics**: Tự xây dựng lại bộ 6 metrics đầy đủ thay vì chỉ 2 metrics như trước:
   - Factuality (Bám sát yêu cầu)
   - Relevancy (Trả lời đúng trọng tâm)
   - Safety (An toàn, không gợi ý cồn cho trẻ vị thành niên)
   - Context Relevance (Context móc ra từ DB có hữu ích không)
   - Helpfulness (Ngắn gọn, xúc tích, dễ hiểu)
   - B2B Tool Called (Đếm xem hệ thống có nhận diện đúng B2B và gọi tool tính toán không)
4. **Tối ưu Tốc độ & Giới hạn Rate Limit**:
   - Khắc phục lỗi 429 từ Gemini (15 RPM) bằng cách thêm delay 8s giữa mỗi vòng lặp Agent.
   - Khắc phục lỗi 429 từ NVIDIA NIM (Giới hạn luồng song song) bằng cách gộp cả 5 LLM metrics vào một Prompt JSON duy nhất.
   - Sử dụng `asyncio.Semaphore(2)` để xếp hàng, chỉ cho 2 lượt chấm điểm chạy song song cùng lúc nhằm không làm sập server NVIDIA.

## Những vấn đề còn đang vướng mắc (Khó khăn)
1. **Tốc độ phản hồi của NVIDIA NIM**: Server NVIDIA NIM ở gói miễn phí xử lý endpoint `deepseek-v4-pro` quá chậm (trung bình ngâm request mất 3-4 phút mới trả về kết quả). Việc này khiến tổng thời gian chấm điểm 12 cases test kéo dài tới hơn 20 phút (thay vì vài giây như các LLM khác). Nếu muốn scale lên 170 cases thì sẽ tốn rất nhiều thời gian.
2. **Deterministic Behavior khi test**: Phải thiết lập `temperature = 0.0` trong `nodes.py` để đảm bảo Agent sinh ra kết quả ổn định mỗi lần chạy test (không bị lệch metrics do xác suất của LLM). Khi đưa lên Production sẽ cần sửa lại `0.7`. (Đã tự động set lại thành `0.7` ở commit này để dọn đường cho Phase 3).
3. **Biến môi trường `.env`**: Cần cực kỳ cẩn thận với định dạng file `.env`. Tránh để khoảng trắng ở cuối hoặc các ký tự null byte (như lỗi UTF-8/encoding) vì thư viện LangChain sẽ load sai API Key và đẩy lên server (gây lỗi 401 Unauthorized do Header Bearer bị lỗi).

## Chuẩn bị cho Phase 3
- Môi trường đã được dọn dẹp sạch sẽ, file kết quả tạm thời (`local_eval_results.json`) đã được đưa vào `.gitignore`.
- Nhiệt độ (`temperature`) của các models (cả Gemini và GPT) đã được thiết lập lại về `0.7` để chuẩn bị cho giao diện thật.
- Các script chạy test như `run_local_evals.py` đã được lưu trữ an toàn trong nhánh `dev` để dùng cho sau này.
