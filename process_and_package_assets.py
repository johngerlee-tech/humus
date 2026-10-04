# -*- coding: utf-8 -*-
"""
處理 AI 生成之鳥山明風格角色圖檔為透明背景 PNG，
並生成對應頭像與全套 20 張遊戲圖片，最後打包為 ZIP 壓縮檔。
"""

import os
import cv2
import zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = r"c:\Users\user\Desktop\黑金魔法術RPG"
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")
BRAIN_DIR = r"C:\Users\user\.gemini\antigravity\brain\114fca1f-33b0-42ff-a397-21d34060bfea"

os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(os.path.join(IMAGES_DIR, "custom"), exist_ok=True)

# 1. 定義生成的原圖路徑
SOURCE_FILES = {
    "momo": os.path.join(BRAIN_DIR, "hero_sprite_1791119845329.jpg"),
    "koko": os.path.join(BRAIN_DIR, "hero_sprite_round_1791119908070.jpg"),
    "lulu": os.path.join(BRAIN_DIR, "hero_sprite_syl_1791119925691.jpg"),
    "dudu": os.path.join(BRAIN_DIR, "hero_sprite_mul_1791120038999.jpg"),
    "slime": os.path.join(BRAIN_DIR, "slime_sprite_1791120063283.jpg"),
    "mirage": os.path.join(BRAIN_DIR, "mirage_sprite_1791120086109.jpg"),
    "demon": os.path.join(BRAIN_DIR, "demon_sprite_1791120202718.jpg"),
    "frost": os.path.join(BRAIN_DIR, "earth_titan_1791120279753.jpg"),
    "boss": os.path.join(BRAIN_DIR, "boss_titan_1791120304316.jpg"),
    "hall_bg": os.path.join(BRAIN_DIR, "forest_bg_1791120326793.jpg")
}

def remove_background_and_make_png(src_path, target_size=(800, 1000)):
    """透過色彩與泛洪填充智慧去除棋盤格或純色外框背景"""
    img = Image.open(src_path).convert("RGBA")
    arr = np.array(img, dtype=np.uint8)
    h, w = arr.shape[:2]

    # 計算 RGB 差異 (判斷是否為無彩度之灰色棋盤格或白色)
    r, g, b = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)
    diff_rg = np.abs(r - g)
    diff_gb = np.abs(g - b)
    diff_rb = np.abs(r - b)
    is_neutral = (diff_rg < 12) & (diff_gb < 12) & (diff_rb < 12)

    # 檢查是否為明亮或中度灰色 (棋盤格通常在 180~255 間)
    is_bg_color = is_neutral & (r > 160)

    # 使用 OpenCV 泛洪填充從圖片四邊邊緣向內擴散
    gray_bin = np.where(is_bg_color, 255, 0).astype(np.uint8)
    
    seeds = []
    # 邊界四條邊採樣
    for x in range(0, w, 15):
        seeds.append((x, 0))
        seeds.append((x, h - 1))
    for y in range(0, h, 15):
        seeds.append((0, y))
        seeds.append((w - 1, y))

    flood_mask = np.zeros((h + 2, w + 2), np.uint8)
    for sx, sy in seeds:
        if gray_bin[sy, sx] == 255:
            cv2.floodFill(gray_bin, mask=flood_mask, seedPoint=(sx, sy), newVal=128)

    bg_mask = (gray_bin == 128)
    arr[bg_mask, 3] = 0

    # 轉回 PIL 並調整尺寸
    res_img = Image.fromarray(arr)
    # 稍微裁切邊界透明空白
    bbox = res_img.getbbox()
    if bbox:
        cropped = res_img.crop(bbox)
        # 依等比例縮放至目標尺寸
        cw, ch = cropped.size
        scale = min(target_size[0] / cw, target_size[1] / ch) * 0.95
        new_w, new_h = int(cw * scale), int(ch * scale)
        resized = cropped.resize((new_w, new_h), Image.LANCZOS)
        
        final_img = Image.new("RGBA", target_size, (0, 0, 0, 0))
        pos_x = (target_size[0] - new_w) // 2
        pos_y = target_size[1] - new_h - 20 # 靠近底部
        final_img.paste(resized, (pos_x, pos_y), resized)
        return final_img

    return res_img.resize(target_size, Image.LANCZOS)

