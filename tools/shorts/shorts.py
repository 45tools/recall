"""45 Recall 紹介ショート（3言語）。
準備：リポジトリ直下で python3 -m http.server 8765、このフォルダで python3 -m http.server 8766、python3 demo_images.py
python3 shorts.py ja / en / zh-Hant / all     （BGM=曲.mp3 を付けるとBGM入り）
"""
import asyncio, sys, os, json
from studio import Studio, APP, HERE

DEMO = APP + "tools/shorts/demo/"
NAME = {"ja": "間違えた所を、写真でくり返し復習", "en": "Snap your mistakes. Review on repeat.", "zh-Hant": "把錯題拍下來，反覆複習"}
SUBJ = {"ja": ["数学", "英語", "数学", "理科", "数学"], "en": ["Math", "English", "Math", "Science", "Math"], "zh-Hant": ["數學", "英文", "數學", "自然", "數學"]}
REMIND = {"ja": "体操服と上ばき", "en": "P.E. clothes & shoes", "zh-Hant": "體育服和室內鞋"}
END = {"ja": ("無料・広告なし・インストール不要", ["間違えた所を写真で復習", "持ち物のリマインドにも"]),
       "en": ("Free · No ads · No install", ["Review your mistakes", "Photo reminders, too"]),
       "zh-Hant": ("免費・無廣告・免安裝", ["用照片複習錯題", "也能拍照提醒"])}
L = {
 "ja": ["45 Recall。間違えた問題を、写真でくり返し復習するアプリです。",
        "今日復習するカードと、続けた日数が、ひと目で分かります。",
        "間違えたページを撮ったら、",
        "間違えた所を囲んで、追加するだけ。",
        "1日後、3日後、1週間後。忘れかけたころに、もう一度出てきます。",
        "写真を見て、思い出せたらOK。",
        "今日の復習が終わると、お祝いの画面。",
        "持ち物やプリントも、撮っておけば、決めた時間に知らせます。",
        "45 Recall。無料・広告なしで、ブラウザですぐ使えます。"],
 "en": ["45 Recall. Snap your mistakes and review them on repeat.",
        "See today's cards and your streak at a glance.",
        "Snap the page you got wrong,",
        "box the mistake, and add it.",
        "It comes back after a day, three days, a week — right before you forget.",
        "Look at the photo. Remembered it? Tap OK.",
        "Finish today's review and celebrate.",
        "Snap things to bring or hand in, and get reminded at the time you choose.",
        "45 Recall. Free, no ads, right in your browser."],
 "zh-Hant": ["45 Recall，把錯題拍下來，反覆複習的App。",
        "今天要複習的卡片和連續天數，一眼就看得到。",
        "拍下寫錯的那一頁，",
        "框出錯的地方，加入就好。",
        "一天後、三天後、一週後，在快要忘記的時候再出現一次。",
        "看著照片，想起來了就按OK。",
        "完成今天的複習，還有慶祝畫面。",
        "要帶的東西或要交的作業，拍下來就會在指定的時間提醒你。",
        "45 Recall，免費、無廣告，用瀏覽器馬上就能用。"],
}

SEED = """async ([base, subj, memo]) => {
  const get = async u => await (await fetch(u)).blob();
  const sod = startOfDay(), now = Date.now();
  const plan = [["c1.jpg",0,1],["c2.jpg",0,2],["c3.jpg",0,0],["c4.jpg",1,2],["c5.jpg",3,3]];
  for (let i = 0; i < plan.length; i++) {
    const [f, dd, lv] = plan[i], b = await get(base + f), c = newCard(b, await thumbOf(b), null, "");
    Object.assign(c, {subject: subj[i], due: sod + dd*DAY, level: lv, created: now - (10 - i)*60000, reviews: lv});
    await dbPut(c);
  }
  const rb = await get(base + "remind.jpg"), r = newCard(rb, await thumbOf(rb), null, memo);
  const at = new Date(sod + DAY); at.setHours(7, 0, 0, 0);
  Object.assign(r, {kind: "remind", remindAt: at.getTime(), subject: "", due: 8.64e15}); await dbPut(r);
  const days = []; for (let i = 1; i <= 3; i++) { const d = new Date(sod - i*DAY); days.push(`${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`); }
  localStorage.setItem("pr_days", JSON.stringify(days));
  await reload(); setMode("review");
}"""


async def card(s, html):
    await s.stage(f"__card({json.dumps(html)})")


