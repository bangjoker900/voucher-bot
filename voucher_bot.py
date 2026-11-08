import os
import cv2
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)

BOT_TOKEN = "9299036072:AAGC9qBThr5XdU2NaknOVVmTPS1exlPbcy0"

DATA_FOLDER = "voucher_data"
os.makedirs(DATA_FOLDER, exist_ok=True)

try:
    from pyzbar.pyzbar import decode
    PYZBAR_AVAILABLE = True
except Exception:
    PYZBAR_AVAILABLE = False

def scan_barcode(image_path):
    if not PYZBAR_AVAILABLE:
        return []
    try:
        img = cv2.imread(image_path)
        barcodes = decode(img)
        return [bc.data.decode("utf-8") for bc in barcodes]
    except Exception:
        return []

def save_voucher(barcode_data, file_path):
    record_file = os.path.join(DATA_FOLDER, "daftar_voucher.txt")
    with open(record_file, "a", encoding="utf-8") as f:
        f.write(f"{barcode_data}|{file_path}\n")

def search_voucher(keyword):
    record_file = os.path.join(DATA_FOLDER, "daftar_voucher.txt")
    if not os.path.exists(record_file):
        return []
    found = []
    with open(record_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            code, path = line.split("|", 1)
            if keyword.lower() in code.lower():
                found.append({"code": code, "path": path})
    return found

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hai! Kirimkan foto voucher kamu, nanti saya simpan datanya.\n"
        "Gunakan /cari [kode] untuk mencari voucher."
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_file = await update.message.photo[-1].get_file()
    filename = f"{user.id}_{photo_file.file_unique_id}.jpg"
    save_path = os.path.join(DATA_FOLDER, filename)
    await photo_file.download_to_drive(save_path)

    barcodes = scan_barcode(save_path)
    if barcodes:
        for code in barcodes:
            save_voucher(code, save_path)
            await update.message.reply_text(f"✅ Tersimpan!\nKode: {code}")
    else:
        await update.message.reply_text(
            "⚠️ Kode tidak terbaca.\nKetik nomor seri/kode voucher:"
        )
        context.user_data["pending_photo"] = save_path

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    pending_photo = context.user_data.get("pending_photo")

    if pending_photo:
        save_voucher(text, pending_photo)
        await update.message.reply_text(f"✅ Tersimpan: {text}")
        context.user_data["pending_photo"] = None
        return

    results = search_voucher(text)
    if results:
        await update.message.reply_text(f"🔍 Ditemukan {len(results)} hasil:")
        for res in results:
            await update.message.reply_photo(
                photo=open(res["path"], "rb"),
                caption=f"Kode: {res['code']}"
            )
    else:
        await update.message.reply_text("❌ Tidak ditemukan.")

async def cari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /cari 12345")
        return
    keyword = " ".join(context.args)
    results = search_voucher(keyword)
    if results:
        await update.message.reply_text(f"🔍 Ditemukan {len(results)} hasil:")
        for res in results:
            await update.message.reply_photo(
                photo=open(res["path"], "rb"),
                caption=f"Kode: {res['code']}"
            )
    else:
        await update.message.reply_text("❌ Tidak ditemukan.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cari", cari))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
