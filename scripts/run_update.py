#!/usr/bin/env python3
"""
主编排脚本 - 期货合规案例库自动更新流程

执行步骤:
1. 加载已有案例数据
2. 爬取中期协官网最新纪律处分决定
3. 处理新案例（提取违规要点、处罚结果、摘要、关键词）
4. 合并到已有案例库
5. 生成更新后的网站HTML
6. 部署到Netlify（如果配置了凭据）
"""
import json
import os
import sys
import subprocess
from datetime import datetime

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

BASE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_PATH = os.path.join(BASE_DIR, "data", "cases.json")
TEMPLATE_PATH = os.path.join(BASE_DIR, "template", "index_template.html")
DIST_PATH = os.path.join(BASE_DIR, "dist", "index.html")

def load_cases():
    """加载已有案例"""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cases(cases):
    """保存案例数据"""
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
    print(f"案例数据已保存: {DATA_PATH} ({len(cases)} 条)")

def main():
    print("=" * 60)
    print(f"期货合规案例库自动更新 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 加载已有案例
    existing_cases = load_cases()
    existing_urls = {c.get("url", "") for c in existing_cases}
    print(f"\n[1/6] 已加载 {len(existing_cases)} 条已有案例")

    # 2. 爬取中期协官网
    print(f"\n[2/6] 爬取中期协官网...")
    from crawl_cfachina import crawl_new_cases
    new_raw_cases = crawl_new_cases(existing_urls)

    if not new_raw_cases:
        print("\n没有发现新案例，跳过更新。")
        # 仍然生成网站（确保最新）
        print(f"\n[5/6] 重新生成网站...")
        from generate_site import generate_site
        generate_site(DATA_PATH, TEMPLATE_PATH, DIST_PATH)
    else:
        # 3. 处理新案例
        print(f"\n[3/6] 处理 {len(new_raw_cases)} 条新案例...")
        from process_cases import process_new_cases
        new_cases = process_new_cases(new_raw_cases, existing_cases)

        # 4. 合并案例
        print(f"\n[4/6] 合并案例...")
        all_cases = existing_cases + new_cases
        save_cases(all_cases)

        # 5. 生成网站
        print(f"\n[5/6] 生成网站...")
        from generate_site import generate_site
        generate_site(DATA_PATH, TEMPLATE_PATH, DIST_PATH)

    # 6. 部署到Netlify
    print(f"\n[6/6] 部署到Netlify...")
    netlify_site_id = os.environ.get("NETLIFY_SITE_ID")
    netlify_token = os.environ.get("NETLIFY_AUTH_TOKEN")

    if netlify_site_id and netlify_token:
        try:
            from deploy_netlify import deploy_to_netlify
            url = deploy_to_netlify(DIST_PATH)
            print(f"\n{'=' * 60}")
            print(f"更新完成! 网站已部署: {url}")
            print(f"{'=' * 60}")
        except Exception as e:
            print(f"\n部署失败: {e}")
            print("网站HTML已生成在 dist/index.html，可手动上传")
    else:
        print("  未配置 Netlify 凭据 (NETLIFY_SITE_ID / NETLIFY_AUTH_TOKEN)")
        print("  网站HTML已生成在 dist/index.html")
        print(f"\n{'=' * 60}")
        print("更新完成! (未自动部署，请手动上传或配置Netlify凭据)")
        print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
