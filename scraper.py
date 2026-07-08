#!/usr/bin/env python3
"""
Video Scraper — 网页视频下载工具
支持 YouTube / Twitter(X) / Bilibili 等主流网站，自动下载最高画质。
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Windows 控制台 UTF-8 支持
if sys.platform == "win32":
    import _locale
    _locale._getdefaultlocale = lambda *args: ("zh_CN", "UTF-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import yaml
import yt_dlp


def load_config(config_path: str = "") -> dict:
    """加载配置文件，返回配置字典"""
    default_config = {
        "output_template": "downloads/%(extractor)s/%(title)s.%(ext)s",
        "ffmpeg_location": "",
        "cookies_file": "",
        "cookies_from_browser": "",
        "proxy": "",
        "concurrent_fragments": 3,
        "retries": 10,
    }

    config = default_config.copy()

    # 查找配置文件
    search_paths = [
        config_path,
        "config.yaml",
        Path(__file__).parent / "config.yaml",
    ]

    for path in search_paths:
        if path and Path(path).exists():
            with open(path, encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if loaded:
                    config.update(loaded)
            break

    return config


def load_history(history_path: str = "history.json") -> list:
    """加载下载历史"""
    try:
        if Path(history_path).exists():
            with open(history_path, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_history(history: list, history_path: str = "history.json"):
    """保存下载历史"""
    # 只保留最近 1000 条记录
    history = history[-1000:]
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def is_already_downloaded(url: str, history: list) -> bool:
    """检查 URL 是否已经下载过"""
    return any(entry.get("url") == url and entry.get("status") == "completed" for entry in history)


def progress_hook(site_name: str = ""):
    """创建进度回调函数"""
    last_time = {"time": 0}

    def hook(d):
        if d["status"] == "downloading":
            # 限频输出，每秒最多更新 4 次
            now = time.time()
            if now - last_time["time"] < 0.25:
                return
            last_time["time"] = now

            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed", 0) or 0
            eta = d.get("eta", 0) or 0

            if total > 0:
                pct = downloaded / total * 100
                # 简单进度条
                bar_len = 30
                filled = int(bar_len * downloaded / total)
                bar = "#" * filled + "-" * (bar_len - filled)

                speed_str = _format_speed(speed)
                eta_str = _format_eta(eta)
                sys.stdout.write(
                    f"\r{site_name}  [{bar}] {pct:.1f}%  {speed_str}  ETA {eta_str}"
                )
                sys.stdout.flush()
        elif d["status"] == "finished":
            print(f"\r{site_name}  下载完成，正在合并处理...")

    return hook


def _format_speed(speed: float) -> str:
    """格式化速度显示"""
    if speed >= 1024 * 1024:
        return f"{speed / 1024 / 1024:.1f} MB/s"
    elif speed >= 1024:
        return f"{speed / 1024:.1f} KB/s"
    return f"{speed:.0f} B/s"


def _format_eta(eta: int) -> str:
    """格式化剩余时间"""
    if eta >= 3600:
        return f"{eta // 3600}h{(eta % 3600) // 60}m"
    elif eta >= 60:
        return f"{eta // 60}m{eta % 60}s"
    return f"{eta}s"


def get_extractor_name(url: str) -> str:
    """从 URL 猜测网站名（用于显示）"""
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "YouTube"
    if "twitter.com" in url_lower or "x.com" in url_lower:
        return "Twitter/X"
    if "bilibili.com" in url_lower or "b23.tv" in url_lower:
        return "Bilibili"
    return "Video"


def download_video(url: str, config: dict, output_dir: str = "") -> dict:
    """
    下载单个视频，自动选择最高画质。

    参数:
        url: 视频 URL
        config: 配置字典
        output_dir: 输出目录（绝对路径）

    返回:
        dict: {"status": "completed"|"error", "title": str, "url": str, "error_msg": str}
    """
    site_name = get_extractor_name(url)

    # 构建输出模板
    if output_dir:
        output_template = os.path.join(output_dir, "%(extractor)s", "%(title)s.%(ext)s")
    else:
        output_template = config.get("output_template", "downloads/%(extractor)s/%(title)s.%(ext)s")

    # 确保输出目录存在
    out_dir = Path(output_template).parent
    if str(out_dir) != ".":
        os.makedirs(out_dir, exist_ok=True)

    # yt-dlp 选项
    ydl_opts = {
        # 格式选择：最高画质视频+最佳音频，或最佳单一文件
        "format": "bv*+ba/b",  # best video + best audio, fallback to best single file
        "format_sort": [       # 优先排序条件
            "res:2160",         # 4K 优先
            "fps",              # 高帧率优先
            "codec:h264",       # H264 优先（兼容性最好）
            "quality",          # 按质量
            "size",             # 文件大小
        ],
        "merge_output_format": "mkv",  # 合并为 mkv（兼容FMP4）
        "fixup": "never",             # 仅复制流，不动编码
        "outtmpl": output_template,
        "progress_hooks": [progress_hook(site_name)],
        "retries": config.get("retries", 10),
        "fragment_retries": config.get("retries", 10),
        "concurrent_fragments": config.get("concurrent_fragments", 1),
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    # 可选配置
    if config.get("ffmpeg_location"):
        ydl_opts["ffmpeg_location"] = config["ffmpeg_location"]
    if config.get("cookies_file"):
        ydl_opts["cookiefile"] = config["cookies_file"]
    if config.get("cookies_from_browser"):
        cf_browser = config["cookies_from_browser"]
        # 支持 chrome::path 格式 → 解析为元组
        if "::" in cf_browser:
            parts = cf_browser.split("::", 1)
            ydl_opts["cookiesfrombrowser"] = (parts[0], parts[1])
        else:
            ydl_opts["cookiesfrombrowser"] = (cf_browser,)
    if config.get("proxy"):
        ydl_opts["proxy"] = config["proxy"]

    result = {
        "url": url,
        "title": "",
        "site": site_name,
        "status": "error",
        "error_msg": "",
        "filepath": "",
        "time": datetime.now().isoformat(),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n[Fetching] {site_name} video info: {url}")

            # 获取视频信息
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError("无法获取视频信息")

            title = info.get("title", "Unknown")
            duration = info.get("duration", 0)
            result["title"] = title

            # 显示视频信息
            print(f"   标题: {title}")
            if duration:
                print(f"   时长: {_format_eta(duration)}")
            print(f"   站点: {info.get('extractor', site_name)}")
            print(f"\n[Downloading]...\n")

            # 执行下载
            ydl.download([url])

            # 下载完成后获取实际文件路径
            result["status"] = "completed"
            result["filepath"] = str(Path(output_template.format(
                extractor=info.get("extractor", site_name),
                title=title,
                ext="mp4"
            )).resolve())

            print(f"\n[Done] {title}")

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        result["error_msg"] = f"下载错误: {error_msg}"
        print(f"\n[Error] {result['error_msg']}")

    except Exception as e:
        error_msg = str(e)
        result["error_msg"] = f"未知错误: {error_msg}"
        print(f"\n[Error] {result['error_msg']}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Video Scraper — 网页视频下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scraper.py https://www.youtube.com/watch?v=xxxxx
  python scraper.py https://twitter.com/user/status/xxxxx
  python scraper.py https://www.bilibili.com/video/BVxxxxx
  python scraper.py --urls urls.txt
  python scraper.py --output E:\\my_videos https://youtu.be/xxxxx
        """,
    )
    parser.add_argument("urls", nargs="*", help="视频 URL（可指定多个）")
    parser.add_argument("--urls-file", "-f", dest="urls_file", help="从文件读取 URL 列表（每行一个）")
    parser.add_argument("--config", "-c", default="", help="配置文件路径")
    parser.add_argument("--output", "-o", default="", help="输出目录（覆盖配置文件中的 output_template）")
    parser.add_argument("--no-history", action="store_true", help="不记录下载历史")
    parser.add_argument("--force", action="store_true", help="强制重新下载（跳过历史检查）")

    args = parser.parse_args()

    # 收集所有 URL
    urls = list(args.urls)

    if args.urls_file:
        path = Path(args.urls_file)
        if path.exists():
            with open(path, encoding="utf-8") as f:
                file_urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            urls.extend(file_urls)
        else:
            print(f"[Error] URL file not found: {args.urls_file}")
            sys.exit(1)

    if not urls:
        parser.print_help()
        print("\n[Error] Please provide at least one URL")
        sys.exit(1)

    # 加载配置
    config = load_config(args.config)

    # 处理输出目录
    output_dir = args.output or ""

    # 加载历史
    history_dir = Path(__file__).parent
    history_path = str(history_dir / "history.json")
    history = load_history(history_path) if not args.no_history else []

    # 逐个下载
    success_count = 0
    fail_count = 0

    for i, url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"  任务 {i}/{len(urls)}")

        # 历史去重
        if not args.force and is_already_downloaded(url, history):
            print(f"[Skipped] already downloaded (use --force to re-download)")
            continue

        result = download_video(url, config, output_dir)

        # 记录历史
        history.append(result)

        if result["status"] == "completed":
            success_count += 1
        else:
            fail_count += 1

        print(f"{'='*60}")

    # 保存历史
    if not args.no_history:
        save_history(history, history_path)

    # 输出汇总
    total = len(urls)
    print(f"\n[Summary] Total: {total} tasks")
    print(f"   [OK] Success: {success_count}")
    print(f"   [FAIL] Failed: {fail_count}")
    if fail_count > 0:
        print(f"\n失败的 URL:")
        for entry in history:
            if entry.get("status") == "error":
                print(f"   [FAIL] {entry['url']}: {entry.get('error_msg', '')}")

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
