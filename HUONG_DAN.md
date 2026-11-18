# Hướng dẫn sử dụng Explainer Studio (tiếng Việt)

Explainer Studio là bộ skill và công cụ cho Claude Code để làm video YouTube kiểu hoạt hình giải thích: video dài 10–15 phút và Shorts dọc 1080×1920.

Claude làm phần lớn công việc:
- tìm chủ đề;
- viết kịch bản và kiểm chứng nguồn;
- đọc giọng bằng ElevenLabs, có mốc thời gian từng chữ;
- dựng từng cảnh bằng HyperFrames/GSAP: nhân vật nói, hiệu ứng âm thanh, ảnh thật;
- tự QA, master âm lượng −14 LUFS;
- cắt Shorts và soạn gói upload.

Bạn chỉ duyệt ở 5 cổng: chủ đề, kịch bản, hook, bản dựng cuối, đăng.

---

## 1. Cài đặt (khoảng 5 phút)

### 1.1. Phần mềm cần có

| Cần | Phiên bản | Để làm gì |
|---|---|---|
| Claude Code | mới nhất | chạy skill và agent |
| Python | 3.10+ | các tool |
| Node.js + npm | 18+ | trình render HyperFrames (lần đầu tự tải Chromium) |
| ffmpeg, ffprobe | 6+ | render, mix, master, QA |
| fontconfig | bất kỳ | tìm font kênh |
| tesseract | tuỳ chọn | kiểm tra chữ trên thumbnail |

Lệnh cài theo hệ điều hành:

```bash
# Ubuntu / Debian / WSL2
sudo apt-get install -y python3 python3-venv nodejs npm ffmpeg fontconfig fonts-noto tesseract-ocr git
# Arch / CachyOS
sudo pacman -S --needed python nodejs npm ffmpeg fontconfig noto-fonts tesseract tesseract-data-eng git
# macOS
brew install python node ffmpeg fontconfig tesseract git && brew install --cask font-noto-sans
```

Dùng Windows thì cài WSL2 (Ubuntu) rồi chạy dòng Ubuntu ở trên.

### 1.2. Tải repo và chạy setup

```bash
git clone https://github.com/<owner>/explainer-studio.git
cd explainer-studio
./setup.sh
```

`setup.sh` làm lần lượt:
1. kiểm tra phần mềm, thiếu gì thì in lệnh cài;
2. tạo `.venv` và cài thư viện Python;
3. tải sẵn HyperFrames;
4. hỏi từng API key (gõ không hiện chữ, Enter để bỏ qua) rồi ghi vào `.env`, quyền 600 và không bao giờ bị commit;
5. kiểm tra từng key với server thật mà không in key ra.

Kết quả mong đợi:

```
== API keys
OK       OPENROUTER_API_KEY
OK       KIE_API_KEY
OK       PEXELS_API_KEY
OK       PIXABAY_API_KEY
SET      FAL_API_KEY            not tested
Ready.
```

`FAL_API_KEY` hiện `SET` là bình thường: FAL không có endpoint kiểm tra miễn phí, lần tạo giọng đầu tiên sẽ chứng minh key chạy được.

---

## 2. API key: lấy ở đâu, tốn bao nhiêu

| Key | Lấy ở | Dùng cho | Bắt buộc? | Chi phí |
|---|---|---|---|---|
| `FAL_API_KEY` | https://fal.ai/dashboard/keys | giọng đọc ElevenLabs có mốc thời gian từng chữ | **Có** | ~0,02 USD / Short, ~1–2 USD / video dài |
| `KIE_API_KEY` | https://kie.ai/api-key | vẽ hình, đạo cụ hoạt hình | Không | ~0,03 USD / hình |
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys | Gemini xem video đối thủ để rút ra style kênh | Không | vài cent / video |
| `PEXELS_API_KEY` | https://www.pexels.com/api/ | ảnh và video stock | Không | miễn phí |
| `PIXABAY_API_KEY` | https://pixabay.com/api/docs/ | ảnh và video stock | Không | miễn phí |

Thiếu key nào thì chỉ tính năng đó tắt, phần còn lại vẫn chạy. Wikimedia Commons, NASA và Internet Archive không cần key.

