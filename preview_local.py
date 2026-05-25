from __future__ import annotations

from datetime import datetime

from src.classifier import classify_item
from src.render import render_outputs
from src.scorer import rank_items
from src.summarizer import summarize_items
from run_daily import load_config


def sample_items() -> list[dict]:
    cn_titles = [
        ("国家卫健委发布重大疾病早筛与慢病管理新进展", "公共卫生/流行病学"),
        ("我国团队公布肿瘤免疫治疗联合策略研究进展", "肿瘤/血液肿瘤"),
        ("医疗AI辅助影像诊断研究进入多中心验证阶段", "医疗AI/数字医学"),
        ("干细胞与外泌体治疗转化研究获得新数据", "生物医药/细胞与基因治疗"),
        ("脑科学项目推动神经退行性疾病早诊技术开发", "神经科学/神经疾病"),
    ]
    intl = [
        ("The New England Journal of Medicine", "A Randomized Trial of a Novel GLP-1 Therapy in Adults with Obesity and Cardiovascular Risk", "Randomized Controlled Trial"),
        ("The Lancet Oncology", "Phase 3 Trial of an Antibody-Drug Conjugate in Metastatic Lung Cancer", "Clinical Trial, Phase III"),
        ("JAMA Cardiology", "Intensive Blood Pressure Control After Myocardial Infarction: A Multicenter Clinical Trial", "Clinical Trial"),
        ("Nature Medicine", "Spatial Immune Remodeling Predicts Response to Cell Therapy in Autoimmune Disease", "Journal Article"),
        ("Cell", "A Microglia-Macrophage Circuit Controls Neuroinflammation in Neurodegeneration", "Journal Article"),
        ("Science Translational Medicine", "RNA Therapy Restores Protein Expression in a Rare Genetic Disorder", "Journal Article"),
        ("BMJ", "Population Screening for Early Cancer Detection: A Pragmatic Trial", "Clinical Trial"),
        ("Nature Biotechnology", "CRISPR Base Editing for an Inherited Blood Disorder", "Journal Article"),
        ("JAMA Oncology", "Neoadjuvant Immunotherapy in Resectable Solid Tumors", "Clinical Trial"),
        ("The Lancet Neurology", "A Disease-Modifying Therapy in Early Parkinson Disease", "Clinical Trial, Phase II"),
        ("Nature", "Single-cell Atlas Reveals Human Immune Aging", "Journal Article"),
        ("Science", "A Vaccine Platform Generates Broad Antiviral Immunity", "Journal Article"),
        ("Cancer Cell", "Tumor Microenvironment Remodeling Drives Resistance to Immunotherapy", "Journal Article"),
        ("Neuron", "Human Brain Organoid Model Links Inflammation to Synaptic Dysfunction", "Journal Article"),
        ("Nature Communications", "Medical Large Language Model Improves Triage Accuracy in Emergency Care", "Journal Article"),
    ]
    items = []
    for i, (title, topic_cn) in enumerate(cn_titles, 1):
        items.append({
            "source": "Preview CN News",
            "source_region": "cn",
            "source_language": "zh",
            "news_origin": "Chinese biomedical news",
            "content_bucket": "cn_news",
            "id": f"preview-cn-{i}",
            "pmid": "",
            "doi": "",
            "title": title,
            "translated_title_cn": title,
            "journal": "中文医学新闻源",
            "published": "2026-05-25",
            "authors": [],
            "abstract": f"{title}。该条模拟中文医学科学新闻用于预览页面结构，正式运行时会由中文新闻源自动替换。",
            "url": "https://example.com/cn-news",
            "publication_types": ["News"],
            "study_type": "Medical news",
            "topic_cn": topic_cn,
            "summary_quality": "source_chinese",
        })
    for i, (journal, title, ptype) in enumerate(intl, 1):
        items.append({
            "source": "Preview",
            "source_region": "intl",
            "source_language": "en",
            "news_origin": "International top-journal paper",
            "content_bucket": "intl_news",
            "id": f"preview-intl-{i}",
            "pmid": f"00000{i:03d}",
            "doi": f"10.0000/preview-{i}",
            "title": title,
            "journal": journal,
            "published": "2026-05-25",
            "authors": ["Preview Author"],
            "abstract": "This preview item represents a biomedical top-journal paper or clinical trial. It includes study design, disease area, key endpoints, and interpretation limits for homepage testing.",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/00000{i:03d}/",
            "publication_types": [ptype],
        })
    return items


def main() -> int:
    config = load_config()
    items = [classify_item(item, config["topics"]) for item in sample_items()]
    from src.selector import select_news_20
    ranked = rank_items(items, config["journals"], config["scoring"], limit=500)
    selected, notes = select_news_20(ranked)
    summarized = summarize_items(selected)
    render_outputs(summarized, notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Preview generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
