
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = 20_000_000
BASE = Path(__file__).resolve().parent
MAX_BYTES = 15 * 1024 * 1024
LABEL = re.compile(r"\b[I1l][Mm][Ee][I1l]\s*([12])?\s*[:：=-]?", re.I)
NUM = re.compile(r"(?<!\d)\d(?:[ \t-]*\d){14}(?![ \t-]*\d)")


def valid_imei(value):
    if len(value) != 15 or not value.isascii() or not value.isdigit() or len(set(value)) == 1:
        return False
    total = 0
    for i, ch in enumerate(value):
        n = int(ch) * (2 if i % 2 else 1)
        total += n // 10 + n % 10
    return total % 10 == 0


def extract(text):
    """Never invent digits or take a 15-digit substring from an EID/IMEISV."""
    found = []
    pending = None
    for line in text.splitlines():
        if not line.strip():
            continue
        labels = list(LABEL.finditer(line))
        segments = []
        if labels:
            pending = None
            for i, label in enumerate(labels):
                end = labels[i + 1].start() if i + 1 < len(labels) else len(line)
                segments.append((label.group(1), line[label.end():end]))
        else:
            if re.search(r"\b(EID|ICCID|MEID|S/N|SERIAL)\b", line, re.I):
                pending = None
                continue
            segments = [(pending, line)]
        for slot, part in segments:
            numbers = [re.sub(r"\D", "", m.group()) for m in NUM.finditer(part)]
            for number in numbers:
                found.append((slot, number))
            pending = slot if labels and not numbers else None
    return found


def recognize(path):
    votes = {}
    with Image.open(path) as original:
        if original.format not in {"JPEG", "PNG", "WEBP"}:
            raise ValueError("Faqat JPG, PNG yoki WEBP rasm yubor.")
        img = ImageOps.exif_transpose(original).convert("RGB")
        img.thumbnail((2600, 2600))
        if max(img.size) < 1600:
            ratio = min(2, 1600 / max(img.size))
            img = img.resize((int(img.width * ratio), int(img.height * ratio)))
        gray = ImageOps.autocontrast(ImageOps.grayscale(img))
        if sum(gray.resize((1, 1)).getdata()) < 100:
            gray = ImageOps.invert(gray)
        prepared = Path(path).with_name("prepared.png")
        gray.save(prepared)
        for psm in (6, 11):
            result = subprocess.run(
                ["tesseract", str(prepared), "stdout", "-l", "eng", "--psm", str(psm)],
                capture_output=True, text=True, timeout=45, check=True,
                env={**os.environ, "OMP_THREAD_LIMIT": "2"},
            )
            for slot, number in set(extract(result.stdout)):
                record = votes.setdefault(number, {"slots": set(), "count": 0})
                if slot:
                    record["slots"].add(slot)
                record["count"] += 1
    return votes


def make_reply(votes):
    if not votes:
        return ("IMEI topilmadi. Raqamlar ko‘rinadigan joyni yaqinroq, tik va tiniq qilib yubor. "
                "Shtrix-kodning o‘zi yetmaydi: 15 xonali raqamlar ko‘rinishi kerak."), None
    # More than two candidates or conflicting OCR is shown explicitly, never guessed away.
    entries = sorted(votes.items(), key=lambda item: (
        next(iter(item[1]["slots"])) if len(item[1]["slots"]) == 1 else "9", item[0]))
    lines, buttons = [], []
    used = set()
    for index, (number, meta) in enumerate(entries[:8], 1):
        slots = meta["slots"]
        label = "IMEI" + next(iter(slots)) if len(slots) == 1 else f"Raqam {index}"
        if label in used or len(slots) > 1:
            label = f"Raqam {index} (belgisi noaniq)"
        used.add(label)
        mark = "" if valid_imei(number) else " ⚠️ tekshir"
        lines.append(f"{label}: <code>{number}</code>{mark}")
        buttons.append([{"text": f"📋 {label}: {number}", "copy_text": {"text": number}}])
    if any(len(v["slots"]) != 1 for v in votes.values()):
        lines.append("\nIMEI1/IMEI2 tartibi to‘liq aniqlanmadi; rasm bilan solishtir.")
    if len(votes) > 2:
        lines.append("\nIkkitadan ko‘p nomzod topildi. Faqat IMEI qismini kesib qayta yubor.")
    lines.append("\nNusxalash uchun pastdagi raqamli tugmani bos. OCR natijasini rasm bilan tekshir.")
    return "\n".join(lines), {"inline_keyboard": buttons}


class APIError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(f"Telegram API: {code}")


