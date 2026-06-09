# Đáp Án Bài Tập

Tài liệu này tóm tắt các thay đổi cần thực hiện. Code hoàn chỉnh nằm ngay trong
hai file bài tập để có thể chạy và đối chiếu trực tiếp.

## Exercise 2: Tools và Knowledge Base

File: `exercise_2_tools.py`

1. Thêm entry `labor_law` vào `LEGAL_KNOWLEDGE` với các từ khóa tiếng Việt và
   tiếng Anh liên quan đến lao động, sa thải và chấm dứt hợp đồng.
2. Tạo tool `check_statute_of_limitations(case_type)` với các trường hợp
   `contract`, `tort` và `property`.
3. Đăng ký tool mới:

```python
tools = [search_legal_knowledge, check_statute_of_limitations]
llm_with_tools = llm.bind_tools(tools)
```

Chạy kiểm tra:

```bash
uv run python exercises/exercise_2_tools.py
```

## Exercise 4: Multi-Agent với Privacy Agent

File: `exercise_4_multiagent.py`

1. Thêm `privacy_analysis` vào shared state với reducer `_last_wins`.
2. Implement `privacy_agent()` để phân tích GDPR, CCPA và data breach.
3. Route các câu hỏi chứa `data`, `privacy`, `gdpr`, `dữ liệu`, `rò rỉ` hoặc
   `breach` tới privacy agent.
4. Đăng ký node và edge:

```python
graph.add_node("privacy_agent", privacy_agent)
graph.add_edge("privacy_agent", "aggregate_results")
```

5. Đưa `privacy_analysis` vào bước tổng hợp kết quả.

Chạy kiểm tra:

```bash
uv run python exercises/exercise_4_multiagent.py
```

## Ghi Chú

Các script gọi LLM thật, vì vậy cần cấu hình `.env` và có OpenRouter hoặc
Ollama đang hoạt động. Smoke tests trong `tests/` chỉ kiểm tra cấu trúc và
không gửi request tới LLM.
