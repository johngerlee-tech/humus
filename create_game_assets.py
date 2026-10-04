# -*- coding: utf-8 -*-
"""
生成《黑金魔法術─永續食物循環系統》全域 20 張高畫質遊戲美術圖檔與應用程式圖示
"""

import os
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_BOLD = r"C:\Windows\Fonts\msjhbd.ttc"
FONT_REG = r"C:\Windows\Fonts\msjh.ttc"

def get_font(size, bold=True):
    path = FONT_BOLD if bold else FONT_REG
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def draw_gradient_rect(draw, bbox, color_top, color_bottom):
    x0, y0, x1, y1 = bbox
    height = max(1, y1 - y0)
    for y in range(y0, y1):
        ratio = (y - y0) / height
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        draw.line([(x0, y), (x1, y)], fill=(r, g, b))

def draw_radial_circle(draw, center, radius, color_center, color_edge):
    cx, cy = center
    steps = 40
    for i in range(steps, 0, -1):
        r = int(radius * (i / steps))
        ratio = i / steps
        alpha = int(color_edge[3] * ratio + color_center[3] * (1 - ratio)) if len(color_center) > 3 else 255
        cr = int(color_edge[0] * ratio + color_center[0] * (1 - ratio))
        cg = int(color_edge[1] * ratio + color_center[1] * (1 - ratio))
        cb = int(color_edge[2] * ratio + color_center[2] * (1 - ratio))
        fill = (cr, cg, cb, alpha) if len(color_center) > 3 else (cr, cg, cb)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)

# ==========================================
# 1. 英雄頭像與立繪生成函數
# ==========================================
def create_hero_graphics(hero_key, name, title, role, primary_color, secondary_color, icon_sym, quote):
    # 头像 (400x400)
    avatar = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    d_av = ImageDraw.Draw(avatar)
    
    # 外圈金色光環
    draw_radial_circle(d_av, (200, 200), 190, (*primary_color, 120), (*secondary_color, 20))
    d_av.ellipse([20, 20, 380, 380], fill=(15, 23, 42, 230), outline=(250, 204, 21, 240), width=6)
    d_av.ellipse([32, 32, 368, 368], outline=(*primary_color, 200), width=3)
    
    # 角色圖騰與文字
    f_sym = get_font(90, bold=True)
    d_av.text((200, 150), icon_sym, fill=(255, 255, 255, 255), anchor="mm", font=f_sym)
    
    # 角色名稱與稱號
    f_name = get_font(34, bold=True)
    f_title = get_font(18, bold=False)
    d_av.rectangle([40, 280, 360, 345], fill=(*secondary_color, 220), outline=(250, 204, 21, 230), width=2)
    d_av.text((200, 302), name, fill=(255, 255, 255), anchor="mm", font=f_name)
    d_av.text((200, 330), title, fill=(254, 240, 138), anchor="mm", font=f_title)
    
    # 立繪 (800x1000)
    sprite = Image.new("RGBA", (800, 1000), (0, 0, 0, 0))
    d_sp = ImageDraw.Draw(sprite)
    
    # 底部地面陰影
    d_sp.ellipse([200, 880, 600, 960], fill=(0, 0, 0, 110))
    # 魔法光環
    draw_radial_circle(d_sp, (400, 520), 380, (*primary_color, 90), (*secondary_color, 0))
    
    # 身體主體卡片展示框 (立繪藝術風格)
    d_sp.rounded_rectangle([120, 100, 680, 880], radius=40, fill=(15, 23, 42, 210), outline=(250, 204, 21, 240), width=6)
    d_sp.rounded_rectangle([135, 115, 665, 865], radius=32, outline=(*primary_color, 180), width=3)
    
    # 頂部主題徽章
    d_sp.rounded_rectangle([250, 60, 550, 130], radius=25, fill=(*secondary_color, 240), outline=(250, 204, 21, 255), width=3)
    f_badge = get_font(26, bold=True)
    d_sp.text((400, 95), f"✨ {role} ✨", fill=(255, 255, 255), anchor="mm", font=f_badge)
    
    # 中心巨大象徵圖騰
    f_giant_sym = get_font(220, bold=True)
    d_sp.text((400, 380), icon_sym, fill=(255, 255, 255), anchor="mm", font=f_giant_sym)
    
    # 屬性星級與稱號
    f_sp_name = get_font(52, bold=True)
    f_sp_title = get_font(28, bold=True)
    f_sp_quote = get_font(22, bold=False)
    d_sp.text((400, 560), name, fill=(255, 255, 255), anchor="mm", font=f_sp_name)
    d_sp.text((400, 620), f"【{title}】", fill=(253, 224, 71), anchor="mm", font=f_sp_title)
    
    # 技能與座右銘對話框
    d_sp.rounded_rectangle([160, 680, 640, 780], radius=20, fill=(*primary_color, 90), outline=(255, 255, 255, 120), width=2)
    d_sp.text((400, 730), f"「{quote}」", fill=(241, 245, 249), anchor="mm", font=f_sp_quote)
    
    # 底部五星評級
    f_stars = get_font(30, bold=True)
    d_sp.text((400, 820), "★★★★★ 守護勇者 ★★★★★", fill=(250, 204, 21), anchor="mm", font=f_stars)
    
    return avatar, sprite

