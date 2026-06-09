# Bài Tập Thực Hành

Thư mục này chứa bài tập và lời giải tham khảo cho codelab A2A Multi-Agent.

- `templates/*.py.template`: skeleton để học viên sao chép và hoàn thành.
- `exercise_*.py`: lời giải tham khảo có thể chạy trực tiếp.
- `SOLUTIONS.md`: giải thích các thay đổi chính.

## Danh Sách Bài Tập

### Exercise 2: Tools và Knowledge Base
**Skeleton:** `templates/exercise_2_tools.py.template`
**Lời giải:** `exercise_2_tools.py`
**Thời gian:** 10 phút  
**Mục tiêu:** Học cách thêm tools và knowledge base vào LLM

**Nhiệm vụ:**
1. Thêm entry về luật lao động vào `LEGAL_KNOWLEDGE`
2. Tạo tool `check_statute_of_limitations` để kiểm tra thời hiệu khởi kiện
3. Test với câu hỏi về thời hiệu

**Chạy:**
```bash
uv run python exercises/exercise_2_tools.py
```

---

### Exercise 4: Multi-Agent với Privacy Agent
**Skeleton:** `templates/exercise_4_multiagent.py.template`
**Lời giải:** `exercise_4_multiagent.py`
**Thời gian:** 15 phút  
**Mục tiêu:** Mở rộng multi-agent system với agent mới

**Nhiệm vụ:**
1. Implement `privacy_agent` function
2. Thêm conditional routing cho privacy agent
3. Thêm privacy_agent vào graph
4. Test với câu hỏi về data breach

**Chạy:**
```bash
uv run python exercises/exercise_4_multiagent.py
```

---

## Đáp Án

Đáp án chi tiết có trong file `SOLUTIONS.md`. 

**⚠️ Lưu ý:** Hãy cố gắng tự làm trước khi xem đáp án!

---

## Hướng Dẫn Làm Bài

### 1. Bắt Đầu Từ Skeleton
Sao chép file `.py.template` thành file làm bài riêng, sau đó hoàn thành các
comment `TODO`. Dùng file lời giải ở thư mục cha để đối chiếu sau khi làm xong.

### 2. Tìm Gợi Ý
Các comment `# Gợi ý:` cho biết hướng làm.

### 3. Tham Khảo Stages
Code trong `stages/*` là examples tốt để tham khảo.

### 4. Test Thường Xuyên
Sau mỗi thay đổi, chạy lại để kiểm tra.

### 5. Debug
Nếu lỗi:
- Đọc error message cẩn thận
- Check syntax (dấu ngoặc, indentation)
- Thêm `print()` để xem giá trị biến
- So sánh với code trong stages

---

## Bài Tập Nâng Cao (Optional)

Sau khi hoàn thành 2 bài tập chính, bạn có thể thử:

### Challenge 1: Financial Agent
Thêm `financial_agent` vào multi-agent system để phân tích thiệt hại tài chính.

### Challenge 2: Conversation Memory
Implement memory để agent nhớ các câu hỏi trước đó.

### Challenge 3: Custom Tool
Tạo tool gọi API thực (ví dụ: tra cứu luật từ database online).

### Challenge 4: Error Handling
Thêm try-catch và retry logic khi tool fails.

---

## Câu Hỏi Thường Gặp

**Q: Làm sao biết code đúng chưa?**  
A: Chạy file và xem output. Nếu không có error và có kết quả hợp lý là OK.

**Q: Tool không được gọi?**  
A: Check xem đã thêm vào `tools` list và `.bind_tools()` chưa.

**Q: Agent không chạy song song?**  
A: Đảm bảo dùng `Send()` API và các agents không phụ thuộc lẫn nhau.

**Q: Import error?**  
A: Chạy `uv sync` để cài đặt dependencies.

---

## Hỗ Trợ

Nếu gặp khó khăn:
1. Đọc lại phần lý thuyết trong `CODELAB.md`
2. Xem `QUICK_REFERENCE.md` cho syntax
3. Hỏi bạn bè hoặc giảng viên
4. Check `SOLUTIONS.md` (last resort!)

**Chúc bạn làm bài tốt! 💪**
