import requests
import json
import hashlib
from pathlib import Path

def fetch_edge_info(architecture):
    """
    获取指定架构的 Edge 最新版本、下载链接和哈希（直接读取API中的哈希）
    """
    arch_map = {"64bit": "x64", "32bit": "x86", "arm64": "arm64"}
    arch_api = arch_map[architecture]
    url = "https://edgeupdates.microsoft.com/api/products"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    stable_product = next(item for item in data if item.get("Product") == "Stable")
    releases = stable_product.get("Releases", [])
    release = next(
        (r for r in releases if r.get("Platform") == "Windows" and r.get("Architecture") == arch_api),
        None
    )
    if not release:
        raise ValueError(f"No Windows {arch_api} release found")
    version = release.get("ProductVersion")
    artifact = next(
        (a for a in release.get("Artifacts", []) if a.get("ArtifactName") == "msi"),
        None
    )
    if not artifact:
        raise ValueError(f"No MSI artifact found for Windows {arch_api} release")
    download_url = artifact.get("Location")
    hash_value = artifact.get("Hash", "").upper()
    if not hash_value:
        raise ValueError(f"No hash found in API for Windows {arch_api} release")
    return {"version": version, "url": download_url, "hash": hash_value}

def update_edge_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"正在更新 {json_path} ...")
    for arch in ["64bit", "32bit", "arm64"]:
        print(f"获取 {arch} 信息 ...")
        info = fetch_edge_info(arch)
        print(f"{arch} url: {info['url']}")
        print(f"{arch} hash: {info['hash']}")
        data["architecture"][arch]["url"] = info["url"]
        data["architecture"][arch]["hash"] = info["hash"]
        data["version"] = info["version"]  # 保证主版本号同步
    print(f"全部信息获取完毕，正在写入文件 ...")
    # 格式化输出，末尾保留空行
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")
    print("更新完成！")

if __name__ == "__main__":
    update_edge_json(r"bucket\edge.json")
