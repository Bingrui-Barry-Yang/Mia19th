#!/usr/bin/env python3
"""Build an encrypted, self-contained interactive letter page."""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import secrets
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
except ImportError as exc:  # pragma: no cover - friendly CLI failure
    raise SystemExit(
        "缺少依赖 cryptography。请先运行：python3 -m pip install -r requirements.txt"
    ) from exc


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "咪呀22.txt"
OUTPUT = ROOT / "index.html"
ITERATIONS = 310_000


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def encrypt_letter(plaintext: str, password: str) -> dict[str, object]:
    salt = secrets.token_bytes(16)
    iv = secrets.token_bytes(12)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS
    )
    key = kdf.derive(password.encode("utf-8"))
    ciphertext = AESGCM(key).encrypt(iv, plaintext.encode("utf-8"), None)
    return {
        "salt": b64(salt),
        "iv": b64(iv),
        "ciphertext": b64(ciphertext),
        "iterations": ITERATIONS,
    }


def render_page(payload: dict[str, object]) -> str:
    payload_json = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    return f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#e5e8ea">
  <meta name="description" content="一封等待被打开的信">
  <title>给咪呀的一封信</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #485058;
      --muted: #7c858d;
      --paper: #f8f9f9;
      --envelope: #f4f6f7;
      --envelope-shadow: #d5dadd;
      --wax: #52799a;
      --wax-dark: #35536d;
      --gold: #c7b991;
      --bg-1: #eef0f1;
      --bg-2: #dfe3e5;
      --ease: cubic-bezier(.22, .8, .28, 1);
    }}

    * {{ box-sizing: border-box; }}
    html {{ min-height: 100%; background: var(--bg-2); }}
    body {{
      min-height: 100%; margin: 0; color: var(--ink);
      font-family: "Songti SC", "STSong", "Noto Serif CJK SC", Georgia, serif;
      background:
        radial-gradient(circle at 18% 12%, rgba(255,255,255,.84), transparent 30rem),
        radial-gradient(circle at 88% 80%, rgba(82,121,154,.08), transparent 28rem),
        linear-gradient(145deg, var(--bg-1), var(--bg-2));
    }}
    body.locked {{ overflow: hidden; }}
    button, input {{ font: inherit; }}
    [hidden] {{ display: none !important; }}

    .auth {{
      position: fixed; inset: 0; z-index: 50; display: grid; place-items: center;
      padding: max(1.25rem, env(safe-area-inset-top)) 1.25rem max(1.25rem, env(safe-area-inset-bottom));
      background:
        radial-gradient(circle at 50% 30%, rgba(255,255,255,.88), transparent 24rem),
        linear-gradient(145deg, #f2f4f5, #dfe3e5);
      transition: opacity .55s ease, visibility .55s ease;
    }}
    .auth.is-leaving {{ opacity: 0; visibility: hidden; }}
    .auth-card {{
      width: min(92vw, 25rem); padding: clamp(1.7rem, 5vw, 2.6rem);
      text-align: center; border: 1px solid rgba(82,121,154,.13); border-radius: 1.4rem;
      background: rgba(248,249,249,.88); backdrop-filter: blur(12px);
      box-shadow: 0 1.6rem 5rem rgba(56,67,76,.13);
    }}
    .auth-mark {{
      width: 3.6rem; height: 3.6rem; margin: 0 auto 1rem; display: grid; place-items: center;
      border-radius: 50%; color: var(--gold); background: var(--wax);
      box-shadow: inset .12rem .14rem .2rem rgba(255,255,255,.2), 0 .45rem 1rem rgba(53,83,109,.18);
    }}
    .auth-mark svg {{ width: 2.2rem; height: 2.2rem; }}
    .auth h1 {{ margin: 0; font-size: clamp(1.2rem, 5vw, 1.65rem); font-weight: 500; line-height: 1.4; letter-spacing: .04em; }}
    .auth p {{ margin: .7rem 0 1.45rem; color: var(--muted); font-size: .93rem; line-height: 1.65; }}
    .headphone-note {{
      margin: 1.15rem 0 .65rem !important; color: var(--muted) !important;
      font-size: .78rem !important; line-height: 1.4 !important; letter-spacing: .09em;
    }}
    .password-wrap {{ position: relative; }}
    .password-wrap input {{
      width: 100%; height: 3.25rem; padding: 0 3.1rem 0 1rem; color: var(--ink);
      border: 1px solid #d8c9c0; border-radius: .85rem; outline: none; background: rgba(255,255,255,.78);
      transition: border-color .2s, box-shadow .2s;
    }}
    .password-wrap input:focus {{ border-color: var(--wax); box-shadow: 0 0 0 .22rem rgba(82,121,154,.12); }}
    .peek {{
      position: absolute; right: .45rem; top: .42rem; width: 2.4rem; height: 2.4rem;
      border: 0; border-radius: .6rem; color: var(--muted); background: transparent; cursor: pointer;
    }}
    .unlock {{
      width: 100%; height: 3.2rem; margin-top: .8rem; border: 0; border-radius: .85rem;
      color: #f8fbfd; background: linear-gradient(145deg, #6b90ae, var(--wax)); cursor: pointer;
      letter-spacing: .14em; box-shadow: 0 .55rem 1.2rem rgba(53,83,109,.17);
      transition: transform .2s, box-shadow .2s, opacity .2s;
    }}
    .unlock:hover {{ transform: translateY(-1px); box-shadow: 0 .7rem 1.5rem rgba(53,83,109,.22); }}
    .unlock:disabled {{ cursor: wait; opacity: .66; transform: none; }}
    .status {{ min-height: 1.35rem; margin: .75rem 0 0 !important; color: #58728a !important; font-size: .86rem !important; }}
    .auth-card.shake {{ animation: shake .38s ease; }}
    @keyframes shake {{ 25% {{ transform: translateX(-.4rem); }} 50% {{ transform: translateX(.35rem); }} 75% {{ transform: translateX(-.18rem); }} }}

    .experience {{ opacity: 0; transition: opacity .65s ease; }}
    .experience.is-ready {{ opacity: 1; }}
    .scene {{
      position: relative; min-height: 100svh; display: grid; place-items: center; overflow: hidden;
      padding: max(1.25rem, env(safe-area-inset-top)) 1rem max(2rem, env(safe-area-inset-bottom));
    }}
    .scene::before {{
      content: ""; position: fixed; inset: 0; pointer-events: none; opacity: .25;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.08'/%3E%3C/svg%3E");
    }}
    .envelope-wrap {{
      position: relative; width: min(84vw, 35rem); aspect-ratio: 1.58;
      filter: drop-shadow(0 1.7rem 1.6rem rgba(56,67,76,.18));
      perspective: 1200px;
    }}
    .envelope-back {{
      position: absolute; inset: 0; z-index: 1; border-radius: .35rem;
      background: linear-gradient(150deg, #f8f9f9, #e8ecee);
    }}
    .flap {{
      position: absolute; z-index: 4; inset: 0 0 auto; height: 57%; transform-origin: 50% 0;
      clip-path: polygon(0 0, 100% 0, 50% 100%);
      background: linear-gradient(170deg, #f8f9f9 10%, #e5e9eb 100%);
      transition: transform 1.05s var(--ease), z-index 0s .54s;
      backface-visibility: hidden;
    }}
    .front {{ position: absolute; inset: 0; z-index: 3; pointer-events: none; border-radius: .35rem; overflow: hidden; }}
    .front::before, .front::after {{ content: ""; position: absolute; inset: 0; }}
    .front::before {{
      background: linear-gradient(32deg, #e7ebed, #f8f9f9 72%);
      clip-path: polygon(0 0, 52% 55%, 100% 0, 100% 100%, 0 100%);
    }}
    .front::after {{
      background: linear-gradient(148deg, transparent 49.6%, rgba(138,119,112,.12) 50%, transparent 50.5%);
      opacity: .8;
    }}
    .paper {{
      position: absolute; z-index: 2; left: 6%; top: 4%; width: 88%; max-height: 88%; overflow: hidden;
      padding: clamp(1.45rem, 5vw, 3.6rem); border: 1px solid rgba(120,97,82,.12); border-radius: .2rem;
      background:
        linear-gradient(rgba(120,97,82,.035) 1px, transparent 1px) 0 0 / 100% 2rem,
        var(--paper);
      box-shadow: 0 .5rem 1.4rem rgba(60,40,34,.12);
      transform: translateY(16%) scale(.96);
      transform-origin: 50% 0;
    }}
    .letter-text {{
      white-space: pre-wrap; overflow-wrap: anywhere; font-size: clamp(1rem, 2.4vw, 1.17rem);
      line-height: 2; letter-spacing: .035em; opacity: 0; transition: opacity .7s 1.15s ease;
    }}
    .seal {{
      position: absolute; z-index: 7; left: 50%; top: 49%; width: clamp(4.4rem, 15vw, 6.1rem); aspect-ratio: 1;
      display: grid; place-items: center; padding: 0; transform: translate(-50%, -50%) rotate(-4deg);
      border: 0; border-radius: 46% 54% 49% 51% / 52% 45% 55% 48%; color: var(--gold); cursor: pointer;
      background:
        radial-gradient(circle at 34% 28%, rgba(255,255,255,.24), transparent 17%),
        radial-gradient(circle at 55% 60%, #668baa, var(--wax) 58%, var(--wax-dark));
      box-shadow: inset .22rem .28rem .35rem rgba(255,255,255,.16), inset -.25rem -.3rem .35rem rgba(28,54,75,.25), 0 .45rem .75rem rgba(38,55,68,.25);
      transition: transform .28s ease, box-shadow .28s ease, opacity .38s .12s ease;
      -webkit-tap-highlight-color: transparent;
    }}
    .seal::before {{ content: ""; position: absolute; inset: 9%; border: 1px solid rgba(215,183,117,.52); border-radius: 50%; }}
    .seal:hover {{ transform: translate(-50%, -52%) rotate(1deg) scale(1.04); box-shadow: inset .22rem .28rem .35rem rgba(255,255,255,.16), inset -.25rem -.3rem .35rem rgba(28,54,75,.25), 0 .65rem 1rem rgba(38,55,68,.3); }}
    .seal:focus-visible, button:focus-visible {{ outline: .2rem solid var(--gold); outline-offset: .25rem; }}
    .seal svg {{ width: 72%; height: 72%; filter: drop-shadow(0 .08rem .04rem rgba(45,18,12,.35)); }}
    .hint {{
      position: absolute; top: calc(100% + 1.65rem); left: 50%; transform: translateX(-50%);
      margin: 0; color: var(--muted); font-size: .88rem; letter-spacing: .12em; white-space: nowrap;
      animation: breathe 2.5s ease-in-out infinite;
    }}
    .music-toggle {{
      position: fixed; z-index: 20; top: max(1rem, env(safe-area-inset-top)); right: max(1rem, env(safe-area-inset-right));
      width: 2.8rem; height: 2.8rem; border: 1px solid rgba(82,121,154,.26); border-radius: 50%;
      color: #f8fbfd; background: rgba(82,121,154,.88); cursor: pointer; backdrop-filter: blur(8px);
      box-shadow: 0 .45rem 1.2rem rgba(38,55,68,.18); transition: transform .2s, opacity .2s;
    }}
    .music-toggle:hover {{ transform: translateY(-1px) scale(1.03); }}
    .music-toggle.needs-tap {{ animation: music-pulse 1.5s ease-in-out infinite; }}
    @keyframes music-pulse {{ 50% {{ transform: scale(1.1); box-shadow: 0 0 0 .45rem rgba(82,121,154,.12); }} }}
    @keyframes breathe {{ 50% {{ opacity: .45; transform: translate(-50%, .16rem); }} }}

    .scene.is-opening {{ overflow: visible; align-items: start; padding-top: clamp(2rem, 8vh, 5rem); }}
    .scene.is-opening .envelope-wrap {{ animation: settle 1.2s var(--ease) forwards; }}
    .scene.is-opening .seal {{ pointer-events: none; transform: translate(-50%, -64%) rotate(13deg) scale(.72); opacity: 0; }}
    .scene.is-opening .flap {{ transform: rotateX(180deg); z-index: 1; }}
    .scene.is-opening .paper {{ animation: paper-rise 1.45s .62s var(--ease) forwards; }}
    .scene.is-opening .letter-text {{ opacity: 1; }}
    .scene.is-opening .hint {{ opacity: 0; animation: none; }}
    @keyframes settle {{ to {{ transform: translateY(1.2rem); filter: drop-shadow(0 1rem 1.2rem rgba(70,45,38,.13)); }} }}
    @keyframes paper-rise {{
      0% {{ z-index: 2; width: 88%; left: 6%; max-height: 88%; transform: translateY(16%) scale(.96); }}
      46% {{ z-index: 2; width: 88%; left: 6%; max-height: 88%; transform: translateY(-62%) scale(.98); }}
      47% {{ z-index: 8; }}
      100% {{ z-index: 8; left: 50%; width: min(90vw, 46rem); max-height: none; transform: translate(-50%, -2.2rem) scale(1); }}
    }}

    @media (max-width: 520px) {{
      .scene {{ padding-inline: .6rem; }}
      .envelope-wrap {{ width: 91vw; }}
      .paper {{ padding: 1.55rem 1.25rem 2.5rem; }}
      .letter-text {{ line-height: 1.9; }}
      .hint {{ top: calc(100% + 1.2rem); }}
    }}
    @media (max-height: 500px) and (orientation: landscape) {{
      .envelope-wrap {{ width: min(58vw, 28rem); }}
      .hint {{ top: 50%; left: calc(100% + 1.5rem); transform: translateY(-50%); white-space: normal; width: 7rem; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{ animation-duration: .01ms !important; animation-delay: 0s !important; transition-duration: .01ms !important; scroll-behavior: auto !important; }}
    }}
  </style>
</head>
<body class="locked">
  <section class="auth" id="auth" aria-labelledby="auth-title">
    <form class="auth-card" id="auth-form" novalidate>
      <div class="auth-mark" aria-hidden="true">
        <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3">
          <path d="M50 45C36 21 13 14 13 32c0 13 16 22 33 20M50 45C64 21 87 14 87 32c0 13-16 22-33 20M48 51C31 49 18 58 21 69c4 14 21 5 29-13M52 51c17-2 30 7 27 18-4 14-21 5-29-13M50 42v27M45 72l5-5 5 5"/>
        </svg>
      </div>
      <h1 id="auth-title">Happy 19th Birthday to Mia</h1>
      <p class="headphone-note">戴上耳机食用更佳</p>
      <div class="password-wrap">
        <label for="password" hidden>密码</label>
        <input id="password" name="password" type="password" autocomplete="current-password" placeholder="请输入密码" required autofocus>
        <button class="peek" id="peek" type="button" aria-label="显示密码" aria-pressed="false">◉</button>
      </div>
      <button class="unlock" id="unlock" type="submit">打开来信</button>
      <p class="status" id="status" role="alert" aria-live="polite"></p>
    </form>
  </section>

  <main class="experience" id="experience" hidden>
    <section class="scene" id="scene" aria-label="一封待打开的信">
      <div class="envelope-wrap">
        <div class="envelope-back" aria-hidden="true"></div>
        <article class="paper" id="paper" aria-label="信纸" tabindex="-1">
          <div class="letter-text" id="letter-text"></div>
        </article>
        <div class="flap" aria-hidden="true"></div>
        <div class="front" aria-hidden="true"></div>
        <button class="seal" id="seal" type="button" aria-label="点击蝴蝶火漆印章打开信封">
          <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true">
            <path d="M50 45C36 21 13 14 13 32c0 13 16 22 33 20M50 45C64 21 87 14 87 32c0 13-16 22-33 20M48 51C31 49 18 58 21 69c4 14 21 5 29-13M52 51c17-2 30 7 27 18-4 14-21 5-29-13M50 42v27M45 72l5-5 5 5"/>
          </svg>
        </button>
        <p class="hint" id="hint">轻触蝴蝶火漆印</p>
      </div>
    </section>
  </main>

  <audio id="bgm" src="keshi-LIMBO.mp3" preload="auto" loop></audio>
  <button class="music-toggle" id="music-toggle" type="button" aria-label="播放背景音乐" hidden>♪</button>

  <script>
    'use strict';
    const ENCRYPTED_LETTER = {payload_json};
    const $ = (selector) => document.querySelector(selector);
    const auth = $('#auth');
    const authForm = $('#auth-form');
    const passwordInput = $('#password');
    const unlockButton = $('#unlock');
    const status = $('#status');
    const experience = $('#experience');
    const scene = $('#scene');
    const seal = $('#seal');
    const bgm = $('#bgm');
    const musicToggle = $('#music-toggle');
    bgm.volume = 0.58;
    let opening = false;

    function syncMusicButton() {{
      musicToggle.textContent = bgm.paused ? '♪' : 'Ⅱ';
      musicToggle.setAttribute('aria-label', bgm.paused ? '播放背景音乐' : '暂停背景音乐');
      if (!bgm.paused) musicToggle.classList.remove('needs-tap');
    }}

    async function startMusic() {{
      musicToggle.hidden = false;
      try {{
        await bgm.play();
      }} catch (_) {{
        musicToggle.classList.add('needs-tap');
      }}
      syncMusicButton();
    }}

    musicToggle.addEventListener('click', async () => {{
      if (bgm.paused) {{
        await startMusic();
      }} else {{
        bgm.pause();
        syncMusicButton();
      }}
    }});
    bgm.addEventListener('play', syncMusicButton);
    bgm.addEventListener('pause', syncMusicButton);

    const fromBase64 = (value) => Uint8Array.from(atob(value), char => char.charCodeAt(0));

    async function decryptLetter(password) {{
      const material = await crypto.subtle.importKey(
        'raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey']
      );
      const key = await crypto.subtle.deriveKey(
        {{ name: 'PBKDF2', salt: fromBase64(ENCRYPTED_LETTER.salt), iterations: ENCRYPTED_LETTER.iterations, hash: 'SHA-256' }},
        material, {{ name: 'AES-GCM', length: 256 }}, false, ['decrypt']
      );
      const plaintext = await crypto.subtle.decrypt(
        {{ name: 'AES-GCM', iv: fromBase64(ENCRYPTED_LETTER.iv) }},
        key, fromBase64(ENCRYPTED_LETTER.ciphertext)
      );
      return new TextDecoder('utf-8', {{ fatal: true }}).decode(plaintext);
    }}

    authForm.addEventListener('submit', async (event) => {{
      event.preventDefault();
      const password = passwordInput.value;
      if (!password) {{ status.textContent = '请先输入密码。'; passwordInput.focus(); return; }}
      unlockButton.disabled = true;
      unlockButton.textContent = '正在解开…';
      status.textContent = '';
      try {{
        const letter = await decryptLetter(password);
        $('#letter-text').textContent = letter;
        passwordInput.value = '';
        experience.hidden = false;
        requestAnimationFrame(() => experience.classList.add('is-ready'));
        auth.classList.add('is-leaving');
        document.body.classList.remove('locked');
        setTimeout(() => {{ auth.hidden = true; seal.focus(); }}, 580);
      }} catch (_) {{
        status.textContent = '密码不对，再试一次吧。';
        authForm.classList.remove('shake');
        void authForm.offsetWidth;
        authForm.classList.add('shake');
        passwordInput.select();
      }} finally {{
        unlockButton.disabled = false;
        unlockButton.textContent = '打开来信';
      }}
    }});

    $('#peek').addEventListener('click', (event) => {{
      const showing = passwordInput.type === 'text';
      passwordInput.type = showing ? 'password' : 'text';
      event.currentTarget.setAttribute('aria-pressed', String(!showing));
      event.currentTarget.setAttribute('aria-label', showing ? '显示密码' : '隐藏密码');
      passwordInput.focus();
    }});

    seal.addEventListener('click', () => {{
      if (opening) return;
      opening = true;
      startMusic();
      scene.classList.add('is-opening');
      seal.setAttribute('aria-expanded', 'true');
      $('#hint').setAttribute('aria-hidden', 'true');
      setTimeout(() => $('#paper').focus({{ preventScroll: true }}), 1700);
    }});

    window.addEventListener('pageshow', () => {{
      passwordInput.value = '';
      unlockButton.disabled = false;
    }});
  </script>
</body>
</html>
'''


def read_password(cli_password: str | None) -> str:
    if cli_password is not None:
        password = cli_password
    else:
        password = getpass.getpass("请输入新的访问密码：")
        confirmation = getpass.getpass("请再输入一次：")
        if password != confirmation:
            raise SystemExit("两次输入的密码不一致。")
    if not password.strip():
        raise SystemExit("密码不能为空。")
    return password


def main() -> None:
    parser = argparse.ArgumentParser(description="生成加密的互动信封页面")
    parser.add_argument(
        "--password",
        help="非交互构建用密码（会出现在命令记录中，日常不建议使用）",
    )
    args = parser.parse_args()

    if not SOURCE.exists():
        raise SystemExit(f"找不到信件文件：{SOURCE.name}")
    plaintext = SOURCE.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not plaintext.strip():
        raise SystemExit("信件内容为空。")

    password = read_password(args.password)
    OUTPUT.write_text(render_page(encrypt_letter(plaintext, password)), encoding="utf-8")
    print(f"已生成：{OUTPUT}")
    print("正文已加密，请妥善保存密码。")


if __name__ == "__main__":
    main()
