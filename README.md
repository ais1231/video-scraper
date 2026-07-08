# Video Scraper — 网页视频下载工具

自动下载 YouTube / Twitter(X) / Bilibili 等主流网站的视频，一键获取最高画质。

## 快速开始

```bash
cd E:\video-scraper
python scraper.py https://www.youtube.com/watch?v=xxxxx
```

## 安装

本工具依赖以下组件，安装脚本已自动处理：

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# ffmpeg（用于合并视频+音频）
# 安装脚本已通过 winget 自动安装
```

### 手动安装 ffmpeg

如果系统未自动安装 ffmpeg，可以从 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 下载，
解压后将 `bin` 目录添加到系统 PATH 中。

## 使用方法

### 下载单个视频

```bash
python scraper.py <视频URL>
```

### 下载多个视频

```bash
python scraper.py <URL1> <URL2> <URL3>
```

### 从文件读取 URL 列表

创建一个文本文件，每行一个 URL：

```
# urls.txt
https://www.youtube.com/watch?v=xxxxx
https://twitter.com/user/status/xxxxx
https://www.bilibili.com/video/BVxxxxx
```

然后：

```bash
python scraper.py --urls-file urls.txt
```

### 指定输出目录

```bash
python scraper.py --output E:\my_videos https://youtu.be/xxxxx
```

### 使用自定义配置

```bash
python scraper.py --config my_config.yaml <URL>
```

## 配置说明

编辑 `config.yaml` 按需修改：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `output_template` | 输出文件路径模板 | `downloads/%(extractor)s/%(title)s.%(ext)s` |
| `ffmpeg_location` | ffmpeg 路径（留空自动搜索 PATH） | `""` |
| `cookies_file` | Netscape 格式 Cookie 文件路径 | `""` |
| `cookies_from_browser` | 自动从浏览器提取 Cookie | `""` |
| `proxy` | 代理地址 | `""` |
| `concurrent_fragments` | 并发分片数 | `3` |
| `retries` | 下载重试次数 | `10` |

### Cookie 认证（Twitter/X 和 Bilibili 必需）

对于需要登录才能查看的视频（如推文中的敏感视频、Bilibili 大会员视频），需要提供 Cookie。

**方法一：自动从浏览器提取（推荐）**

在 `config.yaml` 中设置：

```yaml
cookies_from_browser: chrome   # 可选: chrome, firefox, edge, brave, opera, safari
```

工具会自动从你的浏览器提取登录 Cookie。

**方法二：使用 Cookie 文件**

1. 安装浏览器扩展 [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)
2. 登录目标网站后导出 Cookie 为 Netscape 格式
3. 在 `config.yaml` 中设置：

```yaml
cookies_file: "E:/video-scraper/cookies.txt"
```

## CLI 选项

```
positional arguments:
  urls                  视频 URL（可指定多个）

options:
  -h, --help            显示帮助
  -f, --urls-file FILE  从文件读取 URL 列表
  -c, --config PATH     指定配置文件路径
  -o, --output DIR      输出目录
  --no-history          不记录下载历史
  --force               强制重新下载（跳过历史检查）
```

## 输出目录结构

```
downloads/
├── youtube/
│   └── 视频标题.mp4
├── twitter/
│   └── 推文视频.mp4
└── bilibili/
    └── B站视频.mp4
```

## 常见问题

### Q: 下载中途中断了怎么办？
A: 重新运行相同的命令即可。yt-dlp 会自动断点续传。

### Q: 为什么提示 "Private video" 或 "Sign in to confirm"？
A: 视频需要登录才能访问。请配置 Cookie（见上方说明）。

### Q: 下载的视频没有声音？
A: 某些视频的音视频是分离的，必须有 ffmpeg 才能合并。请确认 ffmpeg 已安装。

### Q: 可以下载 Bilibili 的 4K 视频吗？
A: 可以，但需要 Bilibili 大会员账号的 Cookie。

## 支持的网站

本工具基于 yt-dlp，支持 1000+ 网站，包括但不限于：
- YouTube / YouTube Music
- Twitter / X
- Bilibili
- Instagram / Facebook / TikTok
- 以及更多（[完整列表](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)）
