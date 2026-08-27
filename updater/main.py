import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent


def run(command):
    return subprocess.run(command, cwd=ROOT_DIR, check=True)


def changed_paths(name):
    paths = [f"bucket/{name}.json", f"updater/{name}"]
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    return paths if result.stdout.strip() else []


def restore_paths(name):
    paths = [f"bucket/{name}.json", f"updater/{name}"]
    run(["git", "restore", "--staged", "--worktree", "--", *paths])


def read_version(name):
    json_file = ROOT_DIR / "bucket" / f"{name}.json"
    if not json_file.exists():
        return None

    try:
        with json_file.open(encoding="utf-8-sig") as file:
            return json.load(file).get("version")
    except Exception as error:
        print(f"读取 {json_file} 失败: {error}")
        return None


def discover_updaters():
    updaters = []
    for folder in sorted(BASE_DIR.iterdir()):
        if not folder.is_dir() or folder.name.startswith("__"):
            continue
        scripts = sorted(folder.glob("*.py"))
        if scripts:
            updaters.append((folder.name, scripts))
    return updaters


def write_report(report_path, results):
    if not report_path:
        return

    app_results = [item for item in results if not item.get("global")]
    report = {
        "checked": len(app_results),
        "succeeded": sum(item["status"] == "success" for item in app_results),
        "updated": sum(item["status"] == "success" and item["updated"] for item in app_results),
        "unchanged": sum(item["status"] == "success" and not item["updated"] for item in app_results),
        "failed": sum(item["status"] == "failed" for item in results),
        "results": results,
    }
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", help="将更新结果写入指定的 JSON 文件")
    args = parser.parse_args()

    os.chdir(ROOT_DIR)
    results = []

    try:
        run(["git", "pull"])

        for name, scripts in discover_updaters():
            print(f"\n::group::检查 {name}")
            try:
                for script in scripts:
                    print(f"Running {script}...")
                    run([sys.executable, str(script)])

                paths = changed_paths(name)
                version = read_version(name)
                if paths:
                    commit_message = f'{name}: Update to version {version or "unknown"}'
                    run(["git", "add", "--", *paths])
                    run(["git", "commit", "-m", commit_message, "--", *paths])

                results.append(
                    {
                        "name": name,
                        "status": "success",
                        "updated": bool(paths),
                        "version": version,
                    }
                )
            except Exception as error:
                print(f"::warning title={name} 更新失败::{error}")
                try:
                    restore_paths(name)
                except Exception as restore_error:
                    print(f"::warning title={name} 回滚失败::{restore_error}")
                results.append(
                    {
                        "name": name,
                        "status": "failed",
                        "updated": False,
                        "error": str(error),
                    }
                )
            finally:
                print("::endgroup::")

        if any(item["status"] == "success" and item["updated"] for item in results):
            try:
                run(["git", "push"])
            except Exception as error:
                print(f"::error title=更新提交推送失败::{error}")
                results.append(
                    {
                        "name": "push",
                        "status": "failed",
                        "updated": False,
                        "global": True,
                        "error": str(error),
                    }
                )
    except Exception as error:
        print(f"::error title=更新程序执行失败::{error}")
        results.append(
            {
                "name": "updater",
                "status": "failed",
                "updated": False,
                "global": True,
                "error": str(error),
            }
        )
    finally:
        write_report(args.report, results)

    failed_names = [item["name"] for item in results if item["status"] == "failed"]
    app_results = [item for item in results if not item.get("global")]
    succeeded = sum(item["status"] == "success" for item in app_results)
    print(f"检查 {len(app_results)} 个，成功 {succeeded} 个，失败 {len(failed_names)} 个")
    if failed_names:
        print(f"失败项目: {', '.join(failed_names)}")
    return 1 if any(item.get("global") for item in results if item["status"] == "failed") else 0


if __name__ == "__main__":
    raise SystemExit(main())
