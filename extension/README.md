# 115 Auto Save · Chrome Extension

基于 [WXT](https://wxt.dev) + Vue 3 + TypeScript 构建的 Chrome MV3 浏览器扩展，将油猴脚本 [`../userscript/115-auto-save.user.js`](../userscript/115-auto-save.user.js) 的"输入访问码 → 转存 → 确认目录"三步自动化逻辑迁移到正式扩展。

> 已上架：[Chrome 应用商店 · 115 转存助手](https://chromewebstore.google.com/detail/115-%E8%BD%AC%E5%AD%98%E5%8A%A9%E6%89%8B/akokmklnfgopbmlkpmjjligliekijfla)

## 功能

- 内容脚本：在 `https://115cdn.com/s/*` 自动完成三步点击
- 欢迎页：首次安装弹出，介绍工作原理
- 设置页：开关、延迟微调、主题（auto/light/dark）、语言（auto/zh/en）
- 中英国际化：商店元信息（`_locales/`）+ 扩展内 UI（运行时可切换）
- 主题适配：基于 CSS Variables + `prefers-color-scheme`，无运行时样式库

## 开发

```bash
pnpm install        # 安装依赖（postinstall 会触发 wxt prepare 生成类型）
pnpm dev            # Chrome 开发模式（自动 HMR）
pnpm dev:firefox    # Firefox 开发模式
pnpm build          # 生产构建
pnpm zip            # 产出可上架 Chrome Web Store 的 zip 包
```

## 质量检查

```bash
pnpm lint           # ESLint
pnpm lint:fix       # ESLint --fix
pnpm lint:tsc       # vue-tsc --noEmit
```

## 目录结构

```
extension/
├── wxt.config.ts                  # WXT 配置
├── src/
│   ├── entrypoints/
│   │   ├── content.ts             # 内容脚本（三步点击）
│   │   ├── background.ts          # onInstalled 打开欢迎页
│   │   ├── welcome/               # 欢迎页（首次安装弹出）
│   │   └── options/               # 设置页（manifest options_ui）
│   ├── components/                # LangSwitch / ThemeToggle
│   ├── composables/               # useI18n / useTheme
│   ├── locales/                   # zh_CN.json / en.json
│   ├── styles/theme.css           # CSS Variables 主题
│   └── utils/settings.ts          # chrome.storage.sync 封装
├── design/icon.svg                # 图标唯一矢量源（96×96 图形）
├── scripts/build-icons.py         # 生成 16/32/48/128 PNG（128 自动补 16px 透明内边距）
├── public/icon/                   # ↑ 脚本产物，勿手工替换
└── .output/                       # 构建产物（gitignore）
```

## 上架须知

- `manifest.name` 与 `manifest.description` 使用 `__MSG_*__` 引用，Chrome Web Store 会按用户浏览器语言自动展示对应翻译
- 128×128 图标必须满足「实际图形 96×96 + 四周各 16px 透明内边距」，由 `python scripts/build-icons.py` 生成，详见 [`store-assets/README.md`](./store-assets/README.md)
- 需在商店后台准备中英两份"商品详情页"内容（标题/描述/截图）
- 仅声明了 `storage` 权限和单一域名 `host_permissions`，过审难度低

## 版本号约定

扩展（`package.json` 的 `version`）与油猴脚本（`../userscript/115-auto-save.user.js` 头部 `@version`）**保持同步**：每次发布时两端必须升到同一版本号。

发布前 checklist：

1. 同步修改 `extension/package.json` 与 `userscript/115-auto-save.user.js` 的版本号
2. 在 `extension/` 下执行 `pnpm zip` 生成 `.output/115-auto-save-extension-<version>-chrome.zip`
3. 上传 Chrome Web Store + 同步更新 Greasy Fork 上的脚本
