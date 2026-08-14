#!/usr/bin/env python3
"""
案例处理脚本
从爬取的原始文本中提取结构化字段：
- violation: 违规要点
- penalty: 处罚结果
- summary: 案例摘要
- keywords: 关键词
- main_category / sub_category: 分类
"""
import re
import json
import os

# ========== 分类规则 ==========
CATEGORY_RULES = [
    {
        "main_category": "互联网营销违规",
        "sub_category": "互联网营销",
        "keywords": ["互联网营销", "直播", "营销内容", "短视频", "引流", "新媒体营销"],
    },
    {
        "main_category": "居间业务违规",
        "sub_category": "居间管理",
        "keywords": ["居间", "居间人", "居间业务", "居间合作"],
    },
    {
        "main_category": "廉洁从业违规",
        "sub_category": "廉洁从业",
        "keywords": ["廉洁", "侵占", "利益输送", "挪用", "私下收受", "回扣"],
    },
    {
        "main_category": "从业人员违规",
        "sub_category": "从业人员管理",
        "keywords": ["从业人员", "从业资格", "代客交易", "以他人名义", "私下提供", "交易咨询"],
    },
    {
        "main_category": "异常交易",
        "sub_category": "异常交易",
        "keywords": ["异常交易", "对敲", "转移资金", "实际控制关系", "超限", "日内开仓"],
    },
    {
        "main_category": "内控缺陷",
        "sub_category": "内控管理",
        "keywords": ["内控", "内部控制", "风险管控", "合规管理", "内部控制缺陷"],
    },
    {
        "main_category": "合规经营",
        "sub_category": "适当性管理",
        "keywords": ["适当性", "风险承受能力", "风险测评", "投资者适当性"],
    },
    {
        "main_category": "合规经营",
        "sub_category": "风险管理",
        "keywords": ["风险管理", "做市业务", "场外衍生品", "保险+期货", "资管业务"],
    },
]

# ========== 关键词提取词典 ==========
PENALTY_KEYWORDS = [
    "训诫", "警告", "公开谴责", "通报批评", "责令改正", "暂停",
    "撤销", "取消", "限期整改", "暂停开户", "暂停从业资格",
    "罚款", "警示函", "监管谈话", "记入诚信档案", "不适当人选",
    "暂停新签", "暂停业务",
]

VIOLATION_KEYWORDS = [
    "内控缺陷", "内控管理", "内部控制", "合规风控", "风险管理",
    "居间管理", "居间业务", "互联网营销", "适当性管理", "风险测评",
    "交易者适当性", "从业人员", "从业资格", "廉洁从业",
    "代客交易", "以他人名义", "利益输送", "侵占",
    "做市业务", "场外衍生品", "资管业务", "保险+期货",
    "业务隔离", "岗位兼职", "员工管理", "展业管理",
    "异常交易", "对敲", "转移资金", "实际控制",
    "风险提示", "告知义务", "风险揭示",
]

def classify_case(text):
    """根据全文内容进行分类"""
    text_lower = text.lower() if text else ""
    for rule in CATEGORY_RULES:
        for kw in rule["keywords"]:
            if kw in text:
                return rule["main_category"], rule["sub_category"]
    return "合规经营", "合规经营"

