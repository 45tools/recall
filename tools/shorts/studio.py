"""45 Recall 紹介ショートの撮影スタジオ（45 Brain のものを流用）。
本物のアプリ（localhost:8765）を縦長の画面（1080×1920）の中に入れ、時計を止めた状態で1コマずつ進めて撮る。
読み上げ：edge-tts。シーンごとに mp4 を作り、最後につなぐ。
"""
import asyncio, hashlib, json, os, subprocess, math
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(os.path.dirname(HERE), "fonts")
FPS = 30
W, H = 1080, 1920
VOICE = {"ja": ("ja-JP-NanamiNeural", "-5%"), "en": ("en-US-JennyNeural", "-3%"), "zh-Hant": ("zh-TW-HsiaoChenNeural", "-5%")}
APP = "http://localhost:8765/"
STAGE = "http://localhost:8766/stage.html"

FONT_FILES = {
    "fredoka-500": "fontsource-fredoka-5.1.0/package/files/fredoka-latin-500-normal.woff2",
    "fredoka-600": "fontsource-fredoka-5.1.0/package/files/fredoka-latin-600-normal.woff2",
    "fredoka-700": "fontsource-fredoka-5.1.0/package/files/fredoka-latin-700-normal.woff2",
}
for w in (500, 700, 800):
    FONT_FILES[f"mpr-ja-{w}"] = f"fontsource-m-plus-rounded-1c-5.1.0/package/files/m-plus-rounded-1c-japanese-{w}-normal.woff2"
    FONT_FILES[f"mpr-la-{w}"] = f"fontsource-m-plus-rounded-1c-5.1.0/package/files/m-plus-rounded-1c-latin-{w}-normal.woff2"
FONT_CSS = "".join(
    [f"@font-face{{font-family:'Fredoka';font-weight:{w};src:url(https://fonts.local/fredoka-{w})}}" for w in (500, 600, 700)] +
    [f"@font-face{{font-family:'M PLUS Rounded 1c';font-weight:{w};src:url(https://fonts.local/mpr-ja-{w})}}"
     f"@font-face{{font-family:'M PLUS Rounded 1c';font-weight:{w};src:url(https://fonts.local/mpr-la-{w});unicode-range:U+0000-00FF}}" for w in (500, 700, 800)])

INIT = """(()=>{ if(location.port!=="8765") return;
  let s=%d; Math.random=()=>{ s=(s*1103515245+12345)%%2147483648; return s/2147483648; };
  try{ if(!sessionStorage.getItem("_init")){ localStorage.clear(); localStorage.setItem("pr_lang","%s"); sessionStorage.setItem("_init","1"); } }catch(e){}
})();"""


def sh(*a):
    subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return float(out.strip())


async def tts(text, lang):
    voice, rate = VOICE[lang]
    os.makedirs(os.path.join(HERE, "tts"), exist_ok=True)
    p = os.path.join(HERE, "tts", hashlib.md5((voice + rate + text).encode()).hexdigest() + ".mp3")
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        for _ in range(3):
            r = subprocess.run(["edge-tts", "--voice", voice, f"--rate={rate}", "--text", text, "--write-media", p], capture_output=True)
            if r.returncode == 0 and os.path.getsize(p) > 0: break
            await asyncio.sleep(2)
    return p, dur(p)


