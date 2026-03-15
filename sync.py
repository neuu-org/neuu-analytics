"""
sync.py — Sincroniza datasets da org NEUU e converte para Parquet.

Uso:
    python sync.py              # sincroniza todos os datasets habilitados
    python sync.py commentaries # sincroniza apenas um dataset especifico
"""

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent
DATASETS_DIR = ROOT / "datasets"
DATA_DIR = ROOT / "data"
CONFIG_PATH = ROOT / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def sync_repo(org: str, repo: str) -> Path:
    """Clona ou atualiza um repo da org."""
    dest = DATASETS_DIR / repo
    if dest.exists():
        print(f"  Atualizando {repo}...")
        subprocess.run(["git", "-C", str(dest), "pull", "--ff-only"], check=True)
    else:
        print(f"  Clonando {org}/{repo}...")
        url = f"https://github.com/{org}/{repo}.git"
        subprocess.run(["git", "clone", "--depth", "1", url, str(dest)], check=True)
    return dest


def collect_json_files(base_dir: Path, glob_pattern: str) -> list[Path]:
    """Coleta todos os JSONs que casam com o glob pattern."""
    # glob pattern vem como "data/01_cleaned/**/*.json"
    return sorted(base_dir.glob(glob_pattern))


def commentaries_to_parquet(repo_dir: Path, cfg: dict) -> Path:
    """Converte JSONs do bible-commentaries-dataset para Parquet."""
    json_files = collect_json_files(repo_dir, cfg["data_glob"])
    print(f"  Encontrados {len(json_files)} arquivos JSON")

    rows = []
    for jf in tqdm(json_files, desc="  Processando", unit="file"):
        try:
            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        # Extrair categoria do path (ex: .../new_testament/acts/acts/verses/...)
        parts = jf.relative_to(repo_dir).parts
        testament = "unknown"
        category = "unknown"
        for i, p in enumerate(parts):
            if p in ("old_testament", "new_testament"):
                testament = p
                if i + 1 < len(parts):
                    category = parts[i + 1]
                break

        book = data.get("book", "")
        chapter = data.get("chapter", 0)
        verse = data.get("verse", 0)
        status = data.get("commentary_status", "unknown")

        for comm in data.get("commentaries", []):
            content = comm.get("content", "")
            rows.append({
                "testament": testament,
                "category": category,
                "book": book,
                "chapter": int(chapter),
                "verse": int(verse),
                "status": status,
                "author": comm.get("author", "Unknown"),
                "period": comm.get("period", ""),
                "content": content,
                "word_count": len(content.split()),
            })

        if not data.get("commentaries"):
            rows.append({
                "testament": testament,
                "category": category,
                "book": book,
                "chapter": int(chapter),
                "verse": int(verse),
                "status": status,
                "author": None,
                "period": None,
                "content": None,
                "word_count": 0,
            })

    df = pd.DataFrame(rows)
    out = DATA_DIR / "commentaries.parquet"
    df.to_parquet(out, index=False)
    print(f"  Salvo: {out} ({len(df):,} linhas, {out.stat().st_size / 1024 / 1024:.1f} MB)")

    # Enriched (se existir)
    if "enriched_glob" in cfg:
        enriched_files = collect_json_files(repo_dir, cfg["enriched_glob"])
        if enriched_files:
            enrich_rows = []
            for jf in tqdm(enriched_files, desc="  Enriched", unit="file"):
                if jf.name == "enrichment_config.json":
                    continue
                try:
                    with open(jf, encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue

                ref = data.get("verse_reference", "")
                for comm in data.get("commentaries", []):
                    theo = comm.get("theological_analysis", {})
                    summary = comm.get("ai_summary", {})
                    spiritual = comm.get("spiritual_insight", {})
                    enrich_rows.append({
                        "verse_reference": ref,
                        "author": comm.get("author", "Unknown"),
                        "content_pt": comm.get("content_pt", ""),
                        "doctrines": "|".join(theo.get("doctrines", [])),
                        "traditions": "|".join(theo.get("traditions", [])),
                        "theological_method": theo.get("theological_method", ""),
                        "key_points": "|".join(summary.get("key_points", [])),
                        "theme": spiritual.get("theme", ""),
                        "one_sentence": summary.get("one_sentence", ""),
                    })

            df_enriched = pd.DataFrame(enrich_rows)
            out_e = DATA_DIR / "commentaries_enriched.parquet"
            df_enriched.to_parquet(out_e, index=False)
            print(f"  Salvo: {out_e} ({len(df_enriched):,} linhas)")

    return out


def crossrefs_to_parquet(repo_dir: Path, cfg: dict) -> Path:
    """Converte JSONs do bible-crossrefs-dataset para Parquet."""
    json_files = collect_json_files(repo_dir, cfg["data_glob"])
    # Filtrar indexes e metadata
    json_files = [f for f in json_files if "/indexes/" not in str(f).replace("\\", "/")
                  and "/metadata/" not in str(f).replace("\\", "/")]
    print(f"  Encontrados {len(json_files)} arquivos de versiculos")

    rows = []
    for jf in tqdm(json_files, desc="  Processando", unit="file"):
        try:
            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        source = data.get("source_info", {})
        from_book = source.get("book", "")
        from_chapter = source.get("chapter", 0)
        from_verse = source.get("verse", 0)
        from_testament = source.get("testament", "")

        for ref in data.get("cross_references", []):
            has_openbible = "openbible" in ref.get("sources", {})
            has_tsk = "souliberty" in ref.get("sources", {})
            votes = ref.get("votes", 0)

            rows.append({
                "from_book": from_book,
                "from_chapter": int(from_chapter),
                "from_verse": int(from_verse),
                "from_testament": from_testament,
                "to_book": ref.get("to_book", ""),
                "to_chapter": int(ref.get("to_chapter", 0)),
                "to_verse": int(ref.get("to_verse_num", 0)),
                "to_testament": ref.get("to_testament", ""),
                "votes": int(votes),
                "score": int(ref.get("score", 0)),
                "connection_strength": ref.get("connection_strength", ""),
                "source_openbible": has_openbible,
                "source_tsk": has_tsk,
            })

    if rows:
        df = pd.DataFrame(rows)
        out = DATA_DIR / "crossrefs.parquet"
        df.to_parquet(out, index=False)
        print(f"  Salvo: {out} ({len(df):,} linhas, {out.stat().st_size / 1024 / 1024:.1f} MB)")
        return out

    print("  Nenhum dado encontrado")
    return DATA_DIR / "crossrefs.parquet"


def bibletext_to_parquet(repo_dir: Path, cfg: dict) -> Path:
    """Converte JSONs do bible-text-dataset para Parquet."""
    json_files = collect_json_files(repo_dir, cfg["data_glob"])
    print(f"  Encontrados {len(json_files)} arquivos de traducoes")

    rows = []
    for jf in tqdm(json_files, desc="  Processando", unit="file"):
        try:
            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        translation = data.get("translation", jf.stem)
        abbrev = jf.stem  # ex: KJV, NVI, ARA
        lang = jf.parent.name  # ex: english, portuguese

        for book in data.get("books", []):
            book_name = book.get("name", "")
            for chapter in book.get("chapters", []):
                ch_num = chapter.get("chapter", 0)
                for verse in chapter.get("verses", []):
                    text = verse.get("text", "")
                    if isinstance(text, list):
                        text = " ".join(str(t) for t in text)
                    rows.append({
                        "translation": abbrev,
                        "language": lang,
                        "book": book_name,
                        "chapter": int(ch_num),
                        "verse": int(verse.get("verse", 0)),
                        "text": str(text),
                    })

    if rows:
        df = pd.DataFrame(rows)
        out = DATA_DIR / "bibletext.parquet"
        df.to_parquet(out, index=False)
        print(f"  Salvo: {out} ({len(df):,} linhas, {out.stat().st_size / 1024 / 1024:.1f} MB)")
        return out

    print("  Nenhum dado encontrado")
    return DATA_DIR / "bibletext.parquet"


# Mapa de loaders por nome
LOADERS = {
    "commentaries": commentaries_to_parquet,
    "crossrefs": crossrefs_to_parquet,
    "bibletext": bibletext_to_parquet,
}


def main():
    config = load_config()
    org = config["org"]
    target = sys.argv[1] if len(sys.argv) > 1 else None

    DATASETS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

    for key, cfg in config["datasets"].items():
        if target and key != target:
            continue
        if not cfg.get("enabled", False):
            print(f"\n⏭ {cfg['name']} (desabilitado)")
            continue

        print(f"\n{'='*50}")
        print(f"📦 {cfg['name']}")
        print(f"{'='*50}")

        # 1. Sync repo
        repo_dir = sync_repo(org, cfg["repo"])

        # 2. Converter para Parquet
        loader_name = cfg.get("loader", key)
        loader_fn = LOADERS.get(loader_name)
        if loader_fn:
            loader_fn(repo_dir, cfg)
        else:
            print(f"  ⚠ Loader '{loader_name}' nao encontrado")

    print("\n✅ Sync completo!")


if __name__ == "__main__":
    main()
