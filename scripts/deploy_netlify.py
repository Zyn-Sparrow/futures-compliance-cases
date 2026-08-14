#!/usr/bin/env python3
"""
Netlify部署脚本
通过Netlify API直接部署，保持网站URL不变

需要设置环境变量:
  NETLIFY_SITE_ID: Netlify站点ID
  NETLIFY_AUTH_TOKEN: Netlify个人访问令牌
"""
import os
import sys
import time
import hashlib
import requests
import json

NETLIFY_API = "https://api.netlify.com/api/v1"

def deploy_to_netlify(html_path, site_id=None, auth_token=None):
    """
    通过Netlify API部署HTML文件

    Args:
        html_path: index.html 文件路径
        site_id: Netlify站点ID (从环境变量NETLIFY_SITE_ID获取)
        auth_token: Netlify认证令牌 (从环境变量NETLIFY_AUTH_TOKEN获取)

    Returns:
        deploy_url: 部署后的URL
    """
    site_id = site_id or os.environ.get("NETLIFY_SITE_ID")
    auth_token = auth_token or os.environ.get("NETLIFY_AUTH_TOKEN")

    if not site_id:
        raise ValueError("缺少 NETLIFY_SITE_ID 环境变量。请在Netlify后台 > Site settings > General 获取Site ID")
    if not auth_token:
        raise ValueError("缺少 NETLIFY_AUTH_TOKEN 环境变量。请在 https://app.netlify.com/user/applications#personal-access-tokens 创建令牌")

    # 读取HTML文件
    with open(html_path, "rb") as f:
        file_content = f.read()

    file_name = os.path.basename(html_path)
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/octet-stream",
    }

    print(f"开始部署到Netlify (站点: {site_id})...")

    # 计算文件SHA1
    file_sha1 = hashlib.sha1(file_content).hexdigest()
    file_path_web = f"/{file_name}"  # Netlify API要求的路径格式

    # 步骤1: 创建部署（声明文件）
    create_url = f"{NETLIFY_API}/sites/{site_id}/deploys"
    create_resp = requests.post(
        create_url,
        headers={
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        },
        json={
            "files": {file_path_web: file_sha1},
            "title": f"Weekly Update - {time.strftime('%Y-%m-%d %H:%M')}",
        },
        timeout=30,
    )

    if create_resp.status_code not in (200, 201):
        raise Exception(f"创建部署失败: HTTP {create_resp.status_code} - {create_resp.text}")

    deploy_data = create_resp.json()
    deploy_id = deploy_data["id"]
    print(f"  创建部署成功 (ID: {deploy_id})")

    # 检查是否需要上传文件
    required = deploy_data.get("required", [])
    if file_sha1 in required:
        # 上传文件
        upload_url = f"{NETLIFY_API}/deploys/{deploy_id}/files{file_path_web}"
        upload_headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/octet-stream",
        }

        upload_resp = requests.put(
            upload_url,
            headers=upload_headers,
            data=file_content,
            timeout=60,
        )

        if upload_resp.status_code not in (200, 201):
            raise Exception(f"上传文件失败: HTTP {upload_resp.status_code} - {upload_resp.text}")

        print(f"  文件上传成功 ({len(file_content)} 字节)")
    else:
        print(f"  文件未变化，跳过上传")

    # 等待部署完成
    print("  等待部署处理...")
    for attempt in range(30):
        time.sleep(3)
        status_url = f"{NETLIFY_API}/deploys/{deploy_id}"
        status_resp = requests.get(
            status_url,
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=15,
        )
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            state = status_data.get("state", "")
            print(f"  部署状态: {state}")
            if state == "ready":
                deploy_url = status_data.get("ssl_url", status_data.get("url", ""))
                print(f"  部署完成! URL: {deploy_url}")
                return deploy_url
            elif state in ("error", "rejected"):
                raise Exception(f"部署失败: {state}")

    print("  部署超时，但文件已上传，请稍后检查Netlify后台")
    return f"https://app.netlify.com/sites/{site_id}/deploys/{deploy_id}"

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(base_dir, "dist", "index.html")

    if not os.path.exists(html_path):
        print(f"错误: 找不到 {html_path}")
        print("请先运行 generate_site.py 生成网站")
        sys.exit(1)

    try:
        url = deploy_to_netlify(html_path)
        print(f"\n部署成功! 网站地址: {url}")
    except Exception as e:
        print(f"\n部署失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
