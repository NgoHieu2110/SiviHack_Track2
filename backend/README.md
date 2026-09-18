# Tender Matching Backend (FastAPI + Gemini)

Backend độc lập nhận `CompanyProfile` từ frontend Next.js, đọc các file
`.md` chứa thông tin gói thầu trong thư mục `tenders/`, gọi Gemini để
chấm điểm mức độ phù hợp, và trả về `{ matches: TenderMatch[] }` — đúng
shape mà file `api.ts` phía frontend của bạn đang gọi.

## 1. Cài đặt

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Cấu hình

```bash
cp .env.example .env
```

Sửa `.env`:

```
GEMINI_API_KEY=<API key thật của bạn từ https://aistudio.google.com/apikey>
GEMINI_MODEL=gemini-2.5-flash
TENDERS_DIR=./tenders
ALLOWED_ORIGINS=http://localhost:3000
```

> **Lưu ý về model:** theo tài liệu Google tại thời điểm viết file này,
> Gemini 2.5 dự kiến ngừng hỗ trợ vào tháng 10/2026. Nếu `gemini-2.5-flash`
> báo lỗi, kiểm tra model mới nhất tại
> https://ai.google.dev/gemini-api/docs/models và đổi `GEMINI_MODEL`
> trong `.env` — code không cần sửa gì thêm.

## 3. Bỏ 10 file `.md` gói thầu vào thư mục `tenders/`

Mỗi file cần có **YAML frontmatter** ở đầu, xem file mẫu
`tenders/example-tender.md`:

```markdown
---
id: "T-2026-014"
title: "Reconstruction of Provincial Road 42"
authority: "Department of Transport, Hai Duong Province"
cpvCode: "45230000"
cpvLabel: "45230000 — Roads, railways, pipelines, communication lines"
contractNature: "Works"
location: "Hai Duong, Vietnam"
value: 18500000000
currency: "VND"
deadline: "2026-11-30"
role: "Sole contractor"
requiredCertificates:
  - "ISO 9001 (Quality)"
  - "SOA / Classification Certificate"
insuranceRequired: 500000000
guaranteeRequired: "Performance guarantee (5-10%)"
startDate: "2027-01-15"
---
Nội dung mô tả tự do của dự án ở đây — trở thành field `description`.
```

Các field khớp chính xác với `Tender` trong `tender-types.ts` của bạn.

**Nếu file thật của bạn có cấu trúc khác** (không có frontmatter, hoặc
tên field khác), gửi tôi 1 file mẫu thật và tôi sẽ chỉnh `tender_loader.py`
cho khớp — hiện tại đây là format mặc định hợp lý để pipeline chạy được
ngay.

Xóa `example-tender.md` khi đã có file thật, hoặc để lại cũng không sao
(chỉ là một tender bình thường trong tập dữ liệu).

## 4. Chạy backend

```bash
uvicorn main:app --reload --port 8000
```

Kiểm tra: mở `http://localhost:8000/health` — sẽ thấy số file đã load và
lỗi parse (nếu có).

## 5. Nối với frontend

Trong project Next.js, file `.env.local`:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Frontend của bạn (`api.ts`) sẽ tự động POST tới
`http://localhost:8000/tenders/match` thay vì dùng mock — không cần sửa
gì trong `api.ts`.

## Cơ chế cache / reload file .md

- Mỗi request, backend kiểm tra `mtime` (thời gian sửa đổi) của từng file
  `.md`. File nào mới/đổi/xóa sẽ tự động được đọc lại — **không cần
  restart server** khi bạn sửa nội dung gói thầu.
- Muốn ép reload ngay lập tức: `POST http://localhost:8000/admin/reload`
- File `.md` bị lỗi format (thiếu frontmatter, thiếu field bắt buộc) sẽ
  bị bỏ qua và báo lỗi trong `/health` thay vì làm sập cả API.

## Cấu trúc project

```
backend/
├── main.py            # FastAPI app, route POST /tenders/match
├── models.py           # Pydantic models khớp tender-types.ts
├── tender_loader.py     # Đọc + cache 10 file .md
├── gemini_service.py    # Gọi Gemini, chấm điểm, ghép kết quả
├── requirements.txt
├── .env.example
└── tenders/
    └── example-tender.md
```

## Cách hoạt động (luồng xử lý)

1. Frontend POST `CompanyProfile` (JSON) tới `/tenders/match`.
2. Backend đọc toàn bộ tender từ `tenders/*.md` (dùng cache, không đọc
   lại file không đổi).
3. Ghép `CompanyProfile` + danh sách tender thành 1 prompt, gửi cho
   Gemini, yêu cầu trả về JSON: `{id, score, reasons, considerations, summary}`
   cho từng tender.
4. Backend **tự ráp lại** `TenderMatch` bằng dữ liệu `Tender` gốc từ file
   (không lấy trực tiếp từ Gemini) để tránh AI bịa sai số liệu — Gemini
   chỉ quyết định điểm số và lý do, không được phép sửa dữ liệu gốc.
5. Trả về `{ matches: TenderMatch[] }`, sắp xếp theo `score` giảm dần.