class Studio:
    def __init__(self, name, lang, color, seed=7):
        self.name, self.lang, self.color, self.seed = name, lang, color, seed
        self.out = os.path.join(HERE, "out", name); os.makedirs(self.out, exist_ok=True)
        self.frame = 0; self.cues = []; self.speech_end = 0; self.scene_files = []; self.proc = None
        self.fx, self.fy = W / 2, H * 0.78

    async def __aenter__(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch()
        self.ctx = await self.browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1,
                                                  locale={"ja": "ja-JP", "en": "en-US", "zh-Hant": "zh-TW"}[self.lang], has_touch=False)
        await self.ctx.route("https://fonts.googleapis.com/**", lambda r: r.fulfill(status=200, content_type="text/css", body=FONT_CSS))
        await self.ctx.route("https://fonts.gstatic.com/**", lambda r: r.abort())
        await self.ctx.route("https://fonts.local/**", lambda r: r.fulfill(status=200, content_type="font/woff2",
                                                                         body=open(os.path.join(FONTS, FONT_FILES[r.request.url.rsplit("/", 1)[1]]), "rb").read()))
        await self.ctx.add_init_script(INIT % (self.seed, self.lang))
        self.page = await self.ctx.new_page()
        await self.page.clock.install(time="2026-11-05T12:00:00+09:00")
        await self.page.clock.pause_at("2026-11-05T12:00:01+09:00")
        await self.page.goto(STAGE + f"?lang={self.lang}&c={self.color.replace('#', '')}")
        await self.page.clock.run_for(800)
        self.app = self.page.frame_locator("#app")
        return self

    async def __aexit__(self, et, ev, tb):
        if et and self.proc:
            self.proc.kill(); self.proc = None
        else:
            await self.end_scene()
        await self.browser.close(); await self.pw.stop()

    # ---- 場面 ----
    async def scene(self, name):
        await self.end_scene()
        path = os.path.join(self.out, f"{len(self.scene_files):02d}_{name}.tmp.mp4")
        self.proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
                                      "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), path], stdin=subprocess.PIPE)
        self.cur = path

    async def end_scene(self):
        if self.proc:
            self.proc.stdin.close(); rc = self.proc.wait(); self.proc = None
            if rc != 0: raise RuntimeError("ffmpeg failed " + self.cur)
            final = self.cur.replace(".tmp.mp4", ".mp4"); os.replace(self.cur, final); self.scene_files.append(final)

    async def tick(self, n=1):
        for _ in range(n):
            await self.page.evaluate(f"window.__f&&__f({self.fx:.1f},{self.fy:.1f})")
            await self.page.clock.run_for(round((self.frame + 1) * 1000 / FPS) - round(self.frame * 1000 / FPS))
            self.proc.stdin.write(await self.page.screenshot(type="jpeg", quality=92))
            self.frame += 1

    async def hold(self, sec):
        await self.tick(max(1, round(sec * FPS)))

    # ---- 文字・読み上げ ----
    async def stage(self, js):
        await self.page.evaluate(js)

    async def say(self, text, caption=None, wait_prev=True):
        if wait_prev: await self.wait_speech()
        spoken = text.replace("数当て", "かずあて") if self.lang == "ja" else text  # 読み方の指定
        p, d = await tts(spoken, self.lang)
        await self.page.evaluate("t=>window.__cap(t)", caption if caption is not None else text)
        self.cues.append((self.frame / FPS, p)); self.speech_end = self.frame + math.ceil((d + 0.25) * FPS)

    async def wait_speech(self, extra=0.0):
        left = self.speech_end - self.frame
        if left > 0: await self.tick(left)
        if extra: await self.hold(extra)

    # ---- 指 ----
    async def box(self, sel, nth=0):
        loc = self.app.locator(sel).nth(nth)
        b = await loc.bounding_box()
        return loc, b

    async def move_to(self, x, y, frames=9):
        x0, y0 = self.fx, self.fy
        for i in range(1, frames + 1):
            k = i / frames; e = k * k * (3 - 2 * k)
            self.fx, self.fy = x0 + (x - x0) * e, y0 + (y - y0) * e
            await self.tick()

    async def tap(self, sel, nth=0, after=0.25, dx=0.5, dy=0.5):
        loc, b = await self.box(sel, nth)
        x, y = b["x"] + b["width"] * dx, b["y"] + b["height"] * dy
        await self.move_to(x, y)
        await self.page.evaluate("window.__press&&__press()")
        await self.page.mouse.click(x, y)
        await self.hold(after)

    async def keys(self, digits, gap=0.18):
        for d in digits:
            await self.tap(f'#dock [data-k="{d}"]', after=gap)

    async def js(self, code):
        return await self.page.frame(name="app").evaluate(code)

    # ---- 仕上げ ----
    def finish(self, bgm=None, bgm_db=-21):
        listf = os.path.join(self.out, "list.txt")
        open(listf, "w").write("".join(f"file '{os.path.basename(f)}'\n" for f in self.scene_files))
        video = os.path.join(self.out, "video.mp4")
        sh("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf, "-c", "copy", video)
        total = dur(video)
        json.dump({"cues": self.cues, "total": total}, open(os.path.join(self.out, "cues.json"), "w"))
        return mix(self.out, bgm, bgm_db)


def mix(out, bgm=None, bgm_db=-21):
    meta = json.load(open(os.path.join(out, "cues.json")))
    cues, total = meta["cues"], meta["total"]
    video = os.path.join(out, "video.mp4")
    args = ["ffmpeg", "-y", "-i", video]
    parts = []
    for i, (t, p) in enumerate(cues):
        args += ["-i", p]; parts.append(f"[{i+1}:a]adelay={int(t*1000)}|{int(t*1000)},aresample=48000[a{i}]")
    n = len(cues); mixin = "".join(f"[a{i}]" for i in range(n))
    filt = ";".join(parts) + f";{mixin}amix=inputs={n}:normalize=0:dropout_transition=0,volume=1.0[v]"
    if bgm:
        args += ["-stream_loop", "-1", "-i", bgm]
        filt += f";[{n+1}:a]volume={bgm_db}dB,atrim=0:{total:.2f},afade=t=in:d=0.6,afade=t=out:st={total-1.8:.2f}:d=1.8,aresample=48000[b];[v][b]amix=inputs=2:normalize=0[m]"
        last = "[m]"
    else:
        last = "[v]"
    final = os.path.join(out, "final.mp4")
    sh(*args, "-filter_complex", filt + f";{last}apad,atrim=0:{total:.2f}[out]", "-map", "0:v", "-map", "[out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.2f}", final)
    return final
