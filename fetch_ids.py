#!/usr/bin/env python3
"""
fetch_ids.py (non-interactive mode available)

Usage interactive:
  python3 fetch_ids.py --modlist modlist.json --manifest manifest.json --output manifest.filled.json

Usage non-interactive (suitable for CI):
  python3 fetch_ids.py --modlist modlist.json --manifest manifest.json --output manifest.filled.json --non-interactive

Behavior:
- interactive (default): prompts for confirmation for each mod and file selection.
- non-interactive: picks best candidate automatically (highest name similarity + latest file that mentions 1.21 in gameVersions or fileName).
"""
import os
import sys
import json
import time
import argparse
from difflib import SequenceMatcher

try:
    import requests
except Exception:
    print("Missing dependency 'requests'. Install with: pip install requests")
    sys.exit(1)

API_KEY = os.getenv("CURSEFORGE_API_KEY")
if not API_KEY:
    print("ERROR: CURSEFORGE_API_KEY not set. Export it before running.")
    sys.exit(1)

HEADERS = {"x-api-key": API_KEY}
GAME_ID = 432  # Minecraft in CurseForge API

SEARCH_URL = "https://api.curseforge.com/v1/mods/search"
MODFILES_URL = "https://api.curseforge.com/v1/mods/{modId}/files"

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def search_mod(name, page_size=10):
    params = {"gameId": GAME_ID, "searchFilter": name, "pageSize": page_size}
    resp = requests.get(SEARCH_URL, headers=HEADERS, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])

def get_mod_files(mod_id):
    url = MODFILES_URL.format(modId=mod_id)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])

def pick_best_match(name, candidates):
    scored = []
    for c in candidates:
        cname = c.get("name") or ""
        score = similar(name, cname)
        downloads = c.get("downloadCount", 0) or 0
        scored.append((score, downloads, c))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return [c for (_,_,c) in scored]

def pick_file_noninteractive(files):
    # prefer files that mention 1.21 in gameVersions or filename
    candidates = []
    for f in files:
        gameVersions = f.get("gameVersions") or []
        fname = f.get("fileName") or ""
        score = 0
        if any("1.21" in gv for gv in gameVersions):
            score += 2
        if "1.21" in fname:
            score += 1
        # newer fileDate preferred
        fileDate = f.get("fileDate") or ""
        downloads = f.get("downloadCount") or 0
        candidates.append((score, fileDate, downloads, f))
    candidates.sort(key=lambda x: (-x[0], x[1], -x[2]), reverse=False)
    # the sort above yields ascending; pick last for highest
    return candidates[-1][3] if candidates else None

def present_candidates_interactive(name, candidates):
    if not candidates:
        print(f"  No candidates found for '{name}'.")
        return None
    best = pick_best_match(name, candidates)
    print(f"\nCandidates for '{name}':")
    for i, c in enumerate(best[:6], start=1):
        print(f"  [{i}] {c.get('name')}  (projectID={c.get('id')})")
    choice = input("  Choose index (or enter projectID manually, or 's' to skip): ").strip()
    if choice.lower() == 's' or choice == '':
        return None
    if choice.isdigit():
        idx = int(choice)
        if idx >= 1 and idx <= len(best[:6]):
            return best[idx-1]
        else:
            pid = int(choice)
            return {"id": pid, "name": None}
    else:
        try:
            pid = int(choice)
            return {"id": pid, "name": None}
        except Exception:
            print("  Invalid input, skipping.")
            return None

def present_files_interactive(mod):
    mod_id = mod.get("id")
    if not mod_id:
        mod_id = int(input("Enter projectID to fetch files for: ").strip())
    files = get_mod_files(mod_id)
    if not files:
        print(f"  No files returned for projectID {mod_id}.")
        return None
    candidates = []
    for f in files:
        gameVersions = f.get("gameVersions") or []
        fname = f.get("fileName") or ""
        if any("1.21" in gv for gv in gameVersions) or "1.21" in fname:
            candidates.append(f)
    if not candidates:
        candidates = files
    candidates.sort(key=lambda x: x.get("fileDate", ""), reverse=True)
    print(f"  Found {len(candidates)} candidate files (filtered by 1.21.x preferred). Showing top 6:")
    for i, f in enumerate(candidates[:6], start=1):
        print(f"    [{i}] id={f.get('id')}  name='{f.get('displayName')[:80]}'")
        print(f"         gameVersions={f.get('gameVersions')}")
    choice = input("  Choose file index (default 1), or enter fileID manually, or 's' to skip: ").strip()
    if choice.lower() == 's' or choice == '':
        return candidates[0] if candidates else None
    if choice.isdigit():
        idx = int(choice)
        if idx >= 1 and idx <= len(candidates[:6]):
            return candidates[idx-1]
        else:
            fid = int(choice)
            for f in files:
                if f.get('id') == fid:
                    return f
            print("  fileID not found in listed files; skipping.")
            return None
    else:
        print("  Invalid input; selecting first candidate.")
        return candidates[0] if candidates else None

def main(args):
    with open(args.modlist, 'r', encoding='utf-8') as fh:
        mods = json.load(fh)
    with open(args.manifest, 'r', encoding='utf-8') as fh:
        manifest = json.load(fh)
    files_array = []
    missing = []
    for entry in mods:
        name = entry.get("name")
        if not name:
            continue
        print("\n---")
        print(f"Processing: {name}")
        try:
            candidates = search_mod(name)
            if not candidates:
                print(f"  No search results for {name}")
                missing.append({"name": name, "reason": "no_search"})
                continue
            best = pick_best_match(name, candidates)[0]
            if args.non_interactive:
                mod = best
                print(f"  Auto-selected project: {mod.get('name')} (id={mod.get('id')})")
                files = get_mod_files(mod.get('id'))
                file_choice = pick_file_noninteractive(files)
                if not file_choice:
                    print(f"  No suitable files for {name}")
                    missing.append({"name": name, "projectID": mod.get('id'), "reason": "no_file"})
                    continue
            else:
                mod = present_candidates_interactive(name, candidates)
                if not mod:
                    missing.append({"name": name, "reason": "skipped_by_user"})
                    continue
                file_choice = present_files_interactive(mod)
                if not file_choice:
                    missing.append({"name": name, "projectID": mod.get('id'), "reason": "no_file"})
                    continue
            project_id = mod.get("id")
            file_id = file_choice.get("id")
            files_array.append({"projectID": int(project_id), "fileID": int(file_id)})
            print(f"  Selected projectID={project_id}, fileID={file_id}")
            time.sleep(0.2)
        except Exception as e:
            print(f"  ERROR processing {name}: {e}")
            missing.append({"name": name, "error": str(e)})
            continue
    manifest_out = manifest.copy()
    manifest_out["files"] = files_array
    out_path = args.output
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(manifest_out, fh, indent=2)
    print("\nDone. Wrote:", out_path)
    if missing:
        print("\nMissing / skipped entries:")
        print(json.dumps(missing, indent=2))

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Fetch CurseForge project/file IDs and update manifest.json")
    p.add_argument("--modlist", required=True, help="JSON file (array) with mods:{\"name\":\"Create\"}, ...]")
    p.add_argument("--manifest", required=True, help="Path to existing manifest.json (template)")
    p.add_argument("--output", required=True, help="Output manifest path")
    p.add_argument("--non-interactive", action="store_true", help="Run without interactive prompts (for CI)")
    args = p.parse_args()
    main(args)
