# uni-app and Taro

Verified against: Taro 4.2.1 (scaffolded locally), uni-app documentation at the pinned
commit of `dcloudio/uni-app`.

## Contents

- [Picking one](#picking-one)
- [uni-app conditional compilation](#uni-app-conditional-compilation)
- [The typo that ships the wrong branch](#the-typo-that-ships-the-wrong-branch)
- [uni-app project shape](#uni-app-project-shape)
- [uni-app and glass-easel](#uni-app-and-glass-easel)
- [Taro project shape](#taro-project-shape)
- [Taro platform branching](#taro-platform-branching)
- [Sizing: rpx, designWidth, pxtransform](#sizing-rpx-designwidth-pxtransform)
- [What the abstraction does not hide](#what-the-abstraction-does-not-hide)
- [Escape hatches](#escape-hatches)
- [Reviewing a cross-platform project](#reviewing-a-cross-platform-project)

## Picking one

Pick the framework the project already uses; both compile to a real mini program and
neither is worth migrating to. For a new project the deciding question is the team's
component model: uni-app is Vue, Taro is React by default (PReact, Vue 3 and Solid are
also offered by its scaffold). Everything in the rest of this skill still applies —
these tools generate `setData` calls, WXML and `app.json`; they do not change the
runtime's cost model or its limits.

Whichever is used, the diagnosis loop ends in the generated output. Read
`dist/dev/mp-weixin` (Taro) or `unpackage/dist/dev/mp-weixin` (uni-app) when the
behaviour on device does not match the source.

## uni-app conditional compilation

Comment-delimited blocks, with the comment syntax of the host language:

```javascript
// #ifdef MP-WEIXIN
wx.reportAnalytics('view', {})
// #endif
```

```css
/* #ifdef MP-WEIXIN */
.page { padding-top: 0; }
/* #endif */
```

```html
<!-- #ifdef MP-WEIXIN -->
<official-account />
<!-- #endif -->
```

- `#ifdef` — only on the named platform; `#ifndef` — on everything else; `#endif` closes.
- `||` combines platforms; a platform can be combined with a mode flag using `&&`, and
  a mode flag can be negated by prefixing it with an exclamation mark, as in
  `APP && !VUE3-VAPOR`.
- Works in `.vue`/`.nvue`/`.uvue`, `.js`/`.uts`, `.css` and preprocessor files,
  `pages.json` and `manifest.json`.

Platform constants relevant here: `MP-WEIXIN`, `MP-ALIPAY`, `MP-BAIDU`, `MP-TOUTIAO`,
`MP-LARK`, `MP-QQ`, `MP-KUAISHOU`, `MP-JD`, `MP-360`, `MP-XHS`, `MP-HARMONY`, and `MP`
for all of them. Non-mini-program targets: `H5`/`WEB`, `APP`, `APP-ANDROID`, `APP-IOS`,
`APP-HARMONY`, `APP-NVUE`. Mode flags: `VUE3`, `VUE2`, `UNI-APP-X`, `uniVersion`.

Two syntax constraints that bite:

- Both the pre-compilation and post-compilation text must parse. A conditional key in
  JSON must not leave a dangling comma; a conditional `import` must not leave a
  duplicate binding.

  ```javascript
  // wrong: `a` is declared twice after the compiler strips one branch's comments
  // #ifdef MP-WEIXIN
  import a from 'a/wx'
  // #endif
  // #ifndef MP-WEIXIN
  import a from 'a/index'
  // #endif

  // right
  // #ifdef MP-WEIXIN
  import aWx from 'a/wx'
  // #endif
  // #ifndef MP-WEIXIN
  import aIndex from 'a/index'
  // #endif
  let a
  // #ifdef MP-WEIXIN
  a = aWx
  // #endif
  // #ifndef MP-WEIXIN
  a = aIndex
  // #endif
  ```

- In stylesheets the block markers must be `/* */` comments even in Sass/Less/Stylus;
  `//` comments there are stripped before the preprocessor runs and the block is lost.

## The typo that ships the wrong branch

If the platform name is not recognised — misspelled, or newer than the installed
HBuilderX — the compiler does not fail. It treats the condition as unmatched:
`#ifdef MP-WEIXN` drops the block, `#ifndef MP-WEIXN` keeps it.

So a single typo silently removes a WeChat-only feature from the WeChat build, or ships
an APP-only branch to every platform including WeChat. Nothing in the build output says
so. Grep every `#ifdef`/`#ifndef` against the constant list when a platform-specific
feature "does not work in production", and prefer `#ifdef MP-WEIXIN` over
`#ifndef H5` — a typo in the `#ifdef` form removes code, which fails loudly in testing,
while a typo in the `#ifndef` form adds code, which does not.

## uni-app project shape

| File | Role |
|---|---|
| `pages.json` | Routes, tabBar, window style, **subpackages** (`subPackages`), page-level `style` |
| `manifest.json` | Per-platform build config; the `mp-weixin` node carries `appid`, `setting`, `optimization` |
| `App.vue` | App lifecycle (`onLaunch`, `onShow`) |
| `uni.scss` | Global variables |
| `unpackage/dist/<mode>/mp-weixin` | The generated mini program that devtools opens |

Subpackage size limits, tabBar-in-main-package and independent subpackages all apply
exactly as they do natively; `pages.json` is just another way to write `app.json`. The
`mp-weixin.optimization.subPackages` flag enables the compiler's own subpackage
optimisation and is worth turning on for any app with subpackages.

## uni-app and glass-easel

```json
// manifest.json — whole app
{ "mp-weixin": { "componentFramework": "glass-easel", "glassEaselWebview": true } }
```

```json
// pages.json — one page
{ "path": "pages/index/index",
  "style": { "componentFramework": "glass-easel", "glassEaselWebview": true } }
```

The WXML compiler differs slightly between frameworks, so enable it per page and
compare before enabling it globally.

## Taro project shape

A `taro init` project (4.2.1) produces:

```
config/index.ts        designWidth, deviceRatio, framework, compiler, mini.postcss
config/dev.ts  prod.ts
src/app.ts             the App entry
src/app.config.ts      defineAppConfig({ pages, window, subPackages, tabBar })
src/pages/index/index.tsx
src/pages/index/index.config.ts    definePageConfig({ navigationBarTitleText })
project.config.json
```

`app.config.ts` and `<page>.config.ts` compile to `app.json` and the page JSON; every
native config key goes there, including `subPackages`, `preloadRule`,
`lazyCodeLoading`, `renderer` and `componentFramework`.

Build targets come from the scaffolded scripts:

```bash
npm run dev:weapp      # taro build --type weapp --watch
npm run build:weapp    # taro build --type weapp
```

and the other `--type` values the scaffold wires up: `alipay`, `swan`, `tt`, `qq`,
`jd`, `h5`, `rn`, `harmony-hybrid`. The mini program to open in devtools is
`dist/` (or `dist/dev/...` depending on the configured `outputRoot`).

`compiler` in `config/index.ts` is `'webpack5'` or `'vite'`; the scaffold asks at init
time and the answer is not trivially reversible later.

## Taro platform branching

```javascript
import Taro from '@tarojs/taro'

if (process.env.TARO_ENV === 'weapp') { /* WeChat only */ }
```

`process.env.TARO_ENV` is replaced at build time, so unreachable branches are removed
by dead-code elimination. Unlike uni-app's `#ifdef`, an unknown value here is an
ordinary falsy comparison — the branch is simply skipped, which is also silent but at
least symmetrical.

Platform-specific files (`index.weapp.tsx` beside `index.tsx`) are resolved by the
compiler and are the better tool when the whole component differs.

`useLoad`, `useReady`, `useDidShow`, `useDidHide` from `@tarojs/taro` map onto the page
lifecycle; the ordering rules in this skill's lifecycle reference apply unchanged,
because these hooks are registered on the generated `Page`.

## Sizing: rpx, designWidth, pxtransform

`rpx` is the mini program's own unit: the screen is always 750rpx wide, so `rpx`
scales with device width.

Both frameworks let you write `px` in source and convert:

- Taro's `config/index.ts` sets `designWidth: 750` and a `deviceRatio` map, and
  `mini.postcss.pxtransform` performs the conversion. With `designWidth: 750`, `1px` in
  source becomes `1rpx` in the output — so a value copied from a 375-wide web design
  comes out half size.
- uni-app converts `px` to `rpx` according to the design width configured in
  `pages.json`/`manifest.json`.

Decide once whether the codebase writes `px` (converted) or `rpx` (literal) and keep it
consistent; a file that mixes both is impossible to review.

## What the abstraction does not hide

- Component and API coverage differs per platform. `official-account`, `ad`, `open-data`
  and WeChat's open-capability buttons have no cross-platform equivalent and must be
  conditional.
- Every `<button open-type="…">` behaviour, the login flow, authorization scopes and
  the privacy-consent flow are WeChat-specific and unavoidably platform code.
- Subpackage size caps, the page-stack limit, the native-component rules and the
  data-update cost model all apply to the generated output. A Vue `v-for` over 600 rows
  becomes a `wx:for` over 600 rows.
- Skyline is a WeChat renderer. Enabling it in a cross-platform project affects only the
  WeChat build.

## Escape hatches

- **Native components inside the framework.** Both allow the platform's own tags
  (`<official-account>`, `<ad>`) inside a conditional block.
- **Native pages/components alongside generated ones.** uni-app supports native mini
  program components through `wxcomponents/`; Taro through
  `usingComponents` in the page config. Use it when a vendor SDK ships only a native
  component.
- **Direct `wx.*` calls.** `uni.*` and `Taro.*` cover the common APIs; anything else is
  a `wx.*` call inside a conditional block. This is normal, not a smell.
- **Patch the output.** Never. A post-build script that edits the generated WXML is
  invisible to the next developer; fix it in the source or in the compiler config.

## Reviewing a cross-platform project

- [ ] Every `#ifdef`/`#ifndef` names a constant that exists (see the list above).
- [ ] `#ifndef` is not used where a typo would add code to WeChat.
- [ ] Conditional imports do not create duplicate bindings; conditional JSON keys leave
      valid JSON.
- [ ] Style conditionals use `/* */`, including in Sass/Less/Stylus.
- [ ] Subpackages are declared in `pages.json`/`app.config.ts`, and tabBar pages are in
      the main package.
- [ ] `px`-vs-`rpx` policy is consistent with `designWidth`.
- [ ] WeChat-only capabilities (login, phone number, privacy consent, `open-type`
      buttons) are inside platform conditionals.
- [ ] The generated `mp-weixin` output has been opened in devtools, not just the source
      reviewed.

<!-- sources: dcloud-uni-app, taro, wx-official-docs, sonofmagic-skills -->