# ==========================================
# 2. 魔王立繪生成函數
# ==========================================
def create_boss_graphics(boss_key, chapter, name, subtitle, color_primary, color_dark, icon_sym, desc):
    sprite = Image.new("RGBA", (900, 1000), (0, 0, 0, 0))
    d = ImageDraw.Draw(sprite)
    
    # 底部威壓陰影
    d.ellipse([180, 880, 720, 970], fill=(0, 0, 0, 140))
    # 暗黑魔王光環
    draw_radial_circle(d, (450, 500), 420, (*color_primary, 110), (*color_dark, 0))
    
    # 魔王戰鬥卡牌主體框
    d.rounded_rectangle([100, 100, 800, 880], radius=45, fill=(10, 15, 29, 230), outline=(*color_primary, 240), width=6)
    d.rounded_rectangle([115, 115, 785, 865], radius=35, outline=(248, 113, 113, 160), width=3)
    
    # 章節警示條
    d.rounded_rectangle([260, 65, 640, 135], radius=22, fill=(*color_dark, 250), outline=(*color_primary, 255), width=3)
    f_ch = get_font(24, bold=True)
    d.text((450, 100), f"⚠️ {chapter} 守護考驗", fill=(254, 240, 138), anchor="mm", font=f_ch)
    
    # 中心巨大魔王象徵符號
    f_giant = get_font(230, bold=True)
    d.text((450, 380), icon_sym, fill=(255, 255, 255), anchor="mm", font=f_giant)
    
    # 魔王名稱
    f_name = get_font(56, bold=True)
    f_sub = get_font(28, bold=True)
    f_desc = get_font(20, bold=False)
    d.text((450, 560), name, fill=(248, 113, 113), anchor="mm", font=f_name)
    d.text((450, 620), f"~ {subtitle} ~", fill=(253, 224, 71), anchor="mm", font=f_sub)
    
    # 魔王考驗說明框
    d.rounded_rectangle([140, 680, 760, 790], radius=18, fill=(30, 20, 45, 200), outline=(*color_primary, 160), width=2)
    # 自動換行
    lines = [desc[:22], desc[22:]] if len(desc) > 22 else [desc]
    y_off = 720 if len(lines) == 1 else 710
    for l in lines:
        if l:
            d.text((450, y_off), l, fill=(226, 232, 240), anchor="mm", font=f_desc)
            y_off += 30
            
    # 底部魔王危險指數
    f_warn = get_font(24, bold=True)
    d.text((450, 830), "⚔️ BOSS BATTLE · 答對擊潰魔王 ⚔️", fill=(239, 68, 68), anchor="mm", font=f_warn)
    
    return sprite

