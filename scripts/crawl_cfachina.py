#!/usr/bin/env python3
"""
中期协官网纪律处分页面爬虫
通过中期协官网API接口获取纪律处分决定，高效可靠

API: https://www.cfachina.org/qx-search/api/wcmSearch/searchDocsByProgram
参数: pageNo, pageSize, keyword, programName
"""
import re
import time
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.cfachina.org"
API_URL = f"{BASE_URL}/qx-search/api/wcmSearch/searchDocsByProgram"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": f"{BASE_URL}/informationpublicity/discipline/",
}

def clean_html_tags(text):
    """清理HTML标签和多余空白"""
    if not text:
        return ""
    # 移除HTML标签
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator="\n")
    # 替换全角空格
    text = text.replace("\u3000", " ")
    # 清理多余空白
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def fetch_api_page(page_no, page_size=20):
    """通过API获取一页纪律处分数据"""
    params = {
        "pageNo": page_no,
        "pageSize": page_size,
        "keyword": "",
        "programName": "纪律处分",
    }
    for attempt in range(3):
        try:
            resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("errcode") == 0:
                    return data["data"]
            else:
                print(f"  API返回 HTTP {resp.status_code} (尝试 {attempt+1})")
        except requests.RequestException as e:
            print(f"  请求错误: {e} (尝试 {attempt+1})")
        time.sleep(2)
    return None

def get_all_discipline_items():
    """获取所有纪律处分条目（含全文）"""
    all_items = []
    page_no = 1
    page_size = 20

    print(f"正在通过API获取纪律处分数据...")
    while True:
        data = fetch_api_page(page_no, page_size)
        if not data:
            print(f"  第 {page_no} 页获取失败，停止")
            break

        data_list = data.get("dataList", [])
        total = data.get("total", 0)

        if not data_list:
            break

        all_items.extend(data_list)
        print(f"  第 {page_no} 页: 获取 {len(data_list)} 条 (累计 {len(all_items)}/{total})")

        if len(all_items) >= total:
            break

        page_no += 1
        time.sleep(0.5)  # 礼貌性延迟

    print(f"总计获取 {len(all_items)} 条记录")
    return all_items

def crawl_new_cases(existing_urls):
    """
    爬取中期协纪律处分页面，返回不在 existing_urls 中的新案例

    Args:
        existing_urls: 已有案例的URL集合

    Returns:
        list of dict: 新案例列表，包含 title, url, publish_date, full_text, source
    """
    print("=" * 60)
    print("开始爬取中期协纪律处分页面")
    print("=" * 60)

    all_items = get_all_discipline_items()

    new_cases = []
    for item in all_items:
        doc_url = urljoin(BASE_URL, item.get("docPubUrl", ""))
        if doc_url in existing_urls:
            continue

        # 清理标题（API返回的标题包含HTML标签）
        raw_title = item.get("docTitle", "")
        title = clean_html_tags(raw_title)

        # 清理全文
        raw_content = item.get("docContent", "")
        full_text = clean_html_tags(raw_content)

        if not full_text or len(full_text) < 20:
            continue

        case = {
            "title": title,
            "url": doc_url,
            "publish_date": item.get("docRelTime", ""),
            "full_text": full_text,
            "source": "中期协",
            "source_type": "official",
        }
        new_cases.append(case)

    print(f"\n发现 {len(new_cases)} 条新案例")
    for c in new_cases:
        print(f"  - [{c['publish_date']}] {c['title'][:50]}")

    print(f"\n爬取完成，共获取 {len(new_cases)} 条新案例正文")
    return new_cases

def main():
    """测试入口：直接运行爬虫并打印结果"""
    import os
    cases_path = os.path.join(os.path.dirname(__file__), "..", "data", "cases.json")
    with open(cases_path, "r", encoding="utf-8") as f:
        existing_cases = json.load(f)

    existing_urls = {c.get("url", "") for c in existing_cases}
    print(f"已有 {len(existing_urls)} 条案例URL")

    new_cases = crawl_new_cases(existing_urls)

    if new_cases:
        print(f"\n新案例预览:")
        for c in new_cases:
            print(f"\n  标题: {c['title']}")
            print(f"  日期: {c['publish_date']}")
            print(f"  URL: {c['url']}")
            print(f"  正文前200字: {c['full_text'][:200]}")
    else:
        print("\n没有新案例")

if __name__ == "__main__":
    main()
