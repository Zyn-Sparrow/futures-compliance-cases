#!/usr/bin/env python3
"""
网站生成脚本
从模板HTML和cases.json生成最终的index.html
"""
import json
import os

def generate_site(cases_path, template_path, output_path):
    """
    从模板和数据生成最终网站HTML

    Args:
        cases_path: cases.json 文件路径
        template_path: index_template.html 文件路径
        output_path: 输出的 index.html 路径
    """
    # 读取案例数据
    with open(cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    # 按发布日期降序排序 (新案例在前)
    cases.sort(key=lambda c: c.get("publish_date", ""), reverse=True)

    # 重新分配ID (确保连续)
    for i, case in enumerate(cases):
        case["id"] = i + 1

    # 读取模板
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # 生成案例数据的JS代码
    cases_js = json.dumps(cases, ensure_ascii=False, indent=2)

    # 替换占位符
    final_html = template.replace("const CASES = __CASES_DATA__;", f"const CASES = {cases_js};")

    # 写入输出文件
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"网站生成完成: {output_path}")
    print(f"  案例总数: {len(cases)}")
    print(f"  文件大小: {len(final_html)} 字节")
    return output_path

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cases_path = os.path.join(base_dir, "data", "cases.json")
    template_path = os.path.join(base_dir, "template", "index_template.html")
    output_path = os.path.join(base_dir, "dist", "index.html")

    generate_site(cases_path, template_path, output_path)

if __name__ == "__main__":
    main()
