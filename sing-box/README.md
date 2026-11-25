# ShellCrash 本地规则集备份

小米路由器 OpenWrt 上 ShellCrash / sing-box 使用的本地规则集备份。

## 说明

- 这些规则集原本在路由器的 `/data/other/ShellCrash/ruleset_sb/`，`AdFull.json` 在 `/data/other/adcustom/`
- 2026-11-25 从线上拉取并托管到 GitHub，用于版本管理和备份
- `manifest.json` 记录了每个文件的 tag、格式、原始路径和大小

## 安全说明（重要）

这是**公开仓库**。密码等敏感信息不会写入仓库：

- 两个同步脚本从环境变量 `ROUTER_PASSWORD` 读取路由器密码，脚本内不含明文密码
- 本地把密码写进 `.env`（已 gitignore，不会上传）；可复制 `.env.example` 修改
- 如果你在别处 clone 这个仓库，需要自己创建 `.env` 或导出环境变量才能运行同步脚本

仓库里只有规则文件本身（域名/IP 列表），不含任何凭证。

## 文件分类

**定制规则（不可用上游覆盖）**
- `Domestic.json` — 国内流量兜底，已并入 9 个小规则集的 214 条域名
- `AdFull.json` — 定制广告拦截
- `push.json` / `X.json` / `meta ai.json` — 专用组，关联手动选择的节点

**核心 DNS / IP 兜底**
- `cn.srs` — DNS 分流规则集（参与 fakeip 判定，不可换源）
- `__geoip_cn.srs` — 国内 IP 段
- `Domestic IPs.json` — 国内 IP 段（另一份）

**标准规则（域名稳定，一般无需更新）**
- AdBlock / PROXY / Special / Google / Microsoft / Apple 系列 / Crypto / Scholar / Speedtest / LAN 等

**留档备份**
- `Google FCM_converted_backup.json` / `Steam_converted_backup.json` — 2026-11-25 转成远程 `.srs` 前的原始本地文件

## 同步到路由器

用 `sync_to_router.py`（在 WorkBuddy 工作区运行）：

```bash
python sync_to_router.py
```

它会把 `sing-box/` 下的文件传回路由器对应路径，并在传输前后做 MD5 校验。

注意：传回后需要在路由器上执行 `start.sh restart` 才会生效。改动配置或规则前务必先备份。

## 从路由器更新本仓库

用 `pull_from_router.py`（在 WorkBuddy 工作区运行），会重新拉取全部文件并更新 manifest。
