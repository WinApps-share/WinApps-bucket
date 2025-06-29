import os
import subprocess
import json

base_dir = os.path.dirname(__file__)
root_dir = os.path.abspath(os.path.join(base_dir, ".."))

# 拉取最新代码
subprocess.run(['git', 'pull'], check=True)

for folder in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder)
    if os.path.isdir(folder_path) and not folder.startswith('__'):
        # 查找py脚本
        for file in os.listdir(folder_path):
            if file.endswith('.py'):
                script_path = os.path.join(folder_path, file)
                print(f'Running {script_path}...')
                subprocess.run(['python', script_path], check=True)
        # 获取版本号（读取 bucket/itunes.json 的 version 字段）
        version = None
        json_file = os.path.join(root_dir, 'bucket', 'itunes.json')
        if os.path.exists(json_file):
            try:
                with open(json_file, encoding='utf-8') as jf:
                    data = json.load(jf)
                    if 'version' in data:
                        version = data['version']
            except Exception as e:
                print(f"读取{json_file}失败: {e}")
        # 检查根路径是否有变更
        result = subprocess.run(['git', 'status', '--porcelain', root_dir], capture_output=True, text=True)
        if result.stdout.strip():
            commit_msg = f'{folder}: Update to version {version or "unknown"}'
            subprocess.run(['git', 'add', root_dir], check=True)
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            subprocess.run(['git', 'push'], check=True)
