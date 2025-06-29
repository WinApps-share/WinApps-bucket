import os
import subprocess
import json

base_dir = os.path.dirname(__file__)

for folder in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder)
    if os.path.isdir(folder_path) and not folder.startswith('__'):
        # 查找py脚本
        for file in os.listdir(folder_path):
            if file.endswith('.py'):
                script_path = os.path.join(folder_path, file)
                print(f'Running {script_path}...')
                subprocess.run(['python', script_path], check=True)
        # 获取版本号（读取json文件中的version字段）
        version = None
        for file in os.listdir(folder_path):
            if file.endswith('.json'):
                json_file = os.path.join(folder_path, file)
                try:
                    with open(json_file, encoding='utf-8') as jf:
                        data = json.load(jf)
                        if 'version' in data:
                            version = data['version']
                            break
                except Exception as e:
                    print(f"读取{json_file}失败: {e}")
        # 检查是否有变更
        result = subprocess.run(['git', 'status', '--porcelain', folder_path], capture_output=True, text=True)
        if result.stdout.strip():
            commit_msg = f'【{folder}】: Update to version {version or "unknown"}'
            subprocess.run(['git', 'add', folder_path], check=True)
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            subprocess.run(['git', 'push'], check=True)