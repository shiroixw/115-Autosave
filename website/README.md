# 115 Auto Save · Website

基于 [Astro 6](https://astro.build) + [Tailwind CSS 4](https://tailwindcss.com) 的静态官网，部署到 [Vercel](https://vercel.com)。

## 设计原则

- 黑白主色 + 单一品牌强调色（115 蓝 `#1B7AE0`）
- 不使用通用紫色渐变，仅在 Hero 顶部使用一处低饱和度径向高光
- 1px 描边卡片 + 大字标题，参考 Linear / Resend / shadcn.com 的克制极简风
- 跟随系统亮/暗主题，可手动切换（持久化到 `localStorage`）
- `public/icon-{32,128}.png` 与扩展图标同源，由 [`../extension/scripts/build-icons.py`](../extension/scripts/build-icons.py) 生成，不要手工替换

## 国际化

- 默认路由 `/` 为中文（默认 locale）
- `/en/` 为英文版本
- 文案集中在 `src/i18n/{zh,en}.ts`
- Astro 内置 `i18n` 配置生成 `<link rel="alternate" hreflang>`

## 开发

```bash
pnpm install
pnpm dev          # 启动开发服务器（http://localhost:4321）
pnpm build        # 静态构建到 dist/
pnpm preview      # 预览构建产物
pnpm lint:tsc     # astro check（类型 + 组件 props 校验）
```

## 部署

直接 push 后由 Vercel 自动构建。Vercel 会识别 Astro，无需额外配置。
