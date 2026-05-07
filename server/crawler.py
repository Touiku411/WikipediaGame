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

#正向api
def get_fwd_links_api(title, lang="en"):
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
        res = session.get(url, params=params, timeout=5)
        if res.status_code != 200:
            time.sleep(0.5)
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

#反向api
def get_bwd_links_api(title, lang="en"):
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "backlinks",
        "bltitle": title,
        "bllimit": "max",
        "blnamespace": 0,  # 0 代表只抓取一般條目，自動過濾掉 Help: 或 Wikipedia: 等頁面
        "format": "json"
    }
    try:
        res = session.get(url, params=params, timeout=5)
        if res.status_code != 200:
            time.sleep(0.5)
            return []
        data = res.json()
        # 修正：反向 API 直接抓 backlinks
        backlinks = data.get("query", {}).get("backlinks", [])
        return [bl["title"] for bl in backlinks]
    except Exception as e:
        print(f"API ERROR for {title}: {e}")
        return []

#bfs
#回傳 path, logs, time, discovered(深度)
def find_path(start_url, target_url):
    lang = "zh" if "zh.wikipedia" in start_url else "en"
    start_title = get_title_from_url(start_url)
    target_title = get_title_from_url(target_url)

    if start_title == target_title:
        return [make_url(start_title, lang)], ["起點與終點相同"], 0, 1
    
    fwd_queue = deque([start_title])
    bwd_queue = deque([target_title])

    #走過節點
    fwd_visited = {}
    fwd_visited[start_title] = [start_title]
    bwd_visited = {}
    bwd_visited[target_title] = [target_title]

    logs = []
    max_depth = 3
    start_time = time.time()

    while fwd_queue and bwd_queue:
        #經過時間
        pass_time = time.time() - start_time
        if pass_time > TIMEOUT:
            logs.append(f"搜尋超過 {TIMEOUT} 秒, 已停止")
            raise TimeoutErrorWithLogs("Search exceeded time limit.", logs, pass_time, len(bwd_visited) + len(fwd_visited))
        #正
        cur_fwd = fwd_queue.popleft()
        #目前fwd深度
        depth_fwd = len(fwd_visited[cur_fwd]) - 1
        

        if depth_fwd < max_depth:
            log_msg = f"[正向] 探索: {cur_fwd} (深度 {depth_fwd})"
            print(log_msg)
            logs.append(log_msg)

            links = get_fwd_links_api(cur_fwd, lang)

            for next_title in links:
                #找到目標 回傳path title
                if next_title in bwd_visited:
                    pass_time = time.time() - start_time
                    fwd_path = fwd_visited[cur_fwd] + [next_title]
                    bwd_path = bwd_visited[next_title]
                    
                    final_path_title = fwd_path + bwd_path[::-1][1:]
                    final_path_url = [make_url(t, lang) for t in final_path_title]

                    success_log = f"找到終點: {next_title}"
                    print(success_log)
                    logs.append(success_log)

                    return final_path_url, logs, pass_time, len(fwd_visited) + len(bwd_visited)
                
                if next_title not in fwd_visited:
                    fwd_visited[next_title] = fwd_visited[cur_fwd] + [next_title]
                    fwd_queue.append(next_title)

        #反
        cur_bwd = bwd_queue.popleft()
        #目前bwd深度
        depth_bwd = len(bwd_visited[cur_bwd]) - 1
        

        if depth_bwd < max_depth:
            log_msg = f"[反向] 探索: {cur_bwd} (深度 {depth_bwd})"
            print(log_msg)
            logs.append(log_msg)

            links = get_bwd_links_api(cur_bwd, lang)

            for prev_title in links:
                #找到目標 回傳path title
                if prev_title in fwd_visited:
                    pass_time = time.time() - start_time
                    fwd_path = fwd_visited[prev_title]
                    bwd_path = bwd_visited[cur_bwd] + [prev_title]
                    
                    final_path_title = fwd_path + bwd_path[::-1][1:]
                    final_path_url = [make_url(t, lang) for t in final_path_title]

                    success_log = f"找到終點: {prev_title}"
                    print(success_log)
                    logs.append(success_log)

                    return final_path_url, logs, pass_time, len(fwd_visited) + len(bwd_visited)
                
                if prev_title not in bwd_visited:
                    bwd_visited[prev_title] = bwd_visited[cur_bwd] + [prev_title]
                    bwd_queue.append(prev_title)
    pass_time = time.time() - start_time
    logs.append("找不到路徑 (或超過深度限制)")
    print("\n找不到路徑")
    raise TimeoutErrorWithLogs("Path not found.", logs, pass_time, len(fwd_visited) + len(bwd_visited))