**4 cách nạp key:**

```bash
./setup.sh --skip-install                 # 1. gõ tay, ẩn chữ
./setup.sh --skip-install --from-env      # 2. lấy từ biến môi trường đã export
./setup.sh --skip-install --keys ~/team.env   # 3. lấy từ file KEY=giá_trị
```

4. Mở `claude` trong thư mục repo, gõ **"setup"** rồi dán key vào chat. Claude ghi vào `.env` và không lặp lại key.

Kiểm tra lại key bất cứ lúc nào:

```bash
.venv/bin/python explainer/check_setup.py
```

---

## 3. Demo khi có đủ key (khoảng 2 phút, khoảng 0,05 USD)

```bash
./demo.sh            # giọng mặc định Rachel
./demo.sh Adam       # hoặc tên giọng ElevenLabs khác
```

Demo tự dựng từ đầu một Short 25 giây về chủ đề "Bút chì không có chì":

| Bước | Dùng key | Kết quả |
|---|---|---|
| 1. Kịch bản | không | 65 chữ: câu hook, ý chính, câu dẫn về video dài |
| 2. Giọng đọc | FAL | `s1.mp3` và mốc thời gian từng chữ (`words.json`) |
| 3. Ảnh thật | Pexels (không có key thì lấy Wikimedia) | ảnh bút chì kèm tác giả và giấy phép trong `CREDITS.md` |
| 4. Hình vẽ | KIE (không có key thì bỏ qua) | bút chì cắt đôi lộ lõi graphite, kiểu hoạt hình |
| 5. Dựng và xuất | không | HyperFrames check, render, master −14 LUFS, QA, contact sheet |

Kết quả nằm ở:
- `explainer/film/demo/shorts/short_1.mp4`: video 1080×1920, 30 fps;
- `explainer/film/demo/shorts/short_1_contact.jpg`: mỗi giây một khung, có viền đỏ đánh dấu vùng UI của Shorts;
- `explainer/film/demo/media/CREDITS.md`: dòng credit để dán vào mô tả video.

Diễn biến trong video:
- Giây 0: tiêu đề "NO **LEAD**?" và ảnh thật đã có sẵn trên màn hình (frame đầu là hook).
- Khi giọng đọc chữ "graphite": hình bút chì pop lên, kèm tiếng pop.
- Khi đọc chữ "clay": nhãn "GRAPHITE + CLAY" hiện ra.
- Suốt video: phụ đề từng chữ, từ đang đọc được tô màu nhấn.
- Câu cuối: end card "FULL STORY ON THE CHANNEL" hiện đúng lúc đọc câu dẫn.

QA sẽ báo vài chỗ đứng hình hơn 1 s và một đoạn im lặng ở cuối. Báo vậy là đúng: demo cố ý đơn giản. Khi làm thật, Claude đạo diễn từng nhịp (skill `explainer-shorts`) để hết các cảnh báo này.

Chạy lại `./demo.sh` thì không tốn thêm tiền: giọng, ảnh và hình đã được cache. Muốn làm lại từ đầu thì xoá `explainer/film/demo` và `explainer/state/demo_pencil.json`.

---

## 4. Làm kênh thật

### 4.1. Tạo kênh

```bash
./setup.sh --new-channel ten_kenh "Tên Kênh"
```

Lệnh này tạo các thư mục sau. Git đều bỏ qua chúng, nên dữ liệu kênh chỉ nằm trên máy bạn.

| Đường dẫn | Chứa gì |
|---|---|
| `explainer/channels/ten_kenh/` | STYLE.md, style.json, LEARNINGS.md, trend_sources.json |
| `explainer/shorts/styles/ten_kenh.json` | bảng màu, font, giọng, avatar, nhân vật |
| `explainer/brand/ten_kenh/` | avatar, ảnh nhân vật |
| `explainer/kit/music/ten_kenh/` | nhạc nền (kèm CREDITS.md) |

### 4.2. Nói với Claude theo thứ tự

Mở `claude` trong thư mục repo rồi nói:

