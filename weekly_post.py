import requests
from PIL import Image, ImageDraw, ImageFont
import io
from datetime import datetime, timedelta

DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1384784710798147604/MhC_WVICE202ZixKFfPBwCvgqc_qf2W6gLYlDUBG5U0R_q3FejUC2zyTZJyGElOje3do"
# 「その週の水曜日」を安全に取得する（毎週金曜実行を想定）
def get_latest_available_wednesday():
    jst_now = datetime.utcnow() + timedelta(hours=9)
    weekday = jst_now.weekday()  # 月=0, 火=1, 水=2, ..., 金=4

    if weekday < 4:
        # 月〜木：1週前の水曜に戻る
        jst_now -= timedelta(weeks=1)

    # 現在時点での週の水曜を計算
    days_to_wednesday = 2 - jst_now.weekday()
    wednesday = jst_now + timedelta(days=days_to_wednesday)
    return wednesday.strftime('%Y%m%d')

# 画像取得
def get_image(url):
    res = requests.get(url)
    return Image.open(io.BytesIO(res.content)).convert("RGB") if res.status_code == 200 else None

# マージンとラベル追加
def add_margin_and_label(image, label, margin=30, color=(255, 255, 255)):
    new_width = image.width + margin * 2
    new_height = image.height + margin * 2
    new_img = Image.new("RGB", (new_width, new_height), color)
    new_img.paste(image, (margin, margin))

    draw = ImageDraw.Draw(new_img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except:
        font = ImageFont.load_default()

    draw.text((margin + 50, margin + 30), label, fill="black", font=font, stroke_width=2, stroke_fill="white")
    return new_img

# 縦に結合（横幅を統一）
def concat_images_two_uniform(img1, img2):
    max_width = max(img1.width, img2.width)

    def resize(img):
        if img.width == max_width:
            return img
        new_height = int(img.height * (max_width / img.width))
        return img.resize((max_width, new_height), Image.BICUBIC)

    img1 = resize(img1)
    img2 = resize(img2)

    combined = Image.new("RGB", (max_width, img1.height + img2.height))
    combined.paste(img1, (0, 0))
    combined.paste(img2, (0, img1.height))

    output = io.BytesIO()
    combined.save(output, format="PNG")
    output.seek(0)
    return output

# 投稿処理
def post_to_discord():
    date_str = get_latest_available_wednesday()

    urls = [
        f"https://ds.data.jma.go.jp/tcc/tcc/products/climate/db/monitor/weekly/fg{date_str}e.png",
        f"https://ds.data.jma.go.jp/tcc/tcc/products/climate/db/monitor/weekly/fgtemp{date_str}e.png"
    ]
    labels = ["Extreme Climate Events", "Weekly Temperature Anomaly"]

    imgs = []
    for url, label in zip(urls, labels):
        print(f"🔗 取得中: {url}")
        img = get_image(url)
        if img:
            img = add_margin_and_label(img, label)
        imgs.append(img)

    if None in imgs:
        print("❌ 画像取得に失敗")
        return

    combined = concat_images_two_uniform(imgs[0], imgs[1])

    files = {
        "file": ("jma_weekly.png", combined, "image/png")
    }

    content = f"🗓 気象庁 週次気候図（{date_str}基準）\nExtreme Climate Events + Temperature Anomaly をまとめて投稿します。"

    res = requests.post(DISCORD_WEBHOOK_URL, data={"content": content}, files=files)
    if res.status_code == 204:
        print("✅ 投稿成功")
    else:
        print(f"⚠ 投稿失敗: {res.status_code}, {res.text}")

if __name__ == "__main__":
    post_to_discord()
