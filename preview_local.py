from __future__ import annotations

from datetime import datetime

from src.classifier import classify_item
from src.render import render_outputs
from src.scorer import rank_items
from src.summarizer import summarize_items
from run_daily import load_config


def sample_items() -> list[dict]:
    return [
        {
            "source": "Preview",
            "id": "preview-nejm-rct",
            "pmid": "00000001",
            "doi": "10.1056/preview-rct",
            "title": "A Randomized Trial of a Novel GLP-1 Therapy in Adults with Obesity and Cardiovascular Risk",
            "journal": "The New England Journal of Medicine",
            "published": "2026-05-25",
            "authors": ["Preview Author"],
            "abstract": "In this double-blind randomized trial, adults with obesity and cardiovascular risk were assigned to active treatment or placebo. The trial assessed weight reduction, major adverse cardiovascular events, and safety outcomes.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/00000001/",
            "publication_types": ["Randomized Controlled Trial"],
        },
        {
            "source": "Preview",
            "id": "preview-lancet-oncology",
            "pmid": "00000002",
            "doi": "10.1016/preview-oncology",
            "title": "Phase 3 Trial of an Antibody-Drug Conjugate in Metastatic Lung Cancer",
            "journal": "The Lancet Oncology",
            "published": "2026-05-25",
            "authors": ["Preview Author"],
            "abstract": "This phase 3 trial evaluated an antibody-drug conjugate versus standard chemotherapy in patients with metastatic lung cancer, with overall survival and progression-free survival as key endpoints.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/00000002/",
            "publication_types": ["Clinical Trial, Phase III"],
        },
        {
            "source": "Preview",
            "id": "preview-jama-cardio",
            "pmid": "00000003",
            "doi": "10.1001/preview-cardio",
            "title": "Intensive Blood Pressure Control After Myocardial Infarction: A Multicenter Clinical Trial",
            "journal": "JAMA Cardiology",
            "published": "2026-05-25",
            "authors": ["Preview Author"],
            "abstract": "A multicenter clinical trial studied intensive blood pressure control after myocardial infarction and assessed recurrent cardiovascular events, adverse events, and patient-reported outcomes.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/00000003/",
            "publication_types": ["Clinical Trial", "Multicenter Study"],
        },
        {
            "source": "Preview",
            "id": "preview-nm-translational",
            "pmid": "00000004",
            "doi": "10.1038/preview-translational",
            "title": "Spatial Immune Remodeling Predicts Response to Cell Therapy in Autoimmune Disease",
            "journal": "Nature Medicine",
            "published": "2026-05-25",
            "authors": ["Preview Author"],
            "abstract": "This translational study used spatial omics and immune profiling to identify tissue immune remodeling associated with response to cell therapy in autoimmune disease.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/00000004/",
            "publication_types": ["Journal Article"],
        },
        {
            "source": "Preview",
            "id": "preview-cell-mechanism",
            "pmid": "00000005",
            "doi": "10.1016/preview-cell",
            "title": "A Microglia-Macrophage Circuit Controls Neuroinflammation in Neurodegeneration",
            "journal": "Cell",
            "published": "2026-05-25",
            "authors": ["Preview Author"],
            "abstract": "Mechanistic experiments reveal a microglia-macrophage inflammatory circuit that shapes neurodegeneration, suggesting potential therapeutic targets and biomarkers.",
            "url": "https://pubmed.ncbi.nlm.nih.gov/00000005/",
            "publication_types": ["Journal Article"],
        },
    ]


def main() -> int:
    config = load_config()
    items = [classify_item(item, config["topics"]) for item in sample_items()]
    ranked = rank_items(items, config["journals"], config["scoring"], limit=10)
    summarized = summarize_items(ranked)
    render_outputs(summarized, [], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Preview generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