1. **"build the channel style for ten_kenh"**: Claude đo 5–12 kênh đối thủ (nhịp cắt, tỉ lệ host, màu, chữ, âm thanh, hook, thumbnail) rồi viết STYLE.md. Có sẵn kênh đối thủ thì đưa luôn.
2. **"draft trend sources for ten_kenh"**: Claude soạn danh sách từ khoá tin tức, RSS, subreddit, thực thể quen thuộc.
3. Sửa `explainer/shorts/styles/ten_kenh.json`:
   - `voice`: tên hoặc ID giọng ElevenLabs.
   - màu `bg`, `primary`, `accent`; chữ trên nền phải đạt độ tương phản 3:1, HyperFrames sẽ kiểm tra.
   - `font_display`: font đã cài (xem bằng `fc-list`).
   - `host_poses`: để `{}` nếu kênh không có nhân vật.
4. Bỏ 2–4 bài nhạc có giấy phép vào `explainer/kit/music/ten_kenh/`, ví dụ Kevin MacLeod hay Scott Buckley (CC BY 4.0), hoặc YouTube Audio Library.

### 4.3. Làm việc hằng ngày

| Nói với Claude | Claude làm |
|---|---|
| "plan the next video for ten_kenh" | chạy trend radar, đưa 3–5 chủ đề và tiêu đề, chờ bạn chọn (cổng G1) |
| "write the script" | nguồn, CLAIMS, FACTCHECK độc lập, SCRIPT (cổng G2) |
| "voice and direct chapter 1" | tạo giọng, beat plan, dựng chương 1, QA hook (cổng G3) |
| "direct the remaining chapters" | các agent dựng song song, ghép, master, `qa_film` |
| "make the Short for <video>" | Short dọc 30–50 s, hook riêng, end card dẫn về video dài |
| "upload pack" | tiêu đề, mô tả, chương, tag, credit, comment ghim (cổng G5) |
| "48 h review" / "7 day review" | đọc số liệu Studio, ghi LEARNINGS.md |

Lịch chuẩn: mỗi kênh 1 video dài mỗi ngày, mỗi video đi qua 2 ngày (day −2: nghiên cứu và kịch bản; day −1: dựng và QA). Ngân sách mặc định tối đa 10 USD mỗi video, gồm cả Short, và Claude báo lại đã tiêu bao nhiêu.

### 4.4. Upload

Repo không có uploader qua API. Claude dùng trình duyệt Playwright (cài bằng `/plugin` → `playwright`) sau khi bạn tự đăng nhập YouTube Studio một lần. Claude **không bao giờ** upload, hẹn giờ hay public khi chưa có bạn đồng ý cho từng video.

---

## 5. Bảo mật

- `.env`, `.venv`, `explainer/film`, `vo`, `brand`, `kit/music` và mọi thư mục kênh thật đều nằm trong `.gitignore`.
- Mọi script đọc key qua `explainer/envload.py`, theo thứ tự: biến môi trường → `./.env` → `explainer/.env`. Không script nào in key ra.
- Claude được dặn trong `CLAUDE.md` và các skill: không đọc hay in `.env`, không đưa key vào commit, log hay memory.
- Trước khi push, nên quét thêm một lượt: `gitleaks git .` (https://github.com/gitleaks/gitleaks).

## 6. Xử lý lỗi thường gặp

| Lỗi | Cách sửa |
|---|---|
| `X_API_KEY is not set` | `./setup.sh --skip-install`, hoặc gõ "setup" cho Claude |
| `check_setup.py` báo `FAIL` ở một key | key sai hoặc đã bị thu hồi: tạo key mới rồi chạy lại setup |
| `font not found` | cài font, hoặc ghi đường dẫn .ttf vào `font_display_file` |
| HyperFrames báo contrast `need 3:1` | chỉnh `primary` / `accent` cho tương phản hơn |
| Lần đầu `npx hyperframes` chạy lâu | đang tải Chromium một lần, cứ chờ |
| `ModuleNotFoundError` | chạy bằng `.venv/bin/python`, hoặc `source .venv/bin/activate` trước |
| Thumbnail tách nền xấu | `WITH_REMBG=1 ./setup.sh` để cài rembg |
