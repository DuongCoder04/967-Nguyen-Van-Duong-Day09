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

Trạng thái: Hoàn thành

- Registry báo healthy và có đủ bốn agent đăng ký.
- Dashboard trả lời health check.
- `test_client.py` gửi thành công một request qua Customer Agent.
- Dashboard lưu trace hoàn chỉnh của Customer, Law, Tax, Compliance và aggregate.
- Baseline quan sát với `LLM_PROVIDER=ollama`, `llama3.1:8b`: khoảng 230 giây.
- Phát hiện và sửa lỗi Customer Agent làm mất nội dung specialist khi format lại.

## Phase 3: Runtime Hardening

Trạng thái: Hoàn thành

- `start_all.sh` có startup guard, health checks và shutdown cleanup.
- Agent fail-fast nếu không đăng ký được với Registry.
- URL và timeout được cấu hình bằng environment variables.
- Benchmark đóng HTTP client đúng cách và chỉ báo số liệu thực đo.
- Có test cho registry failure, delegation failure và response rỗng.
- Legacy `A2AClient` vẫn chạy với SDK hiện tại; cảnh báo migration đã được ghi lại.

## Phase 4: Codelab Quality

Trạng thái: Hoàn thành

- Skeleton nằm trong `exercises/templates/`; lời giải chạy được nằm ở thư mục cha.
- Các đường dẫn/lệnh chạy trong tài liệu đã được đồng bộ.
- `CODELAB.md` có expected output cho từng stage.
- `TROUBLESHOOTING.md` bao phủ OpenRouter, Ollama, timeout, port và trace.

## Definition of Done

- `python -m unittest discover -s tests -v` chạy thành công.
- `python -m compileall` không báo lỗi.
- Full system khởi động và đăng ký đủ bốn agent.
- `test_client.py` nhận được câu trả lời A2A hoàn chỉnh.
- Không còn link nội bộ hoặc lệnh chạy sai trong tài liệu.

## Verification Record

- 15 offline tests: pass.
- Python compileall: pass.
- `bash -n start_all.sh`: pass.
- Startup guard với instance đang chạy: pass.
- E2E A2A với Ollama: pass, khoảng 230 giây.

Sau khi restart các service, chạy lại `test_client.py` để xác nhận bản sửa
Customer Agent trả nguyên nội dung specialist qua HTTP.
