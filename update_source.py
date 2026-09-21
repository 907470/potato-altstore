import json
import urllib.request
import os

TARGET_REPOS = [
    # Fallout Community Editions
    ("https://api.github.com/repos/alexbatalov/fallout1-ce/releases", "Fallout 1 CE", "com.alexbatalov.fallout1ce", "github"),
    ("https://api.github.com/repos/alexbatalov/fallout2-ce/releases", "Fallout 2 CE", "com.alexbatalov.fallout2ce", "github"),
    
    # Chris Sotraidis' Pad Ports
    ("https://api.github.com/repos/chrissotraidis/sunpad/releases", "SunPad", "com.chrissotraidis.sunpad", "github"),
    ("https://api.github.com/repos/chrissotraidis/spaghettipad/releases", "SpaghettiPad", "com.chrissotraidis.spaghettipad", "github"),
    ("https://api.github.com/repos/chrissotraidis/ctrpad/releases", "CTRPad", "com.chrissotraidis.ctrpad", "github"),
    ("https://api.github.com/repos/chrissotraidis/ballpad/releases", "BallPad", "com.chrissotraidis.ballpad", "github"),
    ("https://api.github.com/repos/chrissotraidis/annepad/releases", "AnnePad", "com.chrissotraidis.annepad", "github"),
    ("https://api.github.com/repos/chrissotraidis/galaxypad/releases", "GalaxyPad", "com.chrissotraidis.galaxypad", "github"),
    ("https://api.github.com/repos/chrissotraidis/paperpad/releases", "PaperPad", "com.chrissotraidis.paperpad", "github"),
    ("https://api.github.com/repos/chrissotraidis/meleepad/releases", "MeleePad", "com.chrissotraidis.meleepad", "github"),
    ("https://api.github.com/repos/chrissotraidis/harkinianpad/releases", "HarkinianPad", "com.chrissotraidis.harkinianpad", "github"),
    ("https://api.github.com/repos/chrissotraidis/kartpad/releases", "KartPad", "com.chrissotraidis.kartpad", "github"),
    ("https://api.github.com/repos/chrissotraidis/bellpad/releases", "BellPad", "com.chrissotraidis.bellpad", "github"),
    ("https://api.github.com/repos/chrissotraidis/bananapad/releases", "BananaPad", "com.chrissotraidis.bananapad", "github"),
    ("https://api.github.com/repos/chrissotraidis/bearbirdpad/releases", "BearBirdPad", "com.chrissotraidis.bearbirdpad", "github"),
    ("https://api.github.com/repos/chrissotraidis/brawlerpad/releases", "BrawlerPad", "com.chrissotraidis.brawlerpad", "github"),
    
    # Emulators & Native Ports
    ("https://git.ryujinx.app/api/v1/repos/projects/MeloNX/releases", "MeloNX", "com.stossy11.MeloNX", "forgejo"),
    ("https://api.github.com/repos/Manic-EMU/ManicEMU/releases", "Manic EMU", "com.manicemu.app", "github"),
    ("https://api.github.com/repos/bryanthaboi/gen1recomp/releases", "Gen1Recomp", "com.theboisclub.gen1recomp", "github"),
    ("https://api.github.com/repos/ARMSX2/ARMSX2/releases", "ARMSX2", "com.armsx2.emu", "github"),
]

def fetch_releases(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        headers['Authorization'] = f'Bearer {token}'

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

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

    for api_url, base_name, base_bundle, repo_type in TARGET_REPOS:
        print(f"Fetching {base_name}...")
        try:
            releases = fetch_releases(api_url)
            if not releases or not isinstance(releases, list):
                failed_apps.append({
                    "name": base_name,
                    "url": api_url,
                    "reason": "No releases or empty payload returned from API."
                })
                continue

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
                
                # Safely handle empty/None release notes
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

                app_entry = {
                    "name": f"{base_name}{suffix}",
                    "bundleIdentifier": f"{base_bundle}{bundle_suffix}",
                    "developerName": "Community / GitHub",
                    "subtitle": f"{base_name} - {channel} Build",
                    "localizedDescription": f"{channel} releases for {base_name}.",
                    "iconURL": "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f3ae.png",
                    "tintColor": "4A90E2" if channel == "Stable" else ("F5A623" if channel == "Pre-release" else "D0021B"),
                    "versions": versions
                }
                parsed_apps.append(app_entry)

        except Exception as err:
            failed_apps.append({
                "name": base_name,
                "url": api_url,
                "reason": f"Request failed: {str(err)}"
            })

    # Output JSON files
    with open("apps.json", "w", encoding="utf-8") as f:
        json.dump({"name": "Potato AltStore Source", "identifier": "com.potato.altstore.source", "apps": parsed_apps}, f, indent=2)

    with open("errors.json", "w", encoding="utf-8") as f:
        json.dump({"failed_count": len(failed_apps), "failed_apps": failed_apps}, f, indent=2)

    print(f"Done! {len(parsed_apps)} channel entries built. {len(failed_apps)} issues logged to errors.json.")

if __name__ == "__main__":
    build_source()
