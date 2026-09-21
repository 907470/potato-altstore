import json
import urllib.request
import os
import re

USERNAME = "907470"
REPO_NAME = "potato-altstore"

# Known fallback icons for apps that don't host an icon image directly in their repo
DEFAULT_ICONS = {
    "MeloNX": "https://git.ryujinx.app/projects/MeloNX/raw/branch/master/assets/icon.png",
    "Manic EMU": "https://raw.githubusercontent.com/Manic-EMU/ManicEMU/main/Assets.xcassets/AppIcon.appiconset/1024.png",
    "ARMSX2": "https://raw.githubusercontent.com/ARMSX2/ARMSX2/main/assets/icon.png",
    "Gen1Recomp": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f0cf.png",
    "Fallout 1 CE": "https://raw.githubusercontent.com/alexbatalov/fallout1-ce/main/res/fallout.ico",
    "Fallout 2 CE": "https://raw.githubusercontent.com/alexbatalov/fallout2-ce/main/res/fallout2.ico",
}

TARGET_REPOS = [
    # Fallout Community Editions
    ("https://api.github.com/repos/alexbatalov/fallout1-ce/releases", "Fallout 1 CE", "com.alexbatalov.fallout1ce", "https://api.github.com/repos/alexbatalov/fallout1-ce"),
    ("https://api.github.com/repos/alexbatalov/fallout2-ce/releases", "Fallout 2 CE", "com.alexbatalov.fallout2ce", "https://api.github.com/repos/alexbatalov/fallout2-ce"),
    
    # Chris Sotraidis' Pad Ports
    ("https://api.github.com/repos/chrissotraidis/sunpad/releases", "SunPad", "com.chrissotraidis.sunpad", "https://api.github.com/repos/chrissotraidis/sunpad"),
    ("https://api.github.com/repos/chrissotraidis/spaghettipad/releases", "SpaghettiPad", "com.chrissotraidis.spaghettipad", "https://api.github.com/repos/chrissotraidis/spaghettipad"),
    ("https://api.github.com/repos/chrissotraidis/ctrpad/releases", "CTRPad", "com.chrissotraidis.ctrpad", "https://api.github.com/repos/chrissotraidis/ctrpad"),
    ("https://api.github.com/repos/chrissotraidis/ballpad/releases", "BallPad", "com.chrissotraidis.ballpad", "https://api.github.com/repos/chrissotraidis/ballpad"),
    ("https://api.github.com/repos/chrissotraidis/annepad/releases", "AnnePad", "com.chrissotraidis.annepad", "https://api.github.com/repos/chrissotraidis/annepad"),
    ("https://api.github.com/repos/chrissotraidis/galaxypad/releases", "GalaxyPad", "com.chrissotraidis.galaxypad", "https://api.github.com/repos/chrissotraidis/galaxypad"),
    ("https://api.github.com/repos/chrissotraidis/paperpad/releases", "PaperPad", "com.chrissotraidis.paperpad", "https://api.github.com/repos/chrissotraidis/paperpad"),
    ("https://api.github.com/repos/chrissotraidis/meleepad/releases", "MeleePad", "com.chrissotraidis.meleepad", "https://api.github.com/repos/chrissotraidis/meleepad"),
    ("https://api.github.com/repos/chrissotraidis/harkinianpad/releases", "HarkinianPad", "com.chrissotraidis.harkinianpad", "https://api.github.com/repos/chrissotraidis/harkinianpad"),
    ("https://api.github.com/repos/chrissotraidis/kartpad/releases", "KartPad", "com.chrissotraidis.kartpad", "https://api.github.com/repos/chrissotraidis/kartpad"),
    ("https://api.github.com/repos/chrissotraidis/bellpad/releases", "BellPad", "com.chrissotraidis.bellpad", "https://api.github.com/repos/chrissotraidis/bellpad"),
    ("https://api.github.com/repos/chrissotraidis/bananapad/releases", "BananaPad", "com.chrissotraidis.bananapad", "https://api.github.com/repos/chrissotraidis/bananapad"),
    ("https://api.github.com/repos/chrissotraidis/bearbirdpad/releases", "BearBirdPad", "com.chrissotraidis.bearbirdpad", "https://api.github.com/repos/chrissotraidis/bearbirdpad"),
    ("https://api.github.com/repos/chrissotraidis/brawlerpad/releases", "BrawlerPad", "com.chrissotraidis.brawlerpad", "https://api.github.com/repos/chrissotraidis/brawlerpad"),
    
    # Emulators & Native Ports
    ("https://git.ryujinx.app/api/v1/repos/projects/MeloNX/releases", "MeloNX", "com.stossy11.MeloNX", "https://git.ryujinx.app/api/v1/repos/projects/MeloNX"),
    ("https://api.github.com/repos/Manic-EMU/ManicEMU/releases", "Manic EMU", "com.manicemu.app", "https://api.github.com/repos/Manic-EMU/ManicEMU"),
    ("https://api.github.com/repos/bryanthaboi/gen1recomp/releases", "Gen1Recomp", "com.theboisclub.gen1recomp", "https://api.github.com/repos/bryanthaboi/gen1recomp"),
    ("https://api.github.com/repos/ARMSX2/ARMSX2/releases", "ARMSX2", "com.armsx2.emu", "https://api.github.com/repos/ARMSX2/ARMSX2"),
]

