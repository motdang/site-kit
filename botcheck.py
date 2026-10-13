#!/usr/bin/env python3
"""botcheck.py — what each kind of visitor gets from a site, from here and from a cloud network.

    python3 botcheck.py https://motdang.net/ https://wichaa.net/
    python3 botcheck.py --json https://motdang.net/     # one JSON list, for the nightly run (voight-kampff)

Fetches every URL as ~25 visitors (people, link-card fetchers, search, AI, SEO, tools),
once from this machine and once from motdang-server (Hetzner, a cloud network), and
prints status, redirect target and whether og:image is present. A row that differs
between the two columns is a decision made by network, not by who is asking.
"""

import sys, re, urllib.request, urllib.error, ssl, json
CH='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
SECF={'Sec-Fetch-Mode':'navigate','Sec-Fetch-Site':'none','Sec-Fetch-Dest':'document','Accept':'text/html'}
V=[
 ('person: Chrome',CH,SECF),
 ('person: iPhone Safari','Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1',{}),
 ('person: LINE in-app','Mozilla/5.0 (Linux; Android 14; V2312) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36 Line/15.12.1',SECF),
 ('card: Bluesky Cardyb','Mozilla/5.0 (compatible; Bluesky Cardyb/1.1; +mailto:support@bsky.app) Chrome/91.0.4472.114',{}),
 ('card: Bluesky bare Chrome',CH,{}),
 ('card: Mastodon','http.rb/5.2.0 (Mastodon/4.3.2; +https://mastodon.social/) Bot',{}),
 ('card: Facebook','facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',{}),
 ('card: iMessage','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.4 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.4 facebookexternalhit/1.1 Facebot Twitterbot/1.0',{}),
 ('card: LINE','facebookexternalhit/1.1;line-poker/1.0',{}),
 ('card: X','Twitterbot/1.0',{}),
 ('card: Discord','Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)',{}),
 ('card: Telegram','TelegramBot (like TwitterBot)',{}),
 ('card: Slack','Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)',{}),
 ('card: LinkedIn','LinkedInBot/1.0 (compatible; Mozilla/5.0; Apache-HttpClient +http://www.linkedin.com)',{}),
 ('card: WhatsApp','WhatsApp/2.23.20.0',{}),
 ('card: Embedly','Mozilla/5.0 (compatible; Embedly/0.2; +http://support.embed.ly/)',{}),
 ('card: Iframely','Iframely/1.3.1 (+https://iframely.com/docs/about)',{}),
 ('search: Googlebot','Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',{}),
 ('search: bingbot','Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',{}),
 ('ai: GPTBot','Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)',{}),
 ('ai: ClaudeBot','Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)',{}),
 ('ai: Claude-User','Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude-User/1.0; +Claude-User@anthropic.com)',{}),
 ('ai: ChatGPT-User','Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot',{}),
 ('ai: meta-externalagent','meta-externalagent/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)',{}),
 ('seo: AhrefsBot','Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)',{}),
 ('tool: curl','curl/8.7.1',{}),
]
class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**k): return None
op=urllib.request.build_opener(NoRedir)
out=[]
for url in ([u for u in sys.argv[2:]] if sys.argv[1:2] == ['--one'] else []):
  for name,ua,h in V:
    req=urllib.request.Request(url,headers={'User-Agent':ua,**h})
    try:
        r=op.open(req,timeout=25); code=r.status; loc=''; body=r.read(300000).decode('utf8','replace')
    except urllib.error.HTTPError as e:
        code=e.code; loc=e.headers.get('location',''); body=e.read(3000).decode('utf8','replace')
    except Exception as e:
        code='ERR'; loc=str(e)[:60]; body=''
    og=bool(re.search(r'property=["\']og:image["\']',body))
    out.append(dict(url=url,who=name,code=code,loc=loc,og=og))
if sys.argv[1:2] == ['--one']:
    print(json.dumps(out))


if __name__ == "__main__" and sys.argv[1:2] != ["--one"]:
    import subprocess
    as_json = "--json" in sys.argv[1:]
    urls = [a for a in sys.argv[1:] if a != "--json"]
    here = subprocess.run([sys.executable, __file__, "--one", *urls], capture_output=True, text=True).stdout
    try:
        there = subprocess.run(["ssh", "-o", "ConnectTimeout=15", "root@motdang-server", "python3", "-", "--one", *urls],
                               input=open(__file__).read(), capture_output=True, text=True, timeout=900).stdout
    except Exception:
        there = "[]"
    H, T = json.loads(here or "[]"), {(r["url"], r["who"]): r for r in json.loads(there or "[]")}
    if as_json:
        print(json.dumps([{"url": r["url"], "who": r["who"], "here": r, "cloud": T.get((r["url"], r["who"]))} for r in H]))
        sys.exit(0)
    f = lambda x: f"{x['code']}{' og' if x['og'] else ''}{' →' + x['loc'][:40] if x['loc'] else ''}" if x else "—"
    cur = None
    for r in H:
        if r["url"] != cur:
            cur = r["url"]
            print(f"\n## {cur}\n{'visitor':28} {'here':24} cloud (Hetzner)")
        t = T.get((r["url"], r["who"]))
        mark = "  ◀" if t and (t["code"], t["loc"]) != (r["code"], r["loc"]) else ""
        print(f"{r['who']:28} {f(r):24} {f(t)}{mark}")