class Bot:
    def __init__(self, token):
        self.token = token

    def call(self, method, **payload):
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{self.token}/{method}",
            data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=70) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            raise APIError(exc.code) from None
        if not result.get("ok"):
            raise APIError(result.get("error_code", 0))
        return result["result"]

    def reply(self, msg, text, keyboard=None):
        data = dict(chat_id=msg["chat"]["id"], text=text, parse_mode="HTML",
                    reply_parameters={"message_id": msg["message_id"], "allow_sending_without_reply": True})
        if keyboard:
            data["reply_markup"] = keyboard
        return self.call("sendMessage", **data)

    def handle(self, msg):
        if msg["chat"]["type"] != "private":
            return
        allowed = os.getenv("ALLOWED_USER_IDS", "").strip()
        if allowed and str(msg.get("from", {}).get("id")) not in allowed.split(","):
            return
        media = msg.get("photo", [None])[-1] or msg.get("document")
        if not media:
            self.reply(msg, "IMEI yozilgan rasm yoki JPG/PNG fayl yubor. Natijadagi raqamli tugmani bossang, "
                       "IMEI nusxalanadi. Har xabarda bitta telefon rasmini yubor.")
            return
        if media.get("file_size", 0) > MAX_BYTES:
            self.reply(msg, "Rasm hajmi 15 MB dan kichik bo‘lsin.")
            return
        status = self.reply(msg, "⏳ Rasm o‘qilyapti…")
        try:
            info = self.call("getFile", file_id=media["file_id"])
            with tempfile.TemporaryDirectory(prefix="imei_") as folder:
                path = Path(folder) / "input"
                url = f"https://api.telegram.org/file/bot{self.token}/{info['file_path']}"
                with urllib.request.urlopen(url, timeout=60) as response:
                    data = response.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    raise ValueError("Rasm hajmi 15 MB dan kichik bo‘lsin.")
                path.write_bytes(data)
                text, keyboard = make_reply(recognize(path))
            self.reply(msg, text, keyboard)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            self.reply(msg, "OCR rasmni o‘qiy olmadi. Yaqinroq va tiniq rasm yubor. "
                       "Serverdagi OCR vaqtincha ishlamadi; qayta urinib ko‘r.")
        except (ValueError, OSError, Image.DecompressionBombError):
            self.reply(msg, "Rasm ochilmadi yoki internetda uzilish bo‘ldi. "
                       "15 MB dan kichik JPG/PNG rasm yubor.")
        finally:
            try:
                self.call("deleteMessage", chat_id=msg["chat"]["id"], message_id=status["message_id"])
            except Exception:
                pass



"""Render Web Service entry point. Token environment variable: bot_2."""
import hashlib
import hmac
import json
import os
import re
import shutil
import threading
import time
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer



def create_server(bot, secret, port):
    completed = OrderedDict()
    processing = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass  # Don't log webhook headers, images, tokens or IMEIs.

        def answer(self, code, body=b"OK"):
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except OSError:
                pass

        def do_GET(self):
            self.answer(200 if self.path in ("/", "/health") else 404)

        def do_POST(self):
            if self.path != "/telegram":
                self.answer(404)
                return
            supplied = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if not hmac.compare_digest(supplied, secret):
                self.answer(403)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 1_000_000:
                    self.answer(413)
                    return
                self.connection.settimeout(20)
                update = json.loads(self.rfile.read(length))
                if not isinstance(update, dict) or type(update.get("update_id")) is not int:
                    raise ValueError()
            except (ValueError, OSError):
                self.answer(400)
                return
            # Keep OCR concurrency at one for Render Free memory limits.
            # Telegram retries 503; never acknowledge an unprocessed queue item.
            if not processing.acquire(blocking=False):
                self.answer(503)
                return
            try:
                uid = update["update_id"]
                if uid not in completed:
                    if "message" in update:
                        bot.handle(update["message"])
                    completed[uid] = None
                    while len(completed) > 2000:
                        completed.popitem(last=False)
                self.answer(200)
            except Exception as exc:
                print("Xabarni qayta ishlash xatosi:", type(exc).__name__, flush=True)
                self.answer(503)
            finally:
                processing.release()

    return ThreadingHTTPServer(("0.0.0.0", port), Handler)


def register_webhook(bot, url, secret):
    while True:
        try:
            bot.call("setWebhook", url=url + "/telegram", secret_token=secret,
                     max_connections=1, allowed_updates=["message"], drop_pending_updates=False)
            print("Webhook tayyor. Botga rasm yuborish mumkin.", flush=True)
            return
        except Exception as exc:
            print("Webhook ulanmadi:", type(exc).__name__, "— 15 soniyada qayta urinish.", flush=True)
            time.sleep(15)


def main():
    token = os.environ.get("bot_2", "").strip()
    if not re.fullmatch(r"\d+:[A-Za-z0-9_-]+", token):
        raise SystemExit("Render Environment bo‘limida bot_2 nomiga BotFather tokenini yoz.")
    url = (os.environ.get("WEBHOOK_URL") or os.environ.get("RENDER_EXTERNAL_URL", "")).rstrip("/")
    if not url.startswith("https://"):
        raise SystemExit("WEBHOOK_URL=https://xizmating.onrender.com kerak; Render odatda URLni o‘zi beradi.")
    if not shutil.which("tesseract"):
        raise SystemExit("Tesseract topilmadi. Render Language: Docker bo‘lishi kerak.")
    secret = hmac.new(token.encode(), b"imei-bot-render-webhook-v1", hashlib.sha256).hexdigest()
    bot = Bot(token)
    server = create_server(bot, secret, int(os.environ.get("PORT", "10000")))
    threading.Thread(target=register_webhook, args=(bot, url, secret), daemon=True).start()
    print("IMEI bot_2 web server ishga tushdi.", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
