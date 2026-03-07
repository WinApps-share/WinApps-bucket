<div align="center">
  <h1>WinApps Scoop bucket</h1>
  <a href="https://github.com/WinApps-share/WinApps-bucket/actions/workflows/ci.yml"><img src="https://github.com/WinApps-share/WinApps-bucket/actions/workflows/ci.yml/badge.svg" /></a>
  <a href="https://github.com/WinApps-share/WinApps-bucket/actions/workflows/excavator.yml"><img src="https://github.com/WinApps-share/WinApps-bucket/actions/workflows/excavator.yml/badge.svg" /></a>
  <img src="https://img.shields.io/github/commit-activity/t/WinApps-share/WinApps-bucket" />
  <a href="https://visitorbadge.io/status?path=https%3A%2F%2Fgithub.com%2FWinApps-share%2FWinApps-bucket"><img src="https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FWinApps-share%2FWinApps-bucket&countColor=%230779b9&style=flat" /></a>
 <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/WinApps-share/WinApps-bucket?style=flat">

</div>

<br />

这是一个 Scoop bucket，其中包含了 [WinApps.cc 网站](https://winapps.cc)内大部分软件。让你无需下载安装包，直接使用 Scoop 命令行安装、更新、卸载软件。

## 使用方法

### 安装 Scoop

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

### 添加 Scoop bucket

```powershell
scoop bucket add winapps https://github.com/WinApps-share/WinApps-bucket.git
```

### 安装软件

```powershell
scoop install winapps/<软件名>
```

### 更新软件

```powershell
scoop update <软件名>
```

### 卸载软件

```powershell
scoop uninstall <软件名>
```

## Star History

<a href="https://www.star-history.com/#WinApps-share/WinApps-bucket&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=WinApps-share/WinApps-bucket&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=WinApps-share/WinApps-bucket&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=WinApps-share/WinApps-bucket&type=date&legend=top-left" />
 </picture>
</a>

