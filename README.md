# Video Scraper — 夸克视频下载工具

**专为夸克浏览器设计** · 仅支持 **YouTube / Twitter(X) / Bilibili** 三个平台

自动下载视频，一键获取最高画质。

## 快速开始

```bash
python scraper.py https://www.youtube.com/watch?v=xxxxx
python scraper.py https://x.com/user/status/xxxxx
python scraper.py https://www.bilibili.com/video/BVxxxxx
```

## 安装

```bash
pip install -r requirements.txt
```

## Cookie 配置（夸克浏览器）

Twitter/X 和 Bilibili 的部分视频需要登录才能下载。

### 首次使用

1. 在夸克里登录好 Twitter / Bilibili
2. **完全关闭夸克浏览器**（右键任务栏 → 退出）
3. 运行一次 Cookie 导出：

```bash
python tools\export_cookies.py
```

4. 之后夸克开着也能正常下载了

### Cookie 过期后

如果下载时报认证错误，重新跑一次上面的导出命令即可。

## 使用方法

```bash
# 下载单个视频
python scraper.py <视频URL>

# 下载多个
python scraper.py <URL1> <URL2>

# 从文件批量下载
python scraper.py --urls-file urls.txt

# 指定输出位置
python scraper.py --output D:\视频 <URL>
```

## 支持的站点

- **YouTube** — 最高 4K
- **Twitter / X** — 最高画质
- **Bilibili** — 需大会员 Cookie

其他网站不支持，程序会直接拒绝。

## 配置

编辑 `config.yaml`：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `cookies_file` | Cookie 文件路径 | `cookies.txt` |
| `proxy` | 代理地址 | `""` |
| `download_dir` | 下载目录 | `downloads/` |
| `concurrent_fragments` | 并发数 | `1` |
| `retries` | 重试次数 | `10` |

## 输出目录

```
downloads/
├── youtube/
├── twitter/
└── bilibili/
```

---

> 本仓库所有代码由 [Vibe Coding](https://en.wikipedia.org/wiki/Vibe_coding) 完成，
> 懒得折腾其他网站，怕又有 bug。
> 如果想尝试新增站点，自行修改代码，后果自负。
