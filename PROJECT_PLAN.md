# Project Plan

## Mục Tiêu

Hoàn thiện Legal Multi-Agent System thành một demo A2A chạy ổn định, có tài liệu
nhất quán và đủ kiểm tra tự động để dùng trong codelab.

## Phase 1: Repository Baseline

Trạng thái: Hoàn thành

- Đồng bộ lệnh chạy và đường dẫn tài liệu với cấu trúc repo.
- Bổ sung `exercises/SOLUTIONS.md`.
- Làm rõ trạng thái các bài tập đã có implementation.
- Thêm smoke tests offline cho registry, routing, graph và A2A response parser.
- Xác minh compile Python và cú pháp shell.

## Phase 2: End-to-End Validation

Trạng thái: Chưa thực hiện

- Khởi động registry, dashboard và bốn agent.
- Kiểm tra health endpoint và agent registration.
- Gửi câu hỏi qua Customer Agent bằng `test_client.py`.
- Xác minh trace ID đi xuyên suốt Customer, Law, Tax và Compliance Agent.
- Ghi nhận latency và lỗi theo từng LLM provider.

## Phase 3: Runtime Hardening

Trạng thái: Chưa thực hiện

- Thêm shutdown cleanup cho `start_all.sh`.
- Chuẩn hóa timeout, retry và thông báo lỗi giữa các service.
- Thêm cấu hình URL cho benchmark thay vì hardcode.
- Bổ sung test cho lỗi registry, agent không khả dụng và response rỗng.
- Kiểm tra tương thích với phiên bản A2A SDK đang khóa trong `uv.lock`.

## Phase 4: Codelab Quality

Trạng thái: Chưa thực hiện

- Tách rõ skeleton bài tập và lời giải tham khảo.
- Kiểm tra toàn bộ lệnh trong `CODELAB.md`, `INSTRUCTOR_GUIDE.md` và
  `QUICK_REFERENCE.md`.
- Thêm expected output cho từng stage.
- Bổ sung troubleshooting cho OpenRouter, Ollama và port conflict.

## Definition of Done

- `python -m unittest discover -s tests -v` chạy thành công.
- `python -m compileall` không báo lỗi.
- Full system khởi động và đăng ký đủ bốn agent.
- `test_client.py` nhận được câu trả lời A2A hoàn chỉnh.
- Không còn link nội bộ hoặc lệnh chạy sai trong tài liệu.
