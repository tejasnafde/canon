"""Live web QA with Playwright against the deployed site.

Run:  /tmp/pwvenv/bin/python qa/e2e/run.py            (no Gemini)
      QA_GEMINI=1 /tmp/pwvenv/bin/python qa/e2e/run.py  (adds Ask and Agent check: about 2 generate calls)
Prints one PASS/FAIL line per case and exits 1 on any failure. Screenshots go to /tmp/canon-qa/.
"""
import os
import sys
import uuid

from playwright.sync_api import sync_playwright

BASE = os.environ.get("QA_BASE", "https://canon.tn07.dev").rstrip("/")
CHROME = "/Applications/Chromium.app/Contents/MacOS/Chromium"
OUT = "/tmp/canon-qa"
ROUTES = ["/", "/new-hire", "/catch-up", "/agent", "/paste", "/ask", "/decisions", "/org", "/benchmark"]
WS = f"v-qa-{uuid.uuid4().hex[:12]}"
results: list[tuple[str, bool, str]] = []


def case(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}"[:300], flush=True)


def watch(page):
    """Collect console errors, page errors and failed API calls for one page."""
    bad: list[str] = []
    page.on("pageerror", lambda e: bad.append(f"pageerror: {e}"))
    page.on("console", lambda m: bad.append(f"console: {m.text}") if m.type == "error" else None)
    page.on("response", lambda r: bad.append(f"{r.status} {r.url}")
            if r.status >= 400 and ("/api/" in r.url or "/mcp" in r.url) else None)
    return bad


def ready(page):
    page.wait_for_selector("main, h1", timeout=30_000)
    page.wait_for_load_state("networkidle", timeout=30_000)


def overflow(page) -> int:
    return page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME)
        for label, vp in (("desktop", {"width": 1440, "height": 900}), ("mobile", {"width": 390, "height": 844})):
            ctx = browser.new_context(viewport=vp)
            ctx.add_init_script(f"localStorage.setItem('canon-ws', '{WS}')")
            for route in ROUTES:
                page = ctx.new_page()
                bad = watch(page)
                try:
                    page.goto(BASE + route, wait_until="domcontentloaded")
                    ready(page)
                    page.wait_for_timeout(500)
                    text = page.inner_text("body")
                    crashed = "Something went wrong" in text or "Unexpected response" in text
                    over = overflow(page)
                    page.screenshot(path=f"{OUT}/{label}{route.replace('/', '_') or '_home'}.png")
                    case(f"{label} {route} renders", not crashed and not bad, "; ".join(bad[:3]))
                    if label == "mobile":
                        case(f"mobile {route} no horizontal scroll", over <= 1, f"overflow {over}px")
                except Exception as e:
                    case(f"{label} {route} renders", False, f"{type(e).__name__}: {e}")
                page.close()
            ctx.close()

        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        ctx.add_init_script(f"localStorage.setItem('canon-ws', '{WS}')")
        page = ctx.new_page()

        page.goto(BASE + "/no-such-page-qa")
        ready(page)
        case("unknown route shows not-found page", "no page at this address" in page.inner_text("main").lower())

        page.goto(BASE + "/decisions/no-such-decision-qa")
        page.wait_for_timeout(4000)
        body = page.inner_text("body").lower()
        case("unknown decision id shows a clear message", "did not load" in body and "not on record" in body,
             body[:120].replace("\n", " "))

        # keyboard only: Tab reaches a visible focus ring on a link or button
        page.goto(BASE + "/")
        ready(page)
        tags = []
        for _ in range(6):
            page.keyboard.press("Tab")
            tags.append(page.evaluate("document.activeElement && document.activeElement.tagName"))
        case("keyboard Tab moves focus to links/buttons", any(t in ("A", "BUTTON", "INPUT") for t in tags), str(tags))
        outline = page.evaluate("""() => { const s = getComputedStyle(document.activeElement);
            return s.outlineStyle !== 'none' || s.boxShadow !== 'none' }""")
        case("focused element has a visible focus style", outline)

        # back / forward
        page.goto(BASE + "/decisions")
        ready(page)
        page.goto(BASE + "/org")
        ready(page)
        page.go_back()
        page.wait_for_timeout(1000)
        b1 = page.url.endswith("/decisions")
        page.go_forward()
        page.wait_for_timeout(1000)
        case("back and forward keep the right page", b1 and page.url.endswith("/org"), page.url)

        # decision page from the list
        page.goto(BASE + "/decisions")
        ready(page)
        link = page.locator("a[href^='/decisions/']").first
        if link.count():
            link.click()
            page.wait_for_timeout(3000)
            case("decision detail opens from the list", "/decisions/" in page.url
                 and "went wrong" not in page.inner_text("body"), page.url)
        else:
            case("decision detail opens from the list", False, "no decision links")

        # Ask: empty input cannot submit
        page.goto(BASE + "/ask")
        ready(page)
        page.fill("input[aria-label='Your question']", "   ")
        case("ask: blank question cannot be submitted", page.locator("form.askrow button[type=submit]").is_disabled())

        # slow network: the Ask page still renders under a 400 ms API delay
        slow = ctx.new_page()
        slow.route("**/api/**", lambda r: (slow.wait_for_timeout(400), r.continue_()))
        try:
            slow.goto(BASE + "/decisions")
            ready(slow)
            case("decisions page renders on a slow network", "went wrong" not in slow.inner_text("body"))
        except Exception as e:
            case("decisions page renders on a slow network", False, str(e)[:120])
        slow.close()

        if os.environ.get("QA_GEMINI") == "1":
            calls = []
            hero = "Why do we not deploy on Fridays?"
            page.on("request", lambda r: calls.append(r.url)
                    if r.method == "POST" and "/api/ask" in r.url and hero in (r.post_data or "") else None)
            page.goto(BASE + "/ask")
            ready(page)
            page.fill("input[aria-label='Your question']", hero)
            page.locator("form.askrow button[type=submit]").click()
            page.locator("form.askrow button[type=submit]").click(force=True, timeout=1000, no_wait_after=True)
            try:
                page.wait_for_selector(".answer >> text=/Answered in/", timeout=60_000)
                case("ask: hero question answers with citations", "I do not know" not in page.inner_text(".answer"))
            except Exception as e:
                case("ask: hero question answers with citations", False, str(e)[:120])
            case("ask: double click sends one request", len(calls) <= 1, f"{len(calls)} POSTs")
            page.screenshot(path=f"{OUT}/ask_answer.png")

            page.goto(BASE + "/agent")
            ready(page)
            posts = []
            page.on("request", lambda r: posts.append(r.url) if r.method == "POST" and "/api/check" in r.url else None)
            page.fill("textarea[aria-label='An action an agent wants to take']",
                      "Schedule an automatic production deploy every Friday at 17:00")
            sub = page.locator("form button[type=submit]").first
            sub.click()
            sub.click(force=True, timeout=1000, no_wait_after=True)
            page.wait_for_timeout(15_000)
            txt = page.inner_text("main").lower()
            case("agent: Friday deploy is blocked", "block" in txt)
            case("agent: double submit sends one check", len(posts) <= 1, f"{len(posts)} POSTs")
            page.screenshot(path=f"{OUT}/agent_check.png")

        page.request.post(BASE + "/api/workspace/reset", headers={"X-Canon-Workspace": WS})
        browser.close()
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