def extract_violation(text):
    """从正文中提取违规要点"""
    if not text:
        return ""

    # 模式1: "经查明，XXX。违反了YYY"
    patterns = [
        r"经查明[，,]?(.+?)(?:鉴于|依据|根据|以上基本事实)",
        r"经查[，,]?(.+?)(?:鉴于|依据|根据|以上基本事实)",
        r"查明[，,]?(.+?)(?:鉴于|依据|根据|以上基本事实)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            violation = match.group(1).strip()
            # 清理换行和多余空格
            violation = re.sub(r"\s+", " ", violation)
            # 截取合理长度
            if len(violation) > 300:
                # 尝试在句号处截断
                cut = violation[:300]
                last_period = cut.rfind("。")
                if last_period > 100:
                    violation = violation[:last_period + 1]
                else:
                    violation = cut + "..."
            return violation

    # 模式2: 如果没有标准格式，提取包含"违反"的句子
    sentences = re.split(r"[。；！？]", text)
    violation_sentences = []
    for s in sentences:
        if "违反" in s or "违规" in s or "不符合" in s or "未能" in s:
            violation_sentences.append(s.strip())

    if violation_sentences:
        return "。".join(violation_sentences[:3]) + "。"

    return ""

def extract_penalty(text):
    """从正文中提取处罚结果"""
    if not text:
        return ""

    patterns = [
        r"决定[：:]\s*(.+?)(?:如果对本|当事人可在|特此公告|$)",
        r"作出如下决定[：:]\s*(.+?)(?:如果对本|当事人可在|特此公告|$)",
        r"处理决定[：:]\s*(.+?)(?:如果对本|当事人可在|特此公告|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            penalty = match.group(1).strip()
            penalty = re.sub(r"\s+", " ", penalty)
            # 截取合理长度
            if len(penalty) > 200:
                cut = penalty[:200]
                last_period = cut.rfind("。")
                if last_period > 50:
                    penalty = penalty[:last_period + 1]
                else:
                    penalty = cut + "..."
            return penalty

    # 模式2: 搜索处罚关键词
    for kw in PENALTY_KEYWORDS:
        idx = text.find(kw)
        if idx >= 0:
            # 往前找"给予"或"采取"
            start = max(0, idx - 20)
            context = text[start:idx + len(kw) + 10].strip()
            return context

    return ""

def generate_summary(title, violation, penalty, full_text):
    """生成案例摘要"""
    if violation and penalty:
        # 从违规和处罚中生成摘要
        summary_parts = []
        # 提取当事人名称
        party_match = re.search(r"当事人[：:](.+?)(?:，|。|\n)", full_text)
        party = party_match.group(1).strip() if party_match else ""

        if party:
            # 简化当事人名称
            party = re.sub(r"[（(].*?[)）]", "", party).strip()
            if len(party) > 30:
                party = party[:30] + "..."
            summary_parts.append(party)

        if violation:
            v = violation[:100]
            if len(violation) > 100:
                v += "..."
            summary_parts.append(f"因{v}")
        if penalty:
            p = penalty[:80]
            if len(penalty) > 80:
                p += "..."
            summary_parts.append(f"被{p}")

        return "，".join(summary_parts) + "。" if summary_parts else title

    # 备选：从标题和正文开头生成
    if full_text:
        first_sentence = re.split(r"[。！？\n]", full_text)
        for s in first_sentence:
            s = s.strip()
            if len(s) > 20:
                return s[:150]

    return title

def extract_keywords(text, title, violation, penalty):
    """从文本中提取关键词"""
    keywords = set()
    combined = f"{title} {violation} {penalty} {text[:500]}"

    # 1. 匹配预定义的违规关键词
    for kw in VIOLATION_KEYWORDS:
        if kw in combined:
            keywords.add(kw)

    # 2. 匹配处罚关键词
    for kw in PENALTY_KEYWORDS:
        if kw in combined:
            keywords.add(kw)

    # 3. 提取公司名称 (XX期货)
    company_patterns = [
        r"([\u4e00-\u9fa5]{2,8}期货[股份有限公司]*)",
        r"([\u4e00-\u9fa5]{2,8}风险管理[有限公司]*)",
    ]
    for pattern in company_patterns:
        matches = re.findall(pattern, combined)
        for m in matches[:2]:  # 最多2个公司名
            keywords.add(m)

    # 4. 提取证监局名称
    bureau_match = re.findall(r"([\u4e00-\u9fa5]{2,4}证监局)", combined)
    for m in bureau_match[:1]:
        keywords.add(m)

    # 5. 提取交易所名称
    exchange_match = re.findall(r"(上期所|郑商所|大商所|上期能源|中金所)", combined)
    for m in exchange_match[:1]:
        keywords.add(m)

    # 限制关键词数量
    result = list(keywords)[:8]
    return json.dumps(result, ensure_ascii=False)

def process_case(raw_case, next_id):
    """
    处理单个案例，从原始数据提取结构化字段

    Args:
        raw_case: 包含 title, url, publish_date, full_text, source 的字典
        next_id: 下一个案例ID

    Returns:
        处理后的完整案例字典
    """
    full_text = raw_case.get("full_text", "")
    title = raw_case.get("title", "")
    violation = extract_violation(full_text)
    penalty = extract_penalty(full_text)
    summary = generate_summary(title, violation, penalty, full_text)
    keywords = extract_keywords(full_text, title, violation, penalty)
    main_category, sub_category = classify_case(full_text)

    case = {
        "id": next_id,
        "title": title,
        "main_category": main_category,
        "sub_category": sub_category,
        "source": raw_case.get("source", "中期协"),
        "source_type": raw_case.get("source_type", "official"),
        "summary": summary,
        "violation": violation,
        "penalty": penalty,
        "keywords": keywords,
        "url": raw_case.get("url", ""),
        "full_text": full_text,
        "publish_date": raw_case.get("publish_date", ""),
    }

    return case

def process_new_cases(new_raw_cases, existing_cases):
    """
    批量处理新案例

    Args:
        new_raw_cases: 爬虫返回的原始案例列表
        existing_cases: 已有案例列表

    Returns:
        处理后的案例列表
    """
    if not new_raw_cases:
        return []

    # 计算起始ID
    max_id = max(c["id"] for c in existing_cases) if existing_cases else 0
    next_id = max_id + 1

    processed = []
    for raw_case in new_raw_cases:
        case = process_case(raw_case, next_id)
        processed.append(case)
        next_id += 1
        print(f"  处理完成: [{case['publish_date']}] {case['title'][:40]}...")
        print(f"    分类: {case['main_category']} / {case['sub_category']}")
        print(f"    违规: {case['violation'][:60]}...")
        print(f"    处罚: {case['penalty'][:60]}...")

    return processed

def main():
    """测试入口"""
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "cases.json")
    with open(data_path, "r", encoding="utf-8") as f:
        existing = json.load(f)

    print(f"已有 {len(existing)} 条案例")

    # 模拟一个新案例
    test_case = {
        "title": "关于对金元期货股份有限公司、聂义锋、吴育娜作出纪律处分的决定",
        "url": "https://www.cfachina.org/informationpublicity/discipline/202608/t20260807_89741.html",
        "publish_date": "2026-08-07",
        "full_text": "中期协字〔2026〕148号\n当事人：金元期货股份有限公司，聂义锋，吴育娜。\n经查明，金元期货股份有限公司存在居间人管理不到位、互联网营销合规管控缺失等问题，违反了《期货公司监督管理办法》的相关规定。\n鉴于以上基本事实和审理情况，依据《中国期货业协会纪律处分程序》的规定，中国期货业协会决定：\n给予金元期货股份有限公司训诫的纪律处分。",
        "source": "中期协",
        "source_type": "official",
    }

    processed = process_new_cases([test_case], existing)
    if processed:
        print(f"\n处理结果:")
        print(json.dumps(processed[0], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
