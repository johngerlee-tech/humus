#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《黑金魔法術─永續食物循環系統》- 本機專用 Python 遊戲伺服器
提供靜態網頁檔案託管及 Game-data 資料夾下的題庫、存檔、自訂換膚與設定 API
"""

import base64
import http.server
import io
import json
import mimetypes
import os
import re
import sys
import time
import urllib.parse
import zipfile
from http import HTTPStatus

# 設定連接埠與根目錄
PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Game-data")
IMAGES_DIR = os.path.join(BASE_DIR, "assets", "images")
CUSTOM_IMG_DIR = os.path.join(IMAGES_DIR, "custom")

# 確保 Game-data 與自訂圖片資料夾存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CUSTOM_IMG_DIR, exist_ok=True)

# 補充常見 MIME 類型
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("image/jpeg", ".jpg")
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("image/webp", ".webp")

# 系統 20 張核心遊戲圖片清單與 AI 生圖建議 Prompt
GAME_IMAGES_META = [
    # --- 四大守護勇者 ---
    {
        "filename": "hero_sprite.png",
        "category": "heroes",
        "categoryName": "四大守護勇者",
        "name": "莫莫 Momo（黑金魔法師）立繪",
        "desc": "戰鬥舞台主角全身戰鬥立繪（精通微生物分解魔法）",
        "spec": "PNG (透明背景) ｜ 建議 800×1000",
        "defaultPath": "assets/images/hero_sprite.png",
        "promptEn": "Full-body anime character sprite, cute young eco-wizard boy named Momo, Akira Toriyama style, pointy dark-brown wizard hat with emerald trim and golden star, friendly cheerful smile, forest green magic cape with autumn leaf pattern, holding a wooden magic staff topped with a glowing green fermentation crystal orb, floating sparkles, clean isolated transparent background, 2D RPG game asset --ar 3:4",
        "promptZh": "鳥山明風格可愛黑金魔法師少年莫莫，戴深褐與翡翠色尖長巫師帽，身穿落葉綠色斗篷，手持頂端鑲嵌發光綠晶球的木法杖，周圍飄散微生魔法光點，透明背景。"
    },
    {
        "filename": "avatar_purple.png",
        "category": "heroes",
        "categoryName": "四大守護勇者",
        "name": "莫莫 Momo（黑金魔法師）頭像",
        "desc": "主畫面、對話框與對抗狀態頭像",
        "spec": "PNG (透明背景) ｜ 建議 400×400",
        "defaultPath": "assets/images/avatar_purple.png",
        "promptEn": "Square profile avatar icon, close-up face portrait of young wizard boy Momo, Akira Toriyama style, warm smiling expression, bright dark eyes, brown wizard hat, green cape collar, glowing magical sparkles, clean line art, transparent background, RPG dialogue face icon --ar 1:1",
        "promptZh": "黑金魔法師少年莫莫頭像特寫，溫暖開朗微笑，戴尖頂巫師帽，身著綠色斗篷，透明背景。"
    },
    {
        "filename": "hero_sprite_round.png",
        "category": "heroes",
        "categoryName": "四大守護勇者",
        "name": "寇寇 Koko（堆肥小勇士）立繪",
        "desc": "戰鬥舞台寇寇全身防禦戰鬥姿態立繪（翻堆通氣與重裝園藝）",
        "spec": "PNG (透明背景) ｜ 建議 800×1000",
        "defaultPath": "assets/images/hero_sprite_round.png",
        "promptEn": "Full-body anime character sprite, courageous garden warrior boy named Koko, Akira Toriyama style, cobalt blue gardening armor overalls, warrior helmet with cute green sprout crest, holding a golden garden trowel shovel in one hand and a sturdy aeration wooden shield in the other, brave hearty grin, earthy aura, clean isolated transparent background, 2D RPG game asset --ar 3:4",
        "promptZh": "鳥山明風格勇敢園藝堆肥小勇士寇寇，戴萌芽頭盔，身穿鈷藍色工作輕甲，手持金色園藝鏟與堅固通氣木盾，豪爽自信微笑，透明背景。"
    },
    {
        "filename": "avatar_round.png",
        "category": "heroes",
        "categoryName": "四大守護勇者",
        "name": "寇寇 Koko（堆肥小勇士）頭像",
        "desc": "寇寇主畫面選角與對話框頭像",
        "spec": "PNG (透明背景) ｜ 建議 400×400",
        "defaultPath": "assets/images/avatar_round.png",
        "promptEn": "Square profile avatar icon, close-up portrait of cheerful garden warrior boy Koko, Akira Toriyama style, warrior helmet with tiny green sprout on top, beaming enthusiastic smile, bright blue collar, transparent background, RPG dialogue icon --ar 1:1",
        "promptZh": "堆肥小勇士寇寇頭像特寫，戴綠芽頭盔，朝氣蓬勃的燦爛笑容，透明背景。"
    },
    {
        "filename": "hero_sprite_syl.png",
        "category": "heroes",
        "categoryName": "四大守護勇者",
        "name": "露露 Lulu（分類精靈）立繪",
        "desc": "戰鬥舞台露露精靈疾速突刺立繪（源頭分類與挑出異物）",
        "spec": "PNG (透明背景) ｜ 建議 800×1000",
        "defaultPath": "assets/images/hero_sprite_syl.png",
        "promptEn": "Full-body anime character sprite, adorable nature fairy girl named Lulu, Akira Toriyama style, twin yellow hair buns, glowing translucent fairy wings, bright amber and emerald dress, holding dual twin-leaf daggers and a filtering sieve shield, sparkling clean aura, dynamic floating battle pose, clean transparent background, 2D game asset --ar 3:4",
        "promptZh": "鳥山明風格靈巧可愛分類精靈露露，包包頭髮型，晶瑩精靈翅膀，身穿亮黃綠色精靈裙，手持雙葉敏捷短刃與瀝乾濾網盾牌，透明背景。"
    },
    {
        "filename": "avatar_syl.png",
        "category": "heroes",
        "categoryName": "四大守護勇者",
        "name": "露露 Lulu（分類精靈）頭像",
        "desc": "露露主畫面選角與對話框頭像",
        "spec": "PNG (透明背景) ｜ 建議 400×400",
        "defaultPath": "assets/images/avatar_syl.png",
        "promptEn": "Square profile avatar icon, close-up face portrait of cute fairy girl Lulu, Akira Toriyama style, bright turquoise eyes, mischievous sweet smile, twin amber hair buns, golden glow, transparent background, 2D RPG icon --ar 1:1",
        "promptZh": "分類精靈露露頭像特寫，琥珀色包包頭，明亮清澈的藍綠眼眸與俏皮笑容，透明背景。"
    },
    {
        "filename": "hero_sprite_mul.png",
        "category": "heroes",
        "categoryName": "四大守護勇者",
        "name": "嘟嘟 Dudu（熟食巡守俠）立繪",
        "desc": "戰鬥舞台嘟嘟大胃俠突進立繪（熟廚餘循環巡守）",
        "spec": "PNG (透明背景) ｜ 建議 800×1000",
        "defaultPath": "assets/images/hero_sprite_mul.png",
        "promptEn": "Full-body anime character sprite, cheerful anthropomorphic piggy chef hero named Dudu, Akira Toriyama style like Oolong, wearing red adventurer chef bandanna and apron, holding a giant wooden serving ladle and wearing a bubbling stew pot shield, hearty wide grin, vibrant warm colors, clean isolated transparent background, 2D RPG game sprite --ar 3:4",
        "promptZh": "鳥山明烏龍風格可愛小豬大胃廚師英雄嘟嘟，頭戴紅頭巾圍著圍裙，手持巨型木勺，充滿食慾與活力，透明背景。"
    },
    {
        "filename": "avatar_mul.png",
        "category": "heroes",
        "categoryName": "四大守護勇者",
        "name": "嘟嘟 Dudu（熟食巡守俠）頭像",
        "desc": "嘟嘟主畫面選角與對話框頭像",
        "spec": "PNG (透明背景) ｜ 建議 400×400",
        "defaultPath": "assets/images/avatar_mul.png",
        "promptEn": "Square profile avatar icon, close-up portrait of jolly piggy chef hero Dudu, Akira Toriyama style, cute pink piggy snout, joyful laughing eyes, red chef bandanna, transparent background, 2D RPG portrait --ar 1:1",
        "promptZh": "熟食巡守小豬嘟嘟頭像特寫，粉紅小豬鼻，大笑的歡樂表情，戴紅廚師頭巾，透明背景。"
    },

    # --- 五大關卡試煉魔王 ---
    {
        "filename": "slime_sprite.png",
        "category": "bosses",
        "categoryName": "五大關卡試煉魔王",
        "name": "第 1 關關主「浪費剩食怪」立繪",
        "desc": "第一章學院惜食大廳守護魔王戰鬥立繪",
        "spec": "PNG (透明背景) ｜ 建議 800×900",
        "defaultPath": "assets/images/slime_sprite.png",
        "promptEn": "Comical food waste slime boss monster, Akira Toriyama Dragon Quest monster style, wobbly giant yellow-brown gelatinous soup blob, wearing a food bowl on head, mouth full of half-eaten noodles and spilled gravy, arms made of floating soup ladles, goofy greedy face, splash particles around, clean isolated transparent background, 2D RPG boss sprite --ar 1:1",
        "promptZh": "鳥山明風格滑稽剩食史萊姆巨魔，由油湯飯菜凝聚的黏稠果凍怪獸，頭頂打翻的湯碗，嘴邊掛著麵條與湯汁，滑稽貪吃，透明背景。"
    },
    {
        "filename": "mirage_sprite.png",
        "category": "bosses",
        "categoryName": "五大關卡試煉魔王",
        "name": "第 2 關關主「混雜垃圾魔」立繪",
        "desc": "第二章中央分類迴廊守護魔王戰鬥立繪",
        "spec": "PNG (透明背景) ｜ 建議 800×900",
        "defaultPath": "assets/images/mirage_sprite.png",
        "promptEn": "Trash confusion beast boss monster, Akira Toriyama scrap monster style, chaotic creature made of crumpled plastic bags, discarded disposable chopsticks, tangled rubber bands, and soda cans, glowing angry red optical eyes, thrashing clawed limbs of wire and plastic, battle stance, clean isolated transparent background, 2D RPG boss sprite --ar 1:1",
        "promptZh": "鳥山明風格混雜垃圾怪獸，由塑膠袋、免洗筷、橡皮筋與飲料罐纏繞而成的雜物狂魔，憤怒紅色眼睛，張牙舞爪，透明背景。"
    },
    {
        "filename": "demon_sprite.png",
        "category": "bosses",
        "categoryName": "五大關卡試煉魔王",
        "name": "第 3 關關主「惡臭果蠅王」立繪",
        "desc": "第三章黑金發酵溫室守護魔王戰鬥立繪",
        "spec": "PNG (透明背景) ｜ 建議 800×900",
        "defaultPath": "assets/images/demon_sprite.png",
        "promptEn": "Giant pest fruit fly king boss monster, Akira Toriyama insect monster style, plump winged fly with purple-black fuzzy body, huge ruby-red multifaceted compound eyes, wearing a rotten fruit peel crown, buzzing transparent wings creating stinky green wavy odor waves, comical menacing posture, clean transparent background, 2D RPG boss sprite --ar 1:1",
        "promptZh": "鳥山明怪獸風格果蠅魔王，毛茸茸紫黑巨型蒼蠅，戴著爛果皮王冠，巨大紅複眼，震動翅膀釋放綠色臭味波紋，透明背景。"
    },
    {
        "filename": "frost_sprite.png",
        "category": "bosses",
        "categoryName": "五大關卡試煉魔王",
        "name": "第 4 關關主「板結枯土巨魔」立繪",
        "desc": "第四章陽光有機菜園守護魔王戰鬥立繪",
        "spec": "PNG (透明背景) ｜ 建議 800×900",
        "defaultPath": "assets/images/frost_sprite.png",
        "promptEn": "Dry compacted clay golem boss monster, Akira Toriyama stone monster style, massive bulky earth golem with parched cracked dry grey-brown mudstone body, withered plant roots trapped and suffocating across its stone chest, glowing amber eyes, raising heavy rocky fist, dust falling, clean isolated transparent background, 2D RPG boss sprite --ar 1:1",
        "promptZh": "鳥山明岩石魔像風格板結枯土巨魔，身軀由乾裂灰褐硬泥塊構成，胸前纏繞枯竭樹根，眼冒琥珀紅光，揮動沉重石拳，透明背景。"
    },
    {
        "filename": "boss_sprite.png",
        "category": "bosses",
        "categoryName": "五大關卡試煉魔王",
        "name": "第 5 關終極關主「失衡異變巨神」立繪",
        "desc": "第五章永續生命神殿終極守護魔王立繪",
        "spec": "PNG (透明背景) ｜ 建議 900×1000",
        "defaultPath": "assets/images/boss_sprite.png",
        "promptEn": "Colossal final boss deity of ecological imbalance, Akira Toriyama grand villain design, imposing biomechanical titan, left half made of withered dead sacred tree trunks and burning furnace smokestacks with dark ash smoke, right half glowing with toxic purple smog core and rusted industrial scrap gears, towering majestic posture, clean isolated transparent background, 2D RPG final boss sprite --ar 1:1",
        "promptZh": "鳥山明風格終極環境失衡邪神，半身枯死神木與燃燒黑煙囪，半身紫霧金屬異變齒輪，浩瀚威嚴壓迫感，透明背景。"
    },

    # --- 五大關卡戰鬥背景 ---
    {
        "filename": "forest_bg.jpg",
        "category": "backgrounds",
        "categoryName": "五大關卡戰鬥背景",
        "name": "第 1 關背景：學院惜食大廳",
        "desc": "第一章惜食大廳餐桌試煉戰鬥背景場景",
        "spec": "JPG (16:9 寬螢幕) ｜ 建議 1920×1080",
        "defaultPath": "assets/images/forest_bg.jpg",
        "promptEn": "Scenic JRPG battle stage background, grand wooden dining banquet hall of magic academy, warm golden lanterns hanging from vaulted wooden beams, long dining tables with healthy colorful food, students tableware banners on stone walls, Akira Toriyama anime interior style, warm lighting, 16:9 landscape wallpaper --ar 16:9",
        "promptZh": "魔法生態學院宏偉木造惜食大廳，暖黃吊燈照耀拱形木樑，餐桌排列整齊，充滿溫馨活力的宴會廳，16:9 鳥山明室內風格。"
    },
    {
        "filename": "desert_bg.jpg",
        "category": "backgrounds",
        "categoryName": "五大關卡戰鬥背景",
        "name": "第 2 關背景：中央分類迴廊",
        "desc": "第二章生熟廚餘與回收分類站戰鬥背景場景",
        "spec": "JPG (16:9 寬螢幕) ｜ 建議 1920×1080",
        "defaultPath": "assets/images/desert_bg.jpg",
        "promptEn": "Scenic JRPG battle stage background, modern eco-friendly waste sorting corridor station, colorful sorting bins for raw food waste, cooked pig feed, and recyclables, bright skylight roof filtering sunshine, educational green leaf murals on walls, Akira Toriyama adventure background, 16:9 --ar 16:9",
        "promptZh": "現代綠色環保中央分類迴廊，彩色分類桶（生廚餘、熟廚餘、資源回收），天窗灑落陽光，牆面繪有綠葉壁畫，16:9。"
    },
    {
        "filename": "river_bg.jpg",
        "category": "backgrounds",
        "categoryName": "五大關卡戰鬥背景",
        "name": "第 3 關背景：黑金發酵溫室",
        "desc": "第三章黑金堆肥箱與通氣發酵工藝背景場景",
        "spec": "JPG (16:9 寬螢幕) ｜ 建議 1920×1080",
        "defaultPath": "assets/images/river_bg.jpg",
        "promptEn": "Scenic JRPG battle stage background, sunny wooden composting greenhouse, wooden fermentation boxes filled with rich dark organic compost, golden sunlight beams shining through glass roof, gentle steam rising from active compost pile, tools hanging neatly, Akira Toriyama landscape, 16:9 --ar 16:9",
        "promptZh": "陽光充沛的木質堆肥溫室，木箱盛滿黑褐有機腐植土，陽光透過玻璃天窗灑下，堆肥升起溫暖蒸氣，16:9。"
    },
    {
        "filename": "highway_bg.jpg",
        "category": "backgrounds",
        "categoryName": "五大關卡戰鬥背景",
        "name": "第 4 關背景：陽光有機菜園",
        "desc": "第四章校園菜園黑金土壤回饋大地場景",
        "spec": "JPG (16:9 寬螢幕) ｜ 建議 1920×1080",
        "defaultPath": "assets/images/highway_bg.jpg",
        "promptEn": "Scenic JRPG battle stage background, vibrant school organic vegetable garden under brilliant blue sky, raised wooden garden beds filled with dark fertile compost soil, flourishing green lettuce and sunflowers, gentle distant green hills, Akira Toriyama anime farm style, 16:9 --ar 16:9",
        "promptZh": "陽光明媚的校園有機菜園，藍天下排列整齊的黑沃土壤花壇，生機盎然的蔬菜與向日葵，遠山蒼翠，16:9。"
    },
    {
        "filename": "sacred_bg.jpg",
        "category": "backgrounds",
        "categoryName": "五大關卡戰鬥背景",
        "name": "第 5 關背景：永續生命神殿",
        "desc": "第五章永續食物循環生命之樹聖境背景場景",
        "spec": "JPG (16:9 寬螢幕) ｜ 建議 1920×1080",
        "defaultPath": "assets/images/sacred_bg.jpg",
        "promptEn": "Scenic JRPG battle stage background, mystical sacred World Tree of ecological circulation, colossal ancient tree rooted in glowing rich black soil, crown touching starry auroras, floating golden pollen and green energy rings forming eternal cycle symbol, dreamlike peaceful paradise, Akira Toriyama magical forest style, 16:9 --ar 16:9",
        "promptZh": "永續生態循環世界之樹神殿，根植於發光黑沃土的參天巨木，星光晨曦與金色光環環繞，象徵永恆食物循環之環，16:9。"
    },

    # --- 遊戲全域場景 ---
    {
        "filename": "title_bg.jpg",
        "category": "system",
        "categoryName": "遊戲全域場景",
        "name": "冒險啟程主畫面背景",
        "desc": "遊戲主登入、學生簽到與選角畫面全螢幕背景",
        "spec": "JPG (16:9 寬螢幕) ｜ 建議 1920×1080",
        "defaultPath": "assets/images/title_bg.jpg",
        "promptEn": "Anime JRPG title screen background art, panoramic view of magical eco-academy campus surrounded by rolling emerald hills and lush vegetable gardens, floating leaves and golden sparkles drifting across dawn sky, Akira Toriyama anime opening cinematic style, hopeful adventure atmosphere, 16:9 --ar 16:9",
        "promptZh": "遊戲主畫面背景，鳥瞰溪洲魔法生態學院美麗校園與金色田園，晨光初照，飛舞的綠葉與金色光芒，冒險啟程序幕，16:9。"
    },
    {
        "filename": "world_map.jpg",
        "category": "system",
        "categoryName": "遊戲全域場景",
        "name": "永續食物循環世界地圖",
        "desc": "世界大地圖探索與關卡導航地圖底圖",
        "spec": "JPG (16:9 寬螢幕) ｜ 建議 1920×1080",
        "defaultPath": "assets/images/world_map.jpg",
        "promptEn": "Fantasy illustrated RPG overworld map of magical eco-campus, antique parchment textured map showing banquet hall, sorting station, greenhouse, organic farm, and sacred tree connected by glowing golden circular trail, Dragon Quest overworld map aesthetic, charming details, 16:9 --ar 16:9",
        "promptZh": "復古羊皮紙奇幻世界大地圖，標繪惜食大廳、分類站、發酵溫室、有機菜園與神殿之金色環形循環航線，勇者鬥惡龍大地圖風格，16:9。"
    }
]

VALID_FILENAMES = {item["filename"].lower(): item["filename"] for item in GAME_IMAGES_META}


def load_json_permissive(filepath):
    """寬容讀取 JSON 檔案，支援過濾註解及多餘逗號"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pattern = r'("(?:\\.|[^"\\])*")|(/\*[\s\S]*?\*/|//[^\r\n]*)'
        cleaned = re.sub(pattern, lambda m: m.group(1) if m.group(1) else "", content)
        cleaned = re.sub(r',\s*([\]\}])', r'\1', cleaned)
        return json.loads(cleaned)


class RPGGameRequestHandler(http.server.SimpleHTTPRequestHandler):
    """自訂 HTTP 請求處理器，處理靜態資源與 Game-data 資料夾的 API 讀寫"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def _set_headers(self, status_code=HTTPStatus.OK, content_type="application/json; charset=utf-8"):
        """發送標準回應標頭與 CORS 標頭"""
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

    def do_OPTIONS(self):
        """處理 CORS 預檢請求"""
        self._set_headers(HTTPStatus.NO_CONTENT)

    def do_GET(self):
        """處理 GET 請求：支援 API 與一般靜態檔案"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        # 預設頁面
        if path == "/":
            self.path = "/index.html"
            return super().do_GET()

        # API: 讀取題庫資料
        if path == "/api/questions":
            questions_file = os.path.join(DATA_DIR, "questions.json")
            if os.path.exists(questions_file):
                try:
                    with open(questions_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._set_headers(HTTPStatus.OK)
                    self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
                except Exception as e:
                    self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
                    self.wfile.write(json.dumps({"error": f"讀取題庫失敗: {str(e)}"}).encode("utf-8"))
            else:
                self._set_headers(HTTPStatus.OK)
                self.wfile.write(json.dumps([]).encode("utf-8"))
            return

        # API: 讀取遊戲設定
        if path == "/api/config":
            config_file = os.path.join(DATA_DIR, "config.json")
            if os.path.exists(config_file):
                try:
                    data = load_json_permissive(config_file)
                    self._set_headers(HTTPStatus.OK)
                    self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
                except Exception as e:
                    self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
                    self.wfile.write(json.dumps({"error": f"讀取設定失敗: {str(e)}"}).encode("utf-8"))
            else:
                self._set_headers(HTTPStatus.NOT_FOUND)
                self.wfile.write(json.dumps({"error": "找不到設定檔"}).encode("utf-8"))
            return

        # API: 讀取範例 CSV 題庫
        if path == "/api/sample-csv":
            sample_file = os.path.join(DATA_DIR, "sample_import.csv")
            if os.path.exists(sample_file):
                try:
                    with open(sample_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    self._set_headers(HTTPStatus.OK, "text/plain; charset=utf-8")
                    self.wfile.write(content.encode("utf-8"))
                except Exception as e:
                    self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
                    self.wfile.write(f"讀取範例失敗: {str(e)}".encode("utf-8"))
            else:
                self._set_headers(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8")
                self.wfile.write("找不到範例檔案".encode("utf-8"))
            return

        # API: 讀取遊戲存檔
        if path == "/api/save-game":
            save_file = os.path.join(DATA_DIR, "saves.json")
            if os.path.exists(save_file):
                try:
                    with open(save_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._set_headers(HTTPStatus.OK)
                    self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
                except Exception as e:
                    self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
                    self.wfile.write(json.dumps({"error": f"讀取存檔失敗: {str(e)}"}).encode("utf-8"))
            else:
                self._set_headers(HTTPStatus.OK)
                self.wfile.write(json.dumps({}).encode("utf-8"))
            return

        # API: 讀取多組題庫列表 (Question Banks)
        if path == "/api/question-banks":
            banks_file = os.path.join(DATA_DIR, "question_banks.json")
            if os.path.exists(banks_file):
                try:
                    with open(banks_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._set_headers(HTTPStatus.OK)
                    self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
                except Exception as e:
                    self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
                    self.wfile.write(json.dumps({"error": f"讀取題庫組失敗: {str(e)}"}).encode("utf-8"))
            else:
                self._set_headers(HTTPStatus.OK)
                self.wfile.write(json.dumps([]).encode("utf-8"))
            return

        # API: 讀取主題測驗列表 (Thematic Exams)
        if path == "/api/exams":
            exams_file = os.path.join(DATA_DIR, "exams.json")
            if os.path.exists(exams_file):
                try:
                    with open(exams_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._set_headers(HTTPStatus.OK)
                    self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
                except Exception as e:
                    self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
                    self.wfile.write(json.dumps({"error": f"讀取主題測驗失敗: {str(e)}"}).encode("utf-8"))
            else:
                self._set_headers(HTTPStatus.OK)
                self.wfile.write(json.dumps([]).encode("utf-8"))
            return

        # API: 讀取學生答題紀錄列表 (Student Records)
        if path == "/api/student-records":
            records_file = os.path.join(DATA_DIR, "student_records.json")
            if os.path.exists(records_file):
                try:
                    with open(records_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._set_headers(HTTPStatus.OK)
                    self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
                except Exception as e:
                    self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
                    self.wfile.write(json.dumps({"error": f"讀取學生作答紀錄失敗: {str(e)}"}).encode("utf-8"))
            else:
                self._set_headers(HTTPStatus.OK)
                self.wfile.write(json.dumps([]).encode("utf-8"))
            return

        # API: 讀取本地資料儲存檔案資訊 (Storage Info)
        if path == "/api/storage-info":
            storage_files = [
                {
                    "filename": "student_records.json",
                    "relativePath": "Game-data/student_records.json",
                    "title": "學生作答歷程與錯題明細",
                    "description": "記錄所有學生姓名、所選主題測驗、總分、答對率、闖關章節、每題作答詳情（所選選項、正解與時間戳記）。",
                    "category": "學生數據",
                    "format": "JSON Array (物件陣列)"
                },
                {
                    "filename": "question_banks.json",
                    "relativePath": "Game-data/question_banks.json",
                    "title": "多組主題題庫與自訂題目",
                    "description": "存放教師建立或匯入的多組分類題庫（題目內容、四個選項、正確答案索引、詳解說明與啟用狀態）。",
                    "category": "題庫設定",
                    "format": "JSON Array (題庫組物件陣列)"
                },
                {
                    "filename": "exams.json",
                    "relativePath": "Game-data/exams.json",
                    "title": "派送主題測驗發布設定",
                    "description": "存放教師派送建立的主題測驗（名稱、分類、任務說明、關聯題庫組別清單與派送啟用狀態）。",
                    "category": "測驗派送",
                    "format": "JSON Array (測驗設定陣列)"
                },
                {
                    "filename": "questions.json",
                    "relativePath": "Game-data/questions.json",
                    "title": "基礎單一題庫 (相容模式)",
                    "description": "系統預設或舊版相容的單一題庫題目資料檔案。",
                    "category": "題庫設定",
                    "format": "JSON Array (題目陣列)"
                },
                {
                    "filename": "config.json",
                    "relativePath": "Game-data/config.json",
                    "title": "遊戲全域系統與數值平衡設定",
                    "description": "存放後台管理密碼（預設 admin）、四大勇者與五大魔王各項攻防生命數值及換膚路徑。",
                    "category": "系統配置",
                    "format": "JSON Object (鍵值配置)"
                },
                {
                    "filename": "saves.json",
                    "relativePath": "Game-data/saves.json",
                    "title": "玩家角色與闖關進度存檔",
                    "description": "記錄本機玩家的關卡解鎖進度、最高得分與當前選定勇者。",
                    "category": "遊戲存檔",
                    "format": "JSON Object (玩家進度)"
                },
                {
                    "filename": "sample_import.csv",
                    "relativePath": "Game-data/sample_import.csv",
                    "title": "示範題庫 CSV 匯入樣版",
                    "description": "提供教師出題參考與一鍵測試匯入的標準 CSV 格式檔案（題目,答案編號,選項1~4,解析）。",
                    "category": "範例資料",
                    "format": "CSV 純文字"
                }
            ]

            result = []
            for item in storage_files:
                fpath = os.path.join(DATA_DIR, item["filename"])
                exists = os.path.exists(fpath)
                size_bytes = os.path.getsize(fpath) if exists else 0
                mtime = os.path.getmtime(fpath) if exists else None
                record_count = None

                if exists and item["filename"].endswith(".json"):
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            jdata = json.load(f)
                            if isinstance(jdata, list):
                                record_count = len(jdata)
                            elif isinstance(jdata, dict):
                                record_count = len(jdata.keys())
                    except Exception:
                        pass

                result.append({
                    **item,
                    "exists": exists,
                    "sizeBytes": size_bytes,
                    "sizeFormatted": f"{size_bytes / 1024:.2f} KB" if size_bytes >= 1024 else f"{size_bytes} B",
                    "lastModified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)) if mtime else "尚無檔案",
                    "recordCount": record_count
                })

            self._set_headers(HTTPStatus.OK)
            self.wfile.write(json.dumps({
                "dataDir": DATA_DIR,
                "files": result
            }, ensure_ascii=False, indent=2).encode("utf-8"))
            return

        # API: 查詢系統所有 20 張核心圖片之自訂狀態與預覽路徑
        if path == "/api/images-status":
            try:
                config_file = os.path.join(DATA_DIR, "config.json")
                cfg = {}
                if os.path.exists(config_file):
                    try:
                        cfg = load_json_permissive(config_file)
                    except Exception:
                        cfg = {}

                custom_images = cfg.get("customImages", {}) if isinstance(cfg, dict) else {}

                images_list = []
                for meta in GAME_IMAGES_META:
                    fname = meta["filename"]
                    custom_path = os.path.join(CUSTOM_IMG_DIR, fname)
                    is_custom = os.path.exists(custom_path)

                    if is_custom:
                        mtime = os.path.getmtime(custom_path)
                        size_bytes = os.path.getsize(custom_path)
                        current_url = f"assets/images/custom/{fname}?t={int(mtime)}"
                        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
                    else:
                        default_sys_path = os.path.join(BASE_DIR, meta["defaultPath"])
                        mtime = os.path.getmtime(default_sys_path) if os.path.exists(default_sys_path) else None
                        size_bytes = os.path.getsize(default_sys_path) if os.path.exists(default_sys_path) else 0
                        current_url = meta["defaultPath"]
                        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime)) if mtime else "預設資源"

                    images_list.append({
                        **meta,
                        "isCustom": is_custom,
                        "currentUrl": current_url,
                        "sizeBytes": size_bytes,
                        "sizeFormatted": f"{size_bytes / 1024:.1f} KB" if size_bytes >= 1024 else f"{size_bytes} B",
                        "lastModified": time_str
                    })

                self._set_headers(HTTPStatus.OK)
                self.wfile.write(json.dumps({
                    "success": True,
                    "total": len(images_list),
                    "customCount": sum(1 for img in images_list if img["isCustom"]),
                    "images": images_list
                }, ensure_ascii=False, indent=2).encode("utf-8"))
            except Exception as e:
                self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.wfile.write(json.dumps({"success": False, "error": f"取得圖片狀態失敗: {str(e)}"}).encode("utf-8"))
            return

        # 其餘由父類別處理靜態檔案
        return super().do_GET()

    def do_POST(self):
        """處理 POST 請求：更新題庫、測驗、學生紀錄或存檔至 Game-data 目錄"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"

        # API: 單張自訂圖片上傳取代
        if path == "/api/upload-image":
            try:
                data = json.loads(post_body)
                raw_filename = data.get("filename", "").strip()
                base64_data = data.get("data", "").strip()

                lower_fname = raw_filename.lower()
                if lower_fname not in VALID_FILENAMES:
                    self._set_headers(HTTPStatus.BAD_REQUEST)
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": f"不支援的圖片檔名: {raw_filename}。僅支援 20 張系統核心圖片！"
                    }).encode("utf-8"))
                    return

                matched_filename = VALID_FILENAMES[lower_fname]

                if "," in base64_data:
                    base64_data = base64_data.split(",", 1)[1]

                img_bytes = base64.b64decode(base64_data)
                os.makedirs(CUSTOM_IMG_DIR, exist_ok=True)
                target_path = os.path.join(CUSTOM_IMG_DIR, matched_filename)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                with open(target_path, "wb") as f:
                    f.write(img_bytes)

                # 同步更新 config.json
                config_file = os.path.join(DATA_DIR, "config.json")
                cfg = {}
                if os.path.exists(config_file):
                    try:
                        cfg = load_json_permissive(config_file)
                    except Exception:
                        cfg = {}

                if not isinstance(cfg, dict):
                    cfg = {}
                if "customImages" not in cfg or not isinstance(cfg["customImages"], dict):
                    cfg["customImages"] = {}

                timestamp = int(time.time())
                custom_url = f"assets/images/custom/{matched_filename}?t={timestamp}"
                cfg["customImages"][matched_filename] = custom_url

                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)

                self._set_headers(HTTPStatus.OK)
                self.wfile.write(json.dumps({
                    "success": True,
                    "filename": matched_filename,
                    "url": custom_url,
                    "sizeBytes": len(img_bytes),
                    "message": f"成功上傳並替換【{matched_filename}】！"
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.wfile.write(json.dumps({"success": False, "error": f"圖片上傳失敗: {str(e)}"}).encode("utf-8"))
            return

        # API: ZIP 壓縮檔批次上傳所有圖片 (按檔名比對，只處理符合檔名的圖片)
        if path == "/api/upload-zip-images":
            try:
                data = json.loads(post_body)
                base64_zip = data.get("zipData", "").strip()
                if not base64_zip:
                    self._set_headers(HTTPStatus.BAD_REQUEST)
                    self.wfile.write(json.dumps({"success": False, "error": "請提供有效的 ZIP 壓縮檔內容"}).encode("utf-8"))
                    return

                if "," in base64_zip:
                    base64_zip = base64_zip.split(",", 1)[1]

                zip_bytes = base64.b64decode(base64_zip)
                zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))

                updated_files = []
                skipped_files = []
                timestamp = int(time.time())

                # 讀取現有 config
                config_file = os.path.join(DATA_DIR, "config.json")
                cfg = {}
                if os.path.exists(config_file):
                    try:
                        cfg = load_json_permissive(config_file)
                    except Exception:
                        cfg = {}
                if not isinstance(cfg, dict):
                    cfg = {}
                if "customImages" not in cfg or not isinstance(cfg["customImages"], dict):
                    cfg["customImages"] = {}

                for zinfo in zip_file.infolist():
                    if zinfo.is_dir():
                        continue
                    fname = os.path.basename(zinfo.filename)
                    if not fname or fname.startswith(".") or fname.startswith("__MACOSX"):
                        continue

                    lower_name = fname.lower()
                    if lower_name in VALID_FILENAMES:
                        matched = VALID_FILENAMES[lower_name]
                        extracted_bytes = zip_file.read(zinfo)
                        os.makedirs(CUSTOM_IMG_DIR, exist_ok=True)
                        target_path = os.path.join(CUSTOM_IMG_DIR, matched)
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with open(target_path, "wb") as f:
                            f.write(extracted_bytes)

                        custom_url = f"assets/images/custom/{matched}?t={timestamp}"
                        cfg["customImages"][matched] = custom_url
                        updated_files.append({
                            "filename": matched,
                            "url": custom_url,
                            "sizeBytes": len(extracted_bytes)
                        })
                    else:
                        skipped_files.append(fname)

                if updated_files:
                    with open(config_file, "w", encoding="utf-8") as f:
                        json.dump(cfg, f, ensure_ascii=False, indent=2)

                self._set_headers(HTTPStatus.OK)
                self.wfile.write(json.dumps({
                    "success": True,
                    "updatedCount": len(updated_files),
                    "updatedFiles": updated_files,
                    "skippedCount": len(skipped_files),
                    "skippedFiles": skipped_files,
                    "message": f"壓縮檔批次處理完成：成功替換 {len(updated_files)} 張符合檔名的圖片！" +
                               (f"（略過 {len(skipped_files)} 個非系統圖片）" if skipped_files else "")
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.wfile.write(json.dumps({"success": False, "error": f"解壓縮與批次處理失敗: {str(e)}"}).encode("utf-8"))
            return

        # API: 單張或全部圖片改回預設圖片
        if path == "/api/reset-image":
            try:
                data = json.loads(post_body)
                raw_filename = data.get("filename", "").strip()
                reset_all = data.get("all", False)

                config_file = os.path.join(DATA_DIR, "config.json")
                cfg = {}
                if os.path.exists(config_file):
                    try:
                        cfg = load_json_permissive(config_file)
                    except Exception:
                        cfg = {}
                if not isinstance(cfg, dict):
                    cfg = {}
                if "customImages" not in cfg or not isinstance(cfg["customImages"], dict):
                    cfg["customImages"] = {}

                if reset_all:
                    if os.path.exists(CUSTOM_IMG_DIR):
                        for f in os.listdir(CUSTOM_IMG_DIR):
                            fpath = os.path.join(CUSTOM_IMG_DIR, f)
                            if os.path.isfile(fpath):
                                try:
                                    os.remove(fpath)
                                except Exception:
                                    pass
                    cfg["customImages"] = {}
                    with open(config_file, "w", encoding="utf-8") as f:
                        json.dump(cfg, f, ensure_ascii=False, indent=2)

                    self._set_headers(HTTPStatus.OK)
                    self.wfile.write(json.dumps({
                        "success": True,
                        "message": "已成功將系統所有圖片恢復為原始預設圖片！"
                    }, ensure_ascii=False).encode("utf-8"))
                    return

                lower_fname = raw_filename.lower()
                if lower_fname not in VALID_FILENAMES:
                    self._set_headers(HTTPStatus.BAD_REQUEST)
                    self.wfile.write(json.dumps({"success": False, "error": f"未知的圖片檔名: {raw_filename}"}).encode("utf-8"))
                    return

                matched = VALID_FILENAMES[lower_fname]
                custom_path = os.path.join(CUSTOM_IMG_DIR, matched)
                if os.path.exists(custom_path):
                    try:
                        os.remove(custom_path)
                    except Exception:
                        pass

                if matched in cfg["customImages"]:
                    del cfg["customImages"][matched]
                    with open(config_file, "w", encoding="utf-8") as f:
                        json.dump(cfg, f, ensure_ascii=False, indent=2)

                self._set_headers(HTTPStatus.OK)
                self.wfile.write(json.dumps({
                    "success": True,
                    "filename": matched,
                    "message": f"已成功將【{matched}】改回原始預設圖片！"
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.wfile.write(json.dumps({"success": False, "error": f"恢復預設圖片失敗: {str(e)}"}).encode("utf-8"))
            return

        # API: 儲存或更新多組題庫列表 (Question Banks)
        if path == "/api/question-banks":
            try:
                data = json.loads(post_body)
                banks_file = os.path.join(DATA_DIR, "question_banks.json")
                with open(banks_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self._set_headers(HTTPStatus.OK)
                response = {
                    "success": True,
                    "message": f"成功儲存 {len(data)} 組題庫至 Game-data/question_banks.json",
                    "count": len(data)
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(HTTPStatus.BAD_REQUEST)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # API: 儲存或更新主題測驗列表 (Thematic Exams)
        if path == "/api/exams":
            try:
                data = json.loads(post_body)
                exams_file = os.path.join(DATA_DIR, "exams.json")
                with open(exams_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self._set_headers(HTTPStatus.OK)
                response = {
                    "success": True,
                    "message": f"成功儲存 {len(data)} 個主題測驗至 Game-data/exams.json",
                    "count": len(data)
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(HTTPStatus.BAD_REQUEST)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # API: 儲存或追加學生答題紀錄 (Student Records)
        if path == "/api/student-records":
            try:
                new_data = json.loads(post_body)
                records_file = os.path.join(DATA_DIR, "student_records.json")
                existing = []
                if os.path.exists(records_file):
                    try:
                        with open(records_file, "r", encoding="utf-8") as f:
                            existing = json.load(f)
                            if not isinstance(existing, list):
                                existing = []
                    except Exception:
                        existing = []

                if isinstance(new_data, list):
                    existing.extend(new_data)
                elif isinstance(new_data, dict):
                    existing.append(new_data)

                with open(records_file, "w", encoding="utf-8") as f:
                    json.dump(existing, f, ensure_ascii=False, indent=2)

                self._set_headers(HTTPStatus.OK)
                response = {
                    "success": True,
                    "message": f"成功儲存學生作答紀錄至 Game-data/student_records.json (總計 {len(existing)} 筆)",
                    "count": len(existing)
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(HTTPStatus.BAD_REQUEST)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # API: 儲存或更新單一題庫資料 (相容模式)
        if path == "/api/questions":
            try:
                data = json.loads(post_body)
                questions_file = os.path.join(DATA_DIR, "questions.json")
                with open(questions_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self._set_headers(HTTPStatus.OK)
                response = {
                    "success": True,
                    "message": f"成功儲存 {len(data)} 道題目至 Game-data/questions.json",
                    "count": len(data)
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(HTTPStatus.BAD_REQUEST)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # API: 儲存遊戲存檔
        if path == "/api/save-game":
            try:
                data = json.loads(post_body)
                save_file = os.path.join(DATA_DIR, "saves.json")
                with open(save_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self._set_headers(HTTPStatus.OK)
                self.wfile.write(json.dumps({"success": True, "message": "進度已儲存至 Game-data/saves.json"}).encode("utf-8"))
            except Exception as e:
                self._set_headers(HTTPStatus.BAD_REQUEST)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # API: 儲存或更新遊戲設定與勇者/關主數值 (Game Config)
        if path == "/api/config":
            try:
                data = json.loads(post_body)
                config_file = os.path.join(DATA_DIR, "config.json")
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self._set_headers(HTTPStatus.OK)
                response = {
                    "success": True,
                    "message": "遊戲設定已成功儲存至 Game-data/config.json"
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(HTTPStatus.BAD_REQUEST)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # API: 刪除學生答題紀錄 (POST 備用相容路由)
        if path == "/api/student-records/delete":
            try:
                data = json.loads(post_body) if post_body else {}
                record_id = data.get("id")
                exam_id = data.get("examId")
                delete_all = data.get("all", False)

                records_file = os.path.join(DATA_DIR, "student_records.json")
                if not os.path.exists(records_file):
                    self._set_headers(HTTPStatus.OK)
                    self.wfile.write(json.dumps({"success": True, "message": "目前無任何紀錄", "deleted": 0, "remaining": 0}).encode("utf-8"))
                    return

                try:
                    with open(records_file, "r", encoding="utf-8") as f:
                        records = json.load(f)
                        if not isinstance(records, list):
                            records = []
                except Exception:
                    records = []

                initial_count = len(records)
                if delete_all:
                    records = []
                    msg = "已清空所有學生作答紀錄！"
                elif record_id:
                    records = [r for r in records if str(r.get("id")) != str(record_id) and str(r.get("completedAt")) != str(record_id)]
                    msg = "已成功刪除該筆學生作答紀錄！"
                elif exam_id and exam_id != "ALL":
                    records = [r for r in records if r.get("examId") != exam_id]
                    msg = f"已成功清空該測驗的所有學生作答紀錄！"
                else:
                    self._set_headers(HTTPStatus.BAD_REQUEST)
                    self.wfile.write(json.dumps({"success": False, "error": "未指定刪除條件"}).encode("utf-8"))
                    return

                deleted_count = initial_count - len(records)
                with open(records_file, "w", encoding="utf-8") as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)

                self._set_headers(HTTPStatus.OK)
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": msg,
                    "deleted": deleted_count,
                    "remaining": len(records)
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(HTTPStatus.BAD_REQUEST)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # 未支援的 API 路徑
        self._set_headers(HTTPStatus.NOT_FOUND)
        self.wfile.write(json.dumps({"error": "找不到此 API 端點"}).encode("utf-8"))

    def do_DELETE(self):
        """處理 DELETE 請求：支援刪除學生作答紀錄"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        if path == "/api/student-records":
            record_id = query.get("id", [None])[0]
            exam_id = query.get("examId", [None])[0]
            delete_all = query.get("all", ["false"])[0].lower() in ("true", "1")

            records_file = os.path.join(DATA_DIR, "student_records.json")
            if not os.path.exists(records_file):
                self._set_headers(HTTPStatus.OK)
                self.wfile.write(json.dumps({"success": True, "message": "目前無任何紀錄", "deleted": 0, "remaining": 0}).encode("utf-8"))
                return

            try:
                with open(records_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
                    if not isinstance(records, list):
                        records = []
            except Exception:
                records = []

            initial_count = len(records)

            if delete_all:
                records = []
                msg = "已清空所有學生作答紀錄！"
            elif record_id:
                records = [r for r in records if str(r.get("id")) != str(record_id) and str(r.get("completedAt")) != str(record_id)]
                msg = "已成功刪除該筆學生作答紀錄！"
            elif exam_id and exam_id != "ALL":
                records = [r for r in records if r.get("examId") != exam_id]
                msg = f"已成功清空該測驗的所有學生作答紀錄！"
            else:
                self._set_headers(HTTPStatus.BAD_REQUEST)
                self.wfile.write(json.dumps({"success": False, "error": "未指定刪除條件"}).encode("utf-8"))
                return

            deleted_count = initial_count - len(records)
            with open(records_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)

            self._set_headers(HTTPStatus.OK)
            self.wfile.write(json.dumps({
                "success": True,
                "message": msg,
                "deleted": deleted_count,
                "remaining": len(records)
            }, ensure_ascii=False).encode("utf-8"))
            return

        self._set_headers(HTTPStatus.NOT_FOUND)
        self.wfile.write(json.dumps({"error": "找不到此 API 端點"}).encode("utf-8"))


def run_server(start_port=8080, max_attempts=20):
    """啟動本機伺服器服務，若連接埠已被佔用則自動遞增尋找可用埠"""
    current_port = start_port
    httpd = None

    for attempt in range(max_attempts):
        try:
            server_address = ("", current_port)
            httpd = http.server.ThreadingHTTPServer(server_address, RPGGameRequestHandler)
            break
        except OSError:
            current_port += 1

    if not httpd:
        print(f"錯誤：無法在 {start_port} 至 {start_port + max_attempts} 範圍內找到可用連接埠！")
        return

    try:
        print("=" * 65)
        print("  《黑金魔法術─永續食物循環系統》本機遊戲伺服器已成功啟動！")
        print(f"  遊戲伺服器網址: http://localhost:{current_port}")
        print(f"  資料儲存目錄  : {DATA_DIR}")
        print("  按 Ctrl+C 可停止伺服器")
        print("=" * 65)
        sys.stdout.flush()
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n伺服器已停止運行。")
        httpd.server_close()
    except Exception as e:
        print(f"伺服器運行時發生錯誤: {e}")


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