# ==========================================
# 3. 戰鬥與全域背景生成函數 (1920x1080)
# ==========================================
def create_scenic_background(title, subtitle, top_color, bottom_color, deco_type):
    img = Image.new("RGB", (1920, 1080))
    d = ImageDraw.Draw(img)
    
    # 漸層天空與地面
    draw_gradient_rect(d, (0, 0, 1920, 1080), top_color, bottom_color)
    
    # 根據場景添加自然氛圍元素
    if deco_type == "hall": # 學院惜食宴會廳
        # 繪製學院拱門與溫暖光柱
        for x in range(200, 1800, 300):
            d.rectangle([x, 200, x + 60, 1080], fill=(45, 30, 20, 180))
            d.arc([x - 60, 140, x + 120, 320], start=180, end=360, fill=(217, 119, 6), width=6)
        # 暖黃吊燈光暈
        for lx in [400, 960, 1520]:
            draw_radial_circle(d, (lx, 180), 220, (253, 224, 71), (0, 0, 0))
    elif deco_type == "sorting": # 分類迴廊
        # 科技與自然交織的幾何線條
        for y in range(300, 1080, 80):
            d.line([(0, y), (1920, y + 40)], fill=(16, 185, 129), width=2)
        for x in range(100, 1920, 220):
            d.rectangle([x, 700, x + 160, 980], fill=(6, 78, 59))
            d.text((x + 80, 840), "♻️", fill=(255, 255, 255), anchor="mm", font=get_font(60))
    elif deco_type == "greenhouse": # 發酵溫室
        # 溫室玻璃棚架透光
        for x in range(0, 1920, 160):
            d.line([(x, 0), (x + 200, 700)], fill=(254, 240, 138), width=3)
        # 發酵蒸氣光環
        for gx in [350, 960, 1570]:
            draw_radial_circle(d, (gx, 650), 320, (245, 158, 11), (20, 83, 45))
    elif deco_type == "garden": # 陽光有機菜園
        # 遠處翠綠山丘
        d.pieslice([-200, 450, 1200, 1100], start=180, end=360, fill=(22, 101, 52))
        d.pieslice([700, 420, 2100, 1100], start=180, end=360, fill=(34, 197, 94))
        # 菜畦黑土田埂
        for y in range(720, 1080, 90):
            d.rectangle([0, y, 1920, y + 45], fill=(30, 20, 10))
    elif deco_type == "temple": # 永續生命神殿
        # 神聖生命之樹巨木光環
        draw_radial_circle(d, (960, 480), 550, (253, 224, 71), (15, 23, 42))
        # 巨大樹幹與藤蔓
        d.rectangle([820, 400, 1100, 1080], fill=(69, 26, 3))
        d.ellipse([450, 100, 1470, 550], fill=(5, 150, 105))
    elif deco_type == "title": # 主畫面背景
        # 城堡山丘與朝陽
        draw_radial_circle(d, (960, 400), 500, (254, 240, 138), (30, 58, 138))
        d.pieslice([-100, 550, 1100, 1250], start=180, end=360, fill=(6, 78, 59))
        d.pieslice([800, 500, 2050, 1250], start=180, end=360, fill=(16, 185, 129))
    elif deco_type == "map": # 羊皮紙大地圖
        # 地圖網格與航線
        for x in range(100, 1920, 200):
            d.line([(x, 0), (x, 1080)], fill=(120, 53, 15), width=1)
        for y in range(100, 1080, 200):
            d.line([(0, y), (1920, y)], fill=(120, 53, 15), width=1)
        # 綠色生態島嶼輪廓
        d.polygon([(400, 850), (600, 550), (960, 400), (1400, 450), (1600, 750), (1300, 920), (700, 960)], fill=(20, 83, 45), outline=(245, 158, 11), width=4)

    # 頂部半透明微標題條 (增添電玩場景感)
    d.rectangle([0, 0, 1920, 110], fill=(15, 23, 42))
    d.line([(0, 110), (1920, 110)], fill=(250, 204, 21), width=3)
    
    f_t = get_font(42, bold=True)
    f_sub = get_font(24, bold=False)
    d.text((60, 55), title, fill=(255, 255, 255), anchor="lm", font=f_t)
    d.text((1860, 55), subtitle, fill=(253, 224, 71), anchor="rm", font=f_sub)
    
    # 底部裝飾條
    d.rectangle([0, 1040, 1920, 1080], fill=(10, 15, 29))
    d.text((960, 1060), "🌿 黑金魔法術 · 溪洲魔法生態學院 永續食物循環系統 🌿", fill=(148, 163, 184), anchor="mm", font=get_font(18, bold=True))
    
    return img