async def make(lang, bgm=None):
    T = L[lang]
    async with Studio("recall_" + lang, lang, "#14583A", seed=11) as s:
        # 1. タイトル
        await s.scene("title")
        await card(s, f'<div class=chip><i>45</i>Recall</div><img src="{APP}icon-512.png" style="width:330px;height:330px;border-radius:78px;box-shadow:0 20px 50px rgba(0,0,0,.2)"><div class=tag>{NAME[lang]}</div>')
        await s.say(T[0], caption="")
        await s.page.evaluate(f"__app({json.dumps(APP + 'index.html')})")
        await s.page.clock.run_for(1500); await s.page.wait_for_timeout(1500)
        await s.page.frame(name="app").wait_for_selector("#hero", timeout=15000)
        await s.page.frame(name="app").evaluate(SEED, [DEMO, SUBJ[lang], REMIND[lang]])
        await s.page.clock.run_for(600); await s.page.wait_for_timeout(600)
        await s.wait_speech(0.2)
        # 2. ホーム
        await s.scene("home")
        await s.stage(f"__card(''); __title({json.dumps(NAME[lang])}); __finger(true)")
        await s.say(T[1]); await s.hold(0.4)
        await s.move_to(*(await center(s, "#streak")), frames=14)
        await s.wait_speech(0.3)
        # 3. 撮る → 囲む → 追加
        await s.scene("add")
        await s.tap('.tabbar [data-mode="add"]', after=0.3)
        await s.say(T[2])
        x, y = await center(s, ".tShoot")
        await s.move_to(x, y); await s.page.evaluate("window.__press&&__press()"); await s.hold(0.3)
        await s.page.frame(name="app").evaluate("addKind='review'")
        await s.page.frame(name="app").set_input_files("#camFile", os.path.join(HERE, "demo", "page1.jpg"))
        await s.page.wait_for_timeout(1500); await s.page.clock.run_for(300)
        await s.wait_speech(0.1)
        await s.say(T[3])
        await drag_box(s)
        await s.hold(0.4)
        await s.tap("#cropAdd", after=0.6)
        await s.tap("#cropDone", after=0.4)
        await s.page.wait_for_timeout(500)
        await s.wait_speech(0.2)
        # 4. 一覧（間隔）
        await s.scene("list")
        await s.tap('.tabbar [data-mode="list"]', after=0.3)
        await s.say(T[4])
        await s.wait_speech(0.4)
        # 5. 復習
        await s.scene("review")
        await s.tap('.tabbar [data-mode="review"]', after=0.4)
        await s.tap("#startReview", after=0.4)
        await s.say(T[5]); await s.hold(1.2)
        await s.tap("#rvOk", after=0.9)
        await s.tap("#rvOk", after=0.9)
        await s.wait_speech(0.1)
        await s.say(T[6])
        await s.tap("#rvOk", after=0.3)
        await s.hold(2.2)
        await s.wait_speech(0.3)
        await s.tap("#celOk", after=0.4)
        # 6. リマインド
        await s.scene("remind")
        await s.say(T[7]); await s.hold(0.5)
        await s.tap("#rmList .rmItem", after=0.3)
        await s.wait_speech(0.6)
        # 7. おわり
        await s.scene("end")
        await s.stage("__finger(false); __cap('')")
        a, pills = END[lang]
        await card(s, f'<div class=chip><i>45</i>Recall</div><div class=tag>{a}</div><div class=url>45tools.github.io/recall</div>'
                      f'<div class=pills>{"".join(f"<span>{p}</span>" for p in pills)}</div>')
        await s.say(T[8], caption="")
        await s.wait_speech(0.8)
        out = s
    final = out.finish(bgm)
    dst = os.path.join(HERE, "out", f"45Recall_short_{ {'ja': 'JA', 'en': 'EN', 'zh-Hant': 'zhTW'}[lang] }.mp4")
    os.replace(final, dst); print(dst)


async def center(s, sel, nth=0):
    _, b = await s.box(sel, nth)
    return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2


async def drag_box(s):
    """枠を(3)の問題に合わせる動き：指で右下の角を動かすように見せ、枠を少しずつ変える"""
    f = s.page.frame(name="app")
    W, H = await f.evaluate("[crop.img.naturalWidth, crop.img.naturalHeight]")
    x0, y0, w0, h0 = W * .1, H * .35, W * .8, H * .22
    x1, y1, w1, h1 = W * .09, H * .44, W * .82, H * .135
    hb = await f.evaluate("(()=>{const r=document.getElementById('cropBox').getBoundingClientRect();return [r.right,r.bottom]})()")
    fr = s.page.frame_locator("#app").locator("#cropBox")
    b = await fr.bounding_box()
    await s.move_to(b["x"] + b["width"] / 2, b["y"] + 10, frames=10)
    await s.page.evaluate("window.__press&&__press()")
    n = 24
    for i in range(1, n + 1):
        k = i / n; e = k * k * (3 - 2 * k)
        box = dict(x=x0 + (x1 - x0) * e, y=y0 + (y1 - y0) * e, w=w0 + (w1 - w0) * e, h=h0 + (h1 - h0) * e)
        await f.evaluate("b=>{crop.box=b;crop.boxTouched=true;drawBox();}", box)
        nb = await fr.bounding_box()
        s.fx, s.fy = nb["x"] + nb["width"] / 2, nb["y"] + 10
        await s.tick()


if __name__ == "__main__":
    langs = ["ja", "en", "zh-Hant"] if sys.argv[1] == "all" else [sys.argv[1]]
    for lg in langs:
        asyncio.run(make(lg, os.environ.get("BGM")))
