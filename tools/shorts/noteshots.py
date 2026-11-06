"""note記事用のスクリーンショットと見出し画像 → note-img/
準備は shorts.py と同じ（8765 でアプリ、demo_images.py）。python3 noteshots.py
"""
import asyncio, os, base64
from playwright.async_api import async_playwright
from studio import FONT_CSS, FONT_FILES, FONTS, APP, HERE
from shorts import SEED, DEMO, SUBJ, REMIND

OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "note-img"); os.makedirs(OUT, exist_ok=True)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 760}, device_scale_factor=2, locale="ja-JP")
        await ctx.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=FONT_CSS))
        await ctx.route("https://fonts.local/**", lambda r: r.fulfill(status=200, content_type="font/woff2", body=open(os.path.join(FONTS, FONT_FILES[r.request.url.rsplit("/", 1)[1]]), "rb").read()))
        pg = await ctx.new_page()
        await pg.clock.install(time="2026-11-07T19:00:00+09:00")
        await pg.goto(APP + "index.html"); await pg.evaluate("localStorage.setItem('pr_lang','ja')"); await pg.reload(); await pg.wait_for_timeout(800)
        await pg.evaluate(SEED, [DEMO, SUBJ["ja"], REMIND["ja"]]); await pg.wait_for_timeout(700)
        shot = lambda n: pg.screenshot(path=os.path.join(OUT, n))
        await shot("01_home.png")
        await pg.click('.tabbar [data-mode="add"]'); await pg.wait_for_timeout(300); await shot("02_add.png")
        await pg.evaluate("addKind='review'"); await pg.set_input_files("#camFile", os.path.join(HERE, "demo", "page1.jpg")); await pg.wait_for_timeout(1500)
        await pg.evaluate("(()=>{const W=crop.img.naturalWidth,H=crop.img.naturalHeight;crop.box={x:W*.09,y:H*.44,w:W*.82,h:H*.135};crop.boxTouched=true;drawBox();renderQ&&renderQ();})()")
        await pg.wait_for_timeout(500); await shot("03_crop.png")
        await pg.click("#cropAdd"); await pg.wait_for_timeout(600); await pg.click("#cropDone"); await pg.wait_for_timeout(600)
        await pg.click('.tabbar [data-mode="list"]'); await pg.wait_for_timeout(400); await shot("04_list.png")
        await pg.click('.tabbar [data-mode="review"]'); await pg.wait_for_timeout(300)
        await pg.click("#startReview"); await pg.wait_for_timeout(600); await shot("05_review.png")
        for _ in range(3): await pg.click("#rvOk"); await pg.wait_for_timeout(500)
        await pg.wait_for_timeout(2500); await shot("06_celebrate.png"); await pg.click("#celOk"); await pg.wait_for_timeout(400)
        await pg.click("#rmList .rmItem"); await pg.wait_for_timeout(500); await shot("07_remind.png")
        await pg.click("#rmSheet [data-close]"); await pg.wait_for_timeout(300)
        await pg.click("#heroBell"); await pg.wait_for_timeout(500); await shot("08_notify.png")
        await pg.keyboard.press("Escape"); await pg.reload(); await pg.wait_for_timeout(800)
        await pg.evaluate("addKind='remind'"); await pg.set_input_files("#camFile", os.path.join(HERE, "demo", "remind.jpg")); await pg.wait_for_timeout(1500)
        await pg.fill("#cropMemo", "体操服と上ばき"); await shot("09_crop_remind.png")
        home = base64.b64encode(open(os.path.join(OUT, "01_home.png"), "rb").read()).decode()
        icon = base64.b64encode(open(os.path.join(os.path.dirname(os.path.dirname(HERE)), "icon-512.png"), "rb").read()).decode()
        hp = await (await b.new_context(viewport={"width": 1280, "height": 670}, device_scale_factor=2)).new_page()
        await hp.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=FONT_CSS))
        await hp.route("https://fonts.local/**", lambda r: r.fulfill(status=200, content_type="font/woff2", body=open(os.path.join(FONTS, FONT_FILES[r.request.url.rsplit("/", 1)[1]]), "rb").read()))
        await hp.set_content(f'''<html><head><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=x"><style>
body{{margin:0;width:1280px;height:670px;background:#EEF0F3;font-family:"M PLUS Rounded 1c",sans-serif;color:#111418;display:flex;align-items:center;gap:50px;padding:0 80px;box-sizing:border-box;overflow:hidden}}
.l{{flex:1}} .chip{{display:inline-flex;align-items:center;gap:16px;font:700 56px Fredoka,sans-serif}} .chip img{{width:84px;height:84px;border-radius:22px}}
h1{{font-size:64px;font-weight:800;line-height:1.3;margin:26px 0 20px}} h1 b{{color:#14583A}}
p{{margin:0;font-size:30px;font-weight:700;color:#5F6670;line-height:1.6}} p b{{color:#FF7A3D}}
.ph{{width:380px;height:740px;margin-top:130px;border-radius:44px;overflow:hidden;box-shadow:0 0 0 10px #fff,0 30px 60px rgba(0,0,0,.18)}} .ph img{{width:100%}}
</style></head><body><div class=l><div class=chip><img src="data:image/png;base64,{icon}">45 Recall</div>
<h1>間違えた所を、<br><b>写真でくり返し復習。</b></h1><p>撮って囲むだけ。忘れかけたころに、もう一度。<br><b>無料・広告なし・インストール不要</b></p></div>
<div class=ph><img src="data:image/png;base64,{home}"></div></body></html>''')
        await hp.wait_for_timeout(800); await hp.screenshot(path=os.path.join(OUT, "00_header.png"))
        await b.close()
    print(sorted(os.listdir(OUT)))

asyncio.run(main())