def fetch_json(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers['Authorization'] = f'Bearer {token}'

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def find_app_icon(base_name, repo_api_url, releases):
    # 1. Check override table first
    if base_name in DEFAULT_ICONS:
        return DEFAULT_ICONS[base_name]

    # 2. Check if an icon asset is attached directly to the latest release
    for rel in releases:
        assets = rel.get("assets", []) or []
        for asset in assets:
            name = str(asset.get("name") or "").lower()
            if any(ext in name for ext in [".png", ".jpg", ".jpeg"]) and "icon" in name:
                return asset.get("browser_download_url") or asset.get("download_url")

    # 3. Check GitHub/Forgejo Repository Details for Owner Avatar or Repo Assets
    try:
        repo_info = fetch_json(repo_api_url)
        if isinstance(repo_info, dict):
            # Check owner avatar as a clean fallback for pad ports
            owner = repo_info.get("owner", {}) or repo_info.get("repo", {}).get("owner", {})
            avatar_url = owner.get("avatar_url")
            if avatar_url:
                return avatar_url
    except Exception:
        pass

    # 4. Default fallback icon
    return "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3ae.png"

def classify_channel(release):
    tag = str(release.get("tag_name") or "").lower()
    name = str(release.get("name") or "").lower()
    is_prerelease = bool(release.get("prerelease", False))

    if "nightly" in tag or "nightly" in name:
        return "Nightly"
    elif is_prerelease or "preview" in tag or "experimental" in tag:
        return "Pre-release"
    else:
        return "Stable"

def find_ipa_asset(release):
    if not isinstance(release, dict):
        return None, 0
    assets = release.get("assets", []) or []
    for asset in assets:
        if isinstance(asset, dict) and str(asset.get("name") or "").endswith(".ipa"):
            url = asset.get("browser_download_url") or asset.get("download_url")
            return url, asset.get("size", 0)
    return None, 0

def build_source():
    parsed_apps = []
    failed_apps = []

    for api_url, base_name, base_bundle, repo_api_url in TARGET_REPOS:
        print(f"Fetching {base_name}...")
        try:
            releases = fetch_json(api_url)
            if not releases or not isinstance(releases, list):
                failed_apps.append({
                    "name": base_name,
                    "url": api_url,
                    "reason": "No releases or empty payload returned from API."
                })
                continue

            icon_url = find_app_icon(base_name, repo_api_url, releases)
            channel_buckets = {"Stable": [], "Pre-release": [], "Nightly": []}
            found_any_ipa = False

            for rel in releases:
                ipa_url, size = find_ipa_asset(rel)
                if not ipa_url:
                    continue

                found_any_ipa = True
                channel = classify_channel(rel)
                version = str(rel.get("tag_name") or "1.0.0").lstrip("v")
                raw_date = rel.get("published_at") or rel.get("created_at") or "2026-01-01"
                date = str(raw_date).split("T")[0]
                notes = str(rel.get("body") or "Updated release.")

                channel_buckets[channel].append({
                    "version": version,
                    "date": date,
                    "downloadURL": ipa_url,
                    "size": size,
                    "localizedDescription": f"[{channel}] {notes[:300]}"
                })

            if not found_any_ipa:
                failed_apps.append({
                    "name": base_name,
                    "url": api_url,
                    "reason": "Releases found, but none contained a valid .ipa file asset."
                })
                continue

            for channel, versions in channel_buckets.items():
                if not versions:
                    continue

                suffix = "" if channel == "Stable" else f" ({channel})"
                bundle_suffix = "" if channel == "Stable" else f".{channel.lower().replace('-', '')}"
                latest_ver = versions[0]

                app_entry = {
                    "name": f"{base_name}{suffix}",
                    "bundleIdentifier": f"{base_bundle}{bundle_suffix}",
                    "developerName": "Community / GitHub",
                    "subtitle": f"{base_name} - {channel} Build",
                    "localizedDescription": f"{channel} releases for {base_name}.",
                    "iconURL": icon_url,
                    "tintColor": "4A90E2" if channel == "Stable" else ("F5A623" if channel == "Pre-release" else "D0021B"),
                    "version": latest_ver["version"],
                    "versionDate": latest_ver["date"],
                    "versionDescription": latest_ver["localizedDescription"],
                    "downloadURL": latest_ver["downloadURL"],
                    "size": latest_ver["size"],
                    "versions": versions
                }
                parsed_apps.append(app_entry)

        except Exception as err:
            failed_apps.append({
                "name": base_name,
                "url": api_url,
                "reason": f"Request failed: {str(err)}"
            })

    # Top-Level Root Object
    full_source = {
        "name": "Potato AltStore Source",
        "identifier": "com.potato.altstore.source",
        "subtitle": "Community Apps & Emulators",
        "description": "Auto-updated iOS source for emulators, ports, and tools.",
        "iconURL": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3ae.png",
        "website": f"https://{USERNAME}.github.io/{REPO_NAME}/",
        "apps": parsed_apps
    }

    with open("apps.json", "w", encoding="utf-8") as f:
        json.dump(full_source, f, indent=2)

    with open("errors.json", "w", encoding="utf-8") as f:
        json.dump({"failed_count": len(failed_apps), "failed_apps": failed_apps}, f, indent=2)

    print(f"Done! Updated apps.json with app repository icons.")

if __name__ == "__main__":
    build_source()
