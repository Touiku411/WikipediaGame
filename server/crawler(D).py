import time
import requests
import re
import urllib.parse
from collections import deque

TIMEOUT = 120  # time limit in seconds for the search

session = requests.Session()
session.headers.update({
    "User-Agent": "WikiGameBot/1.0 (contact: sgw223@google.com)"
})

class TimeoutErrorWithLogs(Exception):
    def __init__(self, message, logs, time, discovered):
        super().__init__(message)
        self.logs = logs
        self.time = time
        self.discovered = discovered

def get_title_from_url(url):
    raw_title = url.split('/')[-1]
    decoded_title = urllib.parse.unquote(raw_title)
    return decoded_title.replace("_", " ") # 👈 把底線換成空白

def make_url(title, lang="en"):
    title_with_underscores = title.replace(" ", "_")
    encoded_title = urllib.parse.quote(title_with_underscores)
    return f"https://{lang}.wikipedia.org/wiki/{encoded_title}"

def get_wiki_links_api(title, lang="en"):
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "links",
        "titles": title,
        "pllimit": "50",
        "plnamespace": 0,  # 0 代表只抓取一般條目，自動過濾掉 Help: 或 Wikipedia: 等頁面
        "format": "json"
    }
    try:
        # res = requests.get(url, params=params, headers={"User-Agent": "Molliza/5.0"}, timeout=5)
        res = session.get(url, params=params, timeout=5)
        if res.status_code != 200:
            print(f"⚠️ 維基百科警告 (HTTP {res.status_code}): 請求太頻繁，正在暫停...")
            time.sleep(0.5)  # 休息 0.5 秒
            return []
        
        data = res.json()
        pages = data.get("query", {}).get("pages", {})
        page_id = list(pages.keys())[0]
        if page_id == "-1":
            return []
        raw_links = pages[page_id].get("links", [])
        return [link["title"] for link in raw_links]
    except Exception as e:
        print(f"API ERROR for {title}: {e}")
        return []

#bfs
#回傳 path, logs, time, discovered(深度)
def find_path(start_url, target_url):
    lang = "zh" if "zh.wikipedia" in start_url else "en"
    start_title = get_title_from_url(start_url)
    target_title = get_title_from_url(target_url)

    queue = deque([(start_title, [start_title])])
    #走過節點
    visited = set()
    visited.add(start_title)

    logs = []
    max_depth = 4
    start_time = time.time()

    while queue:
        #經過時間
        pass_time = time.time() - start_time
        if pass_time > TIMEOUT:
            logs.append(f"搜尋超過 {TIMEOUT} 秒, 已停止")
            raise TimeoutErrorWithLogs("Search exceeded time limit.", logs, pass_time, len(visited))
        
        item = queue.popleft()
        current_title, current_path = item

        if len(current_path) - 1 >= max_depth:
            continue
        #目前深度
        depth = len(current_path) - 1 

        log_msg = f"正在探索: {current_title} (深度 {depth})"
        print(log_msg)
        logs.append(log_msg)

        links = get_wiki_links_api(current_title, lang)

        for next_title in links:
            #找到目標 回傳path title
            if next_title == target_title:
                pass_time = time.time() - start_time
                final_path_title = current_path + [next_title]
                
                final_path_url = [make_url(t, lang) for t in final_path_title]
                success_log = f"找到終點: {target_title}"
                print(success_log)
                logs.append(success_log)

                return final_path_url, logs, pass_time, len(visited)
            
            if next_title not in visited:
                visited.add(next_title)
                queue.append((next_title, current_path + [next_title]))
    pass_time = time.time() - start_time
    logs.append("找不到路徑 (或超過深度限制)")
    print("\n找不到路徑")
    raise TimeoutErrorWithLogs("Path not found.", logs, pass_time, len(visited))