# ==========================================
# 4. 主生成執行程序
# ==========================================
def main():
    img_dir = os.path.join("assets", "images")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(os.path.join(img_dir, "custom"), exist_ok=True)
    
    print("🎨 正在生成四大守護勇者 (頭像與立繪)...")
    heroes_def = [
        # hero 1: 莫莫
        ("hero_sprite.png", "avatar_purple.png", "莫莫 Momo", "黑金魔法師 · 腐植賢者", "法術輸出 · 分解魔力", 
         (16, 185, 129), (6, 95, 70), "🧙‍♂️", "落葉果皮變黑金，微生物是好幫手！"),
        # hero 2: 寇寇
        ("hero_sprite_round.png", "avatar_round.png", "寇寇 Koko", "堆肥小勇士 · 翻堆大地聖騎", "重裝防禦 · 翻堆通氣", 
         (59, 130, 246), (30, 58, 138), "🛡️", "勤翻堆又保通氣，土壤鬆軟根鬚壯！"),
        # hero 3: 露露
        ("hero_sprite_syl.png", "avatar_syl.png", "露露 Lulu", "分類精靈 · 源頭守護者", "超高暴擊 · 異物剔除", 
         (245, 158, 11), (180, 83, 9), "🧚‍♀️", "生熟廚餘分清楚，塑膠雜物不准進！"),
        # hero 4: 嘟嘟
        ("hero_sprite_mul.png", "avatar_mul.png", "嘟嘟 Dudu", "熟食巡守俠 · 豬豬大胃王", "食慾爆發 · 熟廚餘循環", 
         (239, 68, 68), (153, 27, 27), "🐖", "熟飯菜湯要瀝乾，豬豬飽餐力氣大！"),
    ]
    
    for s_file, a_file, name, title, role, c_pri, c_sec, sym, quote in heroes_def:
        av, sp = create_hero_graphics(s_file, name, title, role, c_pri, c_sec, sym, quote)
        av.save(os.path.join(img_dir, a_file), "PNG")
        sp.save(os.path.join(img_dir, s_file), "PNG")
        print(f"  ✓ {name}: {a_file}, {s_file}")

    print("👾 正在生成五大關主魔王立繪...")
    bosses_def = [
        ("slime_sprite.png", "第 1 關", "浪費剩食怪", "吃不完飯菜凝聚的黏稠巨魔", 
         (245, 158, 11), (120, 53, 15), "🍲", "餐桌惜食大挑戰！吃多少盛多少，擊退剩食怪！"),
        ("mirage_sprite.png", "第 2 關", "混雜垃圾魔", "塑膠與餐具纏繞的分類破壞者", 
         (239, 68, 68), (127, 29, 29), "🗑️", "源頭精準分類！剔除塑膠袋、免洗筷與橡皮筋！"),
        ("demon_sprite.png", "第 3 關", "惡臭果蠅王", "過濕與腐敗滋生的嗡嗡飛蟲王", 
         (168, 85, 247), (88, 28, 135), "🪰", "加入落葉吸乾水分，覆蓋乾料擊退刺鼻異味！"),
        ("frost_sprite.png", "第 4 關", "板結枯土巨魔", "缺乏腐植質而硬邦邦的乾裂石怪", 
         (100, 116, 139), (30, 41, 59), "🪨", "施入熟成黑金堆肥，讓土地呼吸、根鬚舒展！"),
        ("boss_sprite.png", "第 5 關", "失衡異變巨神", "食物鏈斷裂與污染集結的枯竭邪神", 
         (220, 38, 38), (69, 10, 10), "🌋", "串起土地到餐桌的永續食物循環，成就黑金奇蹟！")
    ]
    
    for b_file, ch, b_name, b_sub, c_p, c_d, sym, desc in bosses_def:
        b_sp = create_boss_graphics(b_file, ch, b_name, b_sub, c_p, c_d, sym, desc)
        b_sp.save(os.path.join(img_dir, b_file), "PNG")
        print(f"  ✓ {b_name}: {b_file}")

    print("🌄 正在生成五大戰鬥背景與兩大全域場景...")
    bgs_def = [
        ("forest_bg.jpg", "第一章：學院惜食大廳", "餐桌惜食與源頭減量試煉", (20, 30, 45), (45, 25, 15), "hall"),
        ("desert_bg.jpg", "第二章：中央分類迴廊", "生廚餘、熟廚餘與一般垃圾黃金分流", (15, 45, 35), (20, 60, 45), "sorting"),
        ("river_bg.jpg", "第三章：黑金發酵溫室", "碳氮平衡、通氣與瀝乾控水工藝", (35, 30, 15), (20, 50, 30), "greenhouse"),
        ("highway_bg.jpg", "第四章：陽光有機菜園", "翻土通氣、熟成黑金回饋大地", (30, 64, 175), (22, 101, 52), "garden"),
        ("sacred_bg.jpg", "第五章：永續生命神殿", "黑金魔法完全循環·生命永續傳承", (15, 23, 42), (4, 120, 87), "temple"),
        ("title_bg.jpg", "黑金魔法術：永續食物循環系統", "溪洲魔法生態學院 · 綠色冒險啟程", (15, 23, 42), (5, 46, 22), "title"),
        ("world_map.jpg", "溪洲魔法生態學院 · 永續食物循環地圖", "探索五大生態關卡 · 實踐土地到餐桌循環", (69, 26, 3), (20, 83, 45), "map"),
    ]
    
    for bg_file, title, subtitle, top_c, bot_c, d_type in bgs_def:
        bg_img = create_scenic_background(title, subtitle, top_c, bot_c, d_type)
        bg_img.save(os.path.join(img_dir, bg_file), "JPEG", quality=92)
        print(f"  ✓ {title}: {bg_file}")

    print("📱 正在生成應用程式圖示 (app_icon.png, app_icon.ico)...")
    icon_img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d_ico = ImageDraw.Draw(icon_img)
    # 翡翠黑金漸層圓角底圖
    d_ico.rounded_rectangle([10, 10, 246, 246], radius=55, fill=(16, 185, 129), outline=(250, 204, 21), width=6)
    d_ico.rounded_rectangle([25, 25, 231, 231], radius=45, fill=(15, 23, 42))
    f_ico = get_font(100, bold=True)
    d_ico.text((128, 128), "🧙‍♂️", fill=(255, 255, 255), anchor="mm", font=f_ico)
    icon_img.save("app_icon.png", "PNG")
    icon_img.save("app_icon.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
    print("  ✓ app_icon.png, app_icon.ico")
    
    print("\n🎉 全套 20 張遊戲核心圖片與應用程式圖示生成完畢！")

if __name__ == "__main__":
    main()
