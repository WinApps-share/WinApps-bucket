import requests
import hashlib
import json
import re
import os
import pefile  # pip install pefile

ITUNES_JSON = r'bucket\itunes.json'
URL32 = 'https://www.apple.com/itunes/download/win32'
URL64 = 'https://www.apple.com/itunes/download/win64'
TMP32 = r'updater/itunes/itunes32.exe'
TMP64 = r'updater/itunes/itunes64.exe'
ETAG_FILE = r'updater/itunes/itunes.etag'

def get_final_url(url):
    print(f"[INFO] Resolving final URL for: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    resp = requests.head(url, allow_redirects=True, headers=headers)
    print(f"[INFO] Final URL: {resp.url}")
    return resp.url

def download(url, filename):
    print(f"[INFO] Downloading {url} -> {filename}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    with requests.get(url, stream=True, headers=headers) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"[INFO] Downloaded {filename}")

def get_sha256(filename):
    print(f"[INFO] Calculating SHA256 for {filename}")
    h = hashlib.sha256()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    sha = h.hexdigest()
    print(f"[INFO] SHA256 for {filename}: {sha}")
    return sha

def get_file_version(filename):
    print(f"[INFO] Extracting version from {filename}")
    pe = pefile.PE(filename)
    version = None
    for fileinfo in pe.FileInfo:
        for entry in fileinfo:
            if entry.Key == b'StringFileInfo':
                for st in entry.StringTable:
                    version = st.entries.get(b'ProductVersion').decode()
                    print(f"[INFO] Version found: {version}")
                    break
    pe.close()  # 释放文件句柄，避免 PermissionError
    if not version:
        print("[WARN] Version not found!")
    return version

def update_json(json_path, url32, url64, hash32, hash64, version):
    print(f"[INFO] Updating JSON: {json_path}")
    # 读取 JSON 内容，保留注释
    with open(json_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    # 去除注释行，拼接为字符串
    json_str = ''.join([line for line in lines if not line.strip().startswith('//')])
    data = json.loads(json_str)
    # 直接替换字段
    data['version'] = version
    if 'architecture' in data:
        if '64bit' in data['architecture']:
            data['architecture']['64bit']['url'] = url64
            data['architecture']['64bit']['hash'] = hash64
        if '32bit' in data['architecture']:
            data['architecture']['32bit']['url'] = url32
            data['architecture']['32bit']['hash'] = hash32
    # 写回文件（带缩进，utf-8），并保留原文件末尾的空行
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write('\n')  # 总是补一个换行
    print(f'[INFO] Updated {json_path} to version {version}')

def get_url_etag(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    resp = requests.head(url, allow_redirects=True, headers=headers)
    return resp.headers.get('ETag')

def should_update(url, etag_file):
    new_etag = get_url_etag(url)
    if not new_etag:
        print('[WARN] No ETag found, will always update.')
        return True
    if os.path.exists(etag_file):
        with open(etag_file, 'r', encoding='utf-8') as f:
            old_etag = f.read().strip()
        if old_etag == new_etag:
            print('[INFO] ETag not changed, skip update.')
            return False
    with open(etag_file, 'w', encoding='utf-8') as f:
        f.write(new_etag)
        f.write('\n')
    print('[INFO] ETag changed or first run, will update.')
    return True

def main():
    print("[INFO] Start updating iTunes bucket...")
    if not should_update(URL32, ETAG_FILE):
        return
    real_url32 = get_final_url(URL32)
    real_url64 = get_final_url(URL64)
    download(real_url32, TMP32)
    download(real_url64, TMP64)
    hash32 = get_sha256(TMP32)
    hash64 = get_sha256(TMP64)
    version = get_file_version(TMP32)
    update_json(ITUNES_JSON, real_url32, real_url64, hash32, hash64, version)
    os.remove(TMP32)
    os.remove(TMP64)
    print("[INFO] Temporary files removed.")
    print("[INFO] All done.")

if __name__ == '__main__':
    main()