def crop_avatar(hero_src_path, head_box_ratio=(0.25, 0.05, 0.75, 0.45), target_size=(400, 400)):
    """從角色原圖智慧裁切特寫頭部並套用金色圓形/精美邊框"""
    img = Image.open(hero_src_path).convert("RGBA")
    w, h = img.size
    x0 = int(w * head_box_ratio[0])
    y0 = int(h * head_box_ratio[1])
    x1 = int(w * head_box_ratio[2])
    y1 = int(h * head_box_ratio[3])

    head_crop = img.crop((x0, y0, x1, y1))
    # 將頭像裁切並置中在正方形
    hw, hh = head_crop.size
    square_size = max(hw, hh)
    sq_img = Image.new("RGBA", (square_size, square_size), (0, 0, 0, 0))
    sq_img.paste(head_crop, ((square_size - hw) // 2, (square_size - hh) // 2))

    # 去背處理
    arr = np.array(sq_img, dtype=np.uint8)
    r, g, b = arr[:, :, 0].astype(int), arr[:, :, 1].astype(int), arr[:, :, 2].astype(int)
    is_neutral = (np.abs(r - g) < 14) & (np.abs(g - b) < 14) & (np.abs(r - b) < 14)
    is_bg = is_neutral & (r > 160)
    gray_bin = np.where(is_bg, 255, 0).astype(np.uint8)

    seeds = [(0, 0), (square_size - 1, 0), (0, square_size - 1), (square_size - 1, square_size - 1)]
    for sx, sy in seeds:
        if gray_bin[sy, sx] == 255:
            cv2.floodFill(gray_bin, None, (sx, sy), 128)
    arr[gray_bin == 128, 3] = 0

    head_transparent = Image.fromarray(arr).resize((360, 360), Image.LANCZOS)

    # 製作圓形頭像框
    avatar_canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
    d = ImageDraw.Draw(avatar_canvas)
    
    # 圓形底色光暈
    d.ellipse([10, 10, 390, 390], fill=(15, 23, 42, 240), outline=(250, 204, 21, 255), width=8)
    d.ellipse([22, 22, 378, 378], outline=(16, 185, 129, 200), width=4)

    # 貼入頭像角色
    avatar_canvas.paste(head_transparent, (20, 20), head_transparent)
    return avatar_canvas

def generate_custom_background(filename, title, subtitle, main_art_style="eco"):
    """生成 1920x1080 頂級動漫寬螢幕戰鬥場景"""
    img = Image.new("RGB", (1920, 1080))
    d = ImageDraw.Draw(img)

    if main_art_style == "hall": # 宴會廳已由 AI 生成，直接調整
        pass
    elif main_art_style == "sorting": # 中央分類迴廊
        # 繪製現代綠能玻璃穹頂迴廊
        # 漸層天空與天窗
        for y in range(0, 500):
            r = int(10 + (y / 500) * 20)
            g = int(60 + (y / 500) * 70)
            b = int(70 + (y / 500) * 80)
            d.line([(0, y), (1920, y)], fill=(r, g, b))
        for y in range(500, 1080):
            r = int(25 + ((y - 500) / 580) * 20)
            g = int(45 + ((y - 500) / 580) * 30)
            b = int(35 + ((y - 500) / 580) * 20)
            d.line([(0, y), (1920, y)], fill=(r, g, b))

        # 玻璃天窗鋼構樑柱
        for x in range(0, 1920, 240):
            d.line([(x, 0), (x + 120, 500)], fill=(52, 211, 153), width=4)
            d.line([(x + 120, 500), (x, 1080)], fill=(5, 150, 105), width=3)
        # 迴廊彩色分類大桶子
        bins = [(300, "#10b981", "生廚餘堆肥"), (700, "#f59e0b", "熟廚餘養豬"), (1100, "#38bdf8", "乾淨資源回收"), (1500, "#ef4444", "一般垃圾")]
        for bx, col, text in bins:
            d.rounded_rectangle([bx, 600, bx + 220, 950], radius=25, fill=col, outline=(255, 255, 255), width=4)
            d.ellipse([bx + 40, 640, bx + 180, 780], fill=(255, 255, 255, 180))

    elif main_art_style == "greenhouse": # 黑金發酵溫室
        # 暖橘紅木質發酵棚架
        for y in range(0, 1080):
            ratio = y / 1080
            r = int(35 * (1 - ratio) + 20 * ratio)
            g = int(25 * (1 - ratio) + 45 * ratio)
            b = int(15 * (1 - ratio) + 25 * ratio)
            d.line([(0, y), (1920, y)], fill=(r, g, b))

        # 溫室天窗金光穿透
        for i in range(12):
            x1 = 200 + i * 140
            d.polygon([(x1, 0), (x1 + 100, 0), (x1 + 250, 1080), (x1 + 150, 1080)], fill=(254, 240, 138))
        # 堆肥發酵木箱
        for x in range(150, 1800, 420):
            d.rectangle([x, 620, x + 340, 980], fill=(69, 26, 3), outline=(180, 83, 9), width=4)
            d.rectangle([x + 20, 640, x + 320, 750], fill=(30, 20, 10)) # 黑金土

    elif main_art_style == "garden": # 陽光有機菜園
        # 湛藍天空與金黃陽光
        for y in range(0, 600):
            ratio = y / 600
            d.line([(0, y), (1920, y)], fill=(int(30 + 100 * ratio), int(64 + 130 * ratio), int(175 + 60 * ratio)))
        # 遠方綠油油山丘
        d.pieslice([-100, 400, 1000, 1000], start=180, end=360, fill=(22, 101, 52))
        d.pieslice([600, 380, 2000, 1000], start=180, end=360, fill=(34, 197, 94))
        # 田畦黑金肥沃菜土
        for y in range(650, 1080, 85):
            d.rectangle([0, y, 1920, y + 50], fill=(25, 18, 12))
            # 嫩綠菜苗
            for vx in range(80, 1900, 110):
                d.ellipse([vx, y - 10, vx + 40, y + 20], fill=(74, 222, 128))

    elif main_art_style == "temple": # 永續生命神殿
        # 神秘星空深藍紫
        for y in range(0, 1080):
            ratio = y / 1080
            d.line([(0, y), (1920, y)], fill=(int(15 * (1 - ratio) + 6 * ratio), int(23 * (1 - ratio) + 78 * ratio), int(42 * (1 - ratio) + 59 * ratio)))
        # 巨大世界生命之樹
        d.rectangle([800, 350, 1120, 1080], fill=(69, 26, 3))
        d.ellipse([300, 50, 1620, 600], fill=(5, 150, 105), outline=(52, 211, 153), width=6)
        # 金色循環光環
        d.ellipse([500, 120, 1420, 920], outline=(250, 204, 21), width=8)

    elif main_art_style == "title": # 冒險啟程主畫面背景
        # 晨光初照魔法學院與黑金梯田
        for y in range(0, 600):
            ratio = y / 600
            d.line([(0, y), (1920, y)], fill=(int(20 + 220 * ratio), int(30 + 180 * ratio), int(80 + 50 * ratio)))
        d.ellipse([800, 200, 1120, 520], fill=(254, 240, 138)) # 朝陽
        d.pieslice([-150, 520, 1150, 1300], start=180, end=360, fill=(6, 78, 59))
        d.pieslice([750, 480, 2100, 1300], start=180, end=360, fill=(16, 185, 129))

    elif main_art_style == "map": # 羊皮紙大地圖
        # 古典羊皮紙質感
        for y in range(0, 1080):
            ratio = y / 1080
            d.line([(0, y), (1920, y)], fill=(int(69 * (1 - ratio) + 40 * ratio), int(35 * (1 - ratio) + 60 * ratio), int(15 * (1 - ratio) + 25 * ratio)))
        # 經緯網格
        for x in range(120, 1920, 180):
            d.line([(x, 0), (x, 1080)], fill=(120, 53, 15), width=1)
        for y in range(100, 1080, 180):
            d.line([(0, y), (1920, y)], fill=(120, 53, 15), width=1)
        # 綠色生態島嶼
        d.polygon([(350, 850), (550, 520), (960, 380), (1450, 420), (1650, 720), (1350, 940), (650, 960)], fill=(20, 83, 45), outline=(245, 158, 11), width=6)
        # 金色循環路徑
        d.ellipse([500, 420, 1500, 900], outline=(250, 204, 21), width=4)

    # 頂部半透明微標題條
    d.rectangle([0, 0, 1920, 95], fill=(15, 23, 42))
    d.line([(0, 95), (1920, 95)], fill=(250, 204, 21), width=3)
    
    try:
        font_t = ImageFont.truetype(r"C:\Windows\Fonts\msjhbd.ttc", 36)
        font_sub = ImageFont.truetype(r"C:\Windows\Fonts\msjh.ttc", 22)
        d.text((60, 48), title, fill=(255, 255, 255), anchor="lm", font=font_t)
        d.text((1860, 48), subtitle, fill=(253, 224, 71), anchor="rm", font=font_sub)
    except Exception:
        pass

    return img

def main():
    print("=" * 60)
    print("🎨 開始處理全套 20 張《黑金魔法術》鳥山明風格美術圖檔...")
    print("=" * 60)

    # 1. 處理四大勇者立繪與頭像
    heroes_map = [
        # (src_key, sprite_filename, avatar_filename, head_box, name)
        ("momo", "hero_sprite.png", "avatar_purple.png", (0.28, 0.15, 0.72, 0.48), "莫莫 Momo"),
        ("koko", "hero_sprite_round.png", "avatar_round.png", (0.28, 0.10, 0.72, 0.46), "寇寇 Koko"),
        ("lulu", "hero_sprite_syl.png", "avatar_syl.png", (0.24, 0.08, 0.76, 0.48), "露露 Lulu"),
        ("dudu", "hero_sprite_mul.png", "avatar_mul.png", (0.30, 0.18, 0.74, 0.50), "嘟嘟 Dudu"),
    ]

    for src_key, s_fn, a_fn, h_box, name in heroes_map:
        src = SOURCE_FILES[src_key]
        print(f"👉 處理勇者【{name}】...")
        # 立繪
        sp_img = remove_background_and_make_png(src, (800, 1000))
        sp_img.save(os.path.join(IMAGES_DIR, s_fn), "PNG")
        # 頭像
        av_img = crop_avatar(src, h_box, (400, 400))
        av_img.save(os.path.join(IMAGES_DIR, a_fn), "PNG")
        print(f"  ✓ 已生成: {s_fn} 與 {a_fn}")

    # 2. 處理五大關主魔王立繪
    bosses_map = [
        ("slime", "slime_sprite.png", "浪費剩食怪"),
        ("mirage", "mirage_sprite.png", "混雜垃圾魔"),
        ("demon", "demon_sprite.png", "惡臭果蠅王"),
        ("frost", "frost_sprite.png", "板結枯土巨魔"),
        ("boss", "boss_sprite.png", "失衡異變巨神"),
    ]

    for src_key, b_fn, name in bosses_map:
        src = SOURCE_FILES[src_key]
        print(f"👾 處理魔王【{name}】...")
        b_img = remove_background_and_make_png(src, (800, 900))
        b_img.save(os.path.join(IMAGES_DIR, b_fn), "PNG")
        print(f"  ✓ 已生成: {b_fn}")

    # 3. 處理背景圖檔
    print("🌄 處理背景場景...")
    # 第一關宴會廳使用 AI 生成的宏偉魔法宴會廳
    hall_src = SOURCE_FILES["hall_bg"]
    Image.open(hall_src).resize((1920, 1080), Image.LANCZOS).save(os.path.join(IMAGES_DIR, "forest_bg.jpg"), "JPEG", quality=92)
    print("  ✓ 已生成: forest_bg.jpg (第一章：學院惜食大廳)")

    bg_configs = [
        ("desert_bg.jpg", "第二章：中央分類迴廊", "生廚餘、熟廚餘與回收分類站", "sorting"),
        ("river_bg.jpg", "第三章：黑金發酵溫室", "木箱發酵堆肥與通氣工藝", "greenhouse"),
        ("highway_bg.jpg", "第四章：陽光有機菜園", "黑金沃土滋養校園蔬果", "garden"),
        ("sacred_bg.jpg", "第五章：永續生命神殿", "永續食物循環世界之樹", "temple"),
        ("title_bg.jpg", "黑金魔法術：永續食物循環系統", "溪洲魔法生態學院 · 綠色冒險啟程", "title"),
        ("world_map.jpg", "溪洲魔法生態學院 · 永續食物循環大地圖", "五大生態關卡探索", "map"),
    ]

    for bg_fn, t, sub, style in bg_configs:
        bg = generate_custom_background(bg_fn, t, sub, style)
        bg.save(os.path.join(IMAGES_DIR, bg_fn), "JPEG", quality=92)
        print(f"  ✓ 已生成: {bg_fn} ({t})")

    # 4. 同步複製至 custom/
    for fn in os.listdir(IMAGES_DIR):
        fpath = os.path.join(IMAGES_DIR, fn)
        if os.path.isfile(fpath):
            with open(fpath, "rb") as rf:
                with open(os.path.join(IMAGES_DIR, "custom", fn), "wb") as wf:
                    wf.write(rf.read())

    # 5. 打包為標準 ZIP 壓縮檔
    zip_path = os.path.join(BASE_DIR, "黑金魔法術_全套20張遊戲圖檔.zip")
    print(f"\n📦 正在打包全套 20 張圖片至 ZIP 壓縮檔：{os.path.basename(zip_path)}...")
    
    file_list = [
        "hero_sprite.png", "avatar_purple.png",
        "hero_sprite_round.png", "avatar_round.png",
        "hero_sprite_syl.png", "avatar_syl.png",
        "hero_sprite_mul.png", "avatar_mul.png",
        "slime_sprite.png", "mirage_sprite.png",
        "demon_sprite.png", "frost_sprite.png", "boss_sprite.png",
        "forest_bg.jpg", "desert_bg.jpg", "river_bg.jpg",
        "highway_bg.jpg", "sacred_bg.jpg",
        "title_bg.jpg", "world_map.jpg"
    ]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fn in file_list:
            fp = os.path.join(IMAGES_DIR, fn)
            zf.write(fp, arcname=fn)
            print(f"  + 已加入壓縮檔: {fn}")

    print("\n🎉 全套 20 張對應遊戲角色的高品質美術圖檔與 ZIP 壓縮包已全部準備就緒！")

if __name__ == "__main__":
    main()
