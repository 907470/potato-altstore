import json
import urllib.request
import re

# Format: (GitHub/Forgejo API endpoint, App Name Base, Bundle Identifier Base, Type)
# Type options: "github" or "forgejo"
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
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error reading {url}: {e}")
        return []

def classify_channel(release):
    """Categorizes release into 'stable', 'prerelease', or 'nightly'."""
    tag = release.get("tag_name", "").lower()
    name = release.get("name", "").lower()
    is_prerelease = release.get("prerelease", False)

    if "nightly" in tag or "nightly" in name:
        return "Nightly"
    elif is_prerelease or "preview" in tag or "experimental" in tag:
        return "Pre-release"
    else:
        return "Stable"

def find_ipa_asset(release):
    """Finds the first .ipa download link inside release assets."""
    assets = release.get("assets", [])
    for asset in assets:
        if asset.get("name", "").endswith(".ipa"):
            # Normalize download URL across GitHub and Forgejo
            url = asset.get("browser_download_url") or asset.get("download_url")
            return url, asset.get("size", 0)
    return None, 0

def build_source():
    parsed_apps = []

    for api_url, base_name, base_bundle, repo_type in TARGET_REPOS:
        print(f"Processing {base_name}...")
        releases = fetch_releases(api_url)
        if not releases:
            continue

        # Group releases into channels: Stable, Pre-release, Nightly
        channel_buckets = {"Stable": [], "Pre-release": [], "Nightly": []}

        for rel in releases:
            ipa_url, size = find_ipa_asset(rel)
            if not ipa_url:
                continue

            channel = classify_channel(rel)
            version = rel.get("tag_name", "1.0.0").lstrip("v")
            date = rel.get("published_at", rel.get("created_at", "2026-01-01")).split("T")[0]
            notes = rel.get("body", "Updated release.")

            channel_buckets[channel].append({
                "version": version,
                "date": date,
                "downloadURL": ipa_url,
                "size": size,
                "localizedDescription": f"[{channel}] {notes[:300]}" # Limit length
            })

        # Generate separate app entries for each channel found
        for channel, versions in channel_buckets.items():
            if not versions:
                continue

            # Append channel tag to name and bundle ID if not standard stable
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

    full_source = {
        "name": "Custom Game & Emulator Collection",
        "identifier": "com.custom.ios.source",
        "apps": parsed_apps
    }

    with open("apps.json", "w", encoding="utf-8") as f:
        json.dump(full_source, f, indent=2)

    print(f"Done! Generated apps.json with {len(parsed_apps)} total channel entries.")

if __name__ == "__main__":
    build_source()
