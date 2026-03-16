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


def gazetteers_to_parquet(repo_dir: Path, cfg: dict) -> Path:
    """Converte JSONs do bible-gazetteers-dataset para Parquets."""
    structured_dir = repo_dir / "data" / "pt" / "structured"

    for name in ["entities", "symbols", "relationships"]:
        fpath = structured_dir / f"{name}.json"
        if not fpath.exists():
            print(f"  ⚠ {fpath} nao encontrado")
            continue

        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            rows = data
        elif isinstance(data, dict):
            rows = list(data.values()) if not any(isinstance(v, list) for v in data.values()) else []
            for v in data.values():
                if isinstance(v, list):
                    rows.extend(v)

        # Converter listas/dicts em strings para parquet
        clean_rows = []
        for row in rows:
            clean = {}
            for k, v in row.items():
                if isinstance(v, (list, dict)):
                    clean[k] = json.dumps(v, ensure_ascii=False)
                else:
                    clean[k] = v
            clean_rows.append(clean)

        if clean_rows:
            df = pd.DataFrame(clean_rows)
            out = DATA_DIR / f"gazetteers_{name}.parquet"
            df.to_parquet(out, index=False)
            print(f"  Salvo: {out} ({len(df):,} linhas)")

    return DATA_DIR / "gazetteers_entities.parquet"


def dictionary_to_parquet(repo_dir: Path, cfg: dict) -> Path:
    """Converte JSONs do bible-dictionary-dataset para Parquet."""
    sources_dir = repo_dir / "data" / "02_sources"
    source_names = {
        "easton": "EAS",
        "smith": "SMI",
        "hastings": "HAS",
        "hitchcock": "HIT",
        "schaff": "SCH",
    }

    rows = []
    for source_dir_name, source_code in source_names.items():
        source_path = sources_dir / source_dir_name
        if not source_path.exists():
            continue

        json_files = sorted(source_path.glob("*.json"))
        for jf in json_files:
            if jf.name == "_index.json":
                continue
            try:
                with open(jf, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            for term_key, entry in data.items():
                for defn in entry.get("definitions", []):
                    text = defn.get("text", "")
                    rows.append({
                        "term": term_key,
                        "name": entry.get("name", term_key),
                        "source": source_code,
                        "source_name": source_dir_name.title(),
                        "definition": text,
                        "refs_count": len(entry.get("scripture_refs", [])),
                        "word_count": len(text.split()),
                        "letter": term_key[0].upper() if term_key else "",
                    })

    if rows:
        df = pd.DataFrame(rows)
        out = DATA_DIR / "dictionary.parquet"
        df.to_parquet(out, index=False)
        print(f"  Salvo: {out} ({len(df):,} linhas, {out.stat().st_size / 1024 / 1024:.1f} MB)")
        return out

    print("  Nenhum dado encontrado")
    return DATA_DIR / "dictionary.parquet"


def topics_to_parquet(repo_dir: Path, cfg: dict) -> Path:
    """Converte JSONs do bible-topics-dataset para Parquet."""
    json_files = collect_json_files(repo_dir, cfg["data_glob"])
    json_files = [f for f in json_files if f.name != "_index.json"]
    print(f"  Encontrados {len(json_files)} arquivos de topicos")

    rows = []
    for jf in tqdm(json_files, desc="  Processando", unit="file"):
        try:
            with open(jf, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        topic = data.get("topic", "")
        slug = data.get("slug", "")
        sources = data.get("sources", [])
        def_refs = data.get("definition_refs", [])
        biblical_refs = data.get("biblical_references", [])
        ref_groups = data.get("reference_groups", [])
        see_also = data.get("see_also", [])

        letter = slug[0].upper() if slug else (topic[0].upper() if topic else "")

        source_nav = "NAV" in sources
        source_tor = "TOR" in sources
        has_def_refs = len(def_refs) > 0
        n_ref_groups = len(ref_groups)
        n_biblical_refs = len(biblical_refs)
        n_def_refs = len(def_refs)
        n_see_also = len(see_also)

        rows.append({
            "topic": topic,
            "slug": slug,
            "letter": letter,
            "source_nav": source_nav,
            "source_tor": source_tor,
            "n_sources": len(sources),
            "has_def_refs": has_def_refs,
            "n_ref_groups": n_ref_groups,
            "n_biblical_refs": n_biblical_refs,
            "n_def_refs": n_def_refs,
            "n_see_also": n_see_also,
        })

    if rows:
        df = pd.DataFrame(rows)
        out = DATA_DIR / "topics.parquet"
        df.to_parquet(out, index=False)
        print(f"  Salvo: {out} ({len(df):,} linhas, {out.stat().st_size / 1024 / 1024:.1f} MB)")
        return out

    print("  Nenhum dado encontrado")
    return DATA_DIR / "topics.parquet"


def images_to_parquet(repo_dir: Path, cfg: dict) -> Path:
    """Converte o parquet do bible-images-dataset para formato otimizado."""
    src = repo_dir / cfg["data_glob"]
    # Fallback: parquet is gitignored, try local path on E: drive
    if not src.exists():
        src = Path("E:/bible-images-dataset/data/00_raw/wikiart/filtered_religious.parquet")
    if not src.exists():
        print(f"  Arquivo fonte nao encontrado. Esperado em:")
        print(f"    {repo_dir / cfg['data_glob']}")
        print(f"    E:/bible-images-dataset/data/00_raw/wikiart/filtered_religious.parquet")
        return DATA_DIR / "images.parquet"

    df = pd.read_parquet(src)
    print(f"  Lidos {len(df):,} registros de {src.name}")

    # Achatar colunas de arrays (numpy arrays -> string separada por |)
    array_cols = [
        "styles", "genres", "tags", "media",
        "artist_nations", "artist_movements", "artist_genres",
    ]
    for col in array_cols:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda v: "|".join(str(x) for x in v) if v is not None and hasattr(v, "__iter__") else ""
            )

    # Adicionar URL das imagens no HuggingFace
    HF_BASE = "https://huggingface.co/datasets/Iuryeng/bible-images-dataset/resolve/main/images"
    df["hf_image_url"] = df["key"].apply(lambda k: f"{HF_BASE}/{k}.jpg")

    out = DATA_DIR / "images.parquet"
    df.to_parquet(out, index=False)
    print(f"  Salvo: {out} ({len(df):,} linhas, {out.stat().st_size / 1024 / 1024:.1f} MB)")
    return out


# Mapa de loaders por nome
LOADERS = {
    "commentaries": commentaries_to_parquet,
    "crossrefs": crossrefs_to_parquet,
    "bibletext": bibletext_to_parquet,
    "gazetteers": gazetteers_to_parquet,
    "dictionary": dictionary_to_parquet,
    "topics": topics_to_parquet,
    "images": images_to_parquet,
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
