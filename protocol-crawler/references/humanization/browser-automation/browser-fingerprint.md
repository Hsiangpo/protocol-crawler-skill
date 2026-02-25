# 浏览器环境与zw

除了动作，你的"身体"（浏览器环境）必须看起来像个正常人。

## 1. 视口与注意力 (Viewport & Attention)

大部分pc脚本是"全神贯注"的：从加载页面到任务结束，浏览器一直处于激活状态。而真实人类的操作是碎片化的。

### 1.1 可见性与焦点管理 (Visibility State API)

**检测原理**：JS 可以通过 `document.visibilityState` 和 `window.onblur/onfocus` 监听用户是否切换了标签页或最小化了浏览器。

**拟人策略**：

**Alt-Tab 模拟**：在长任务中间，必须强制插入一段"失去焦点"的时间。

**实现**：

- 通过 CDP 发送 `Page.bringToFront` 和 `Target.activateTarget` 来控制
- 模拟用户切出去回个微信，或者去另一个标签页对比价格，过了 30秒 再切回来继续操作

### 1.2 鼠标出界 (The "Out-of-Bounds" Mouse)

**现象**：pc的鼠标坐标通常永远被限制在 `0 < x < window.innerWidth` 和 `0 < y < window.innerHeight` 之间。

**真实行为**：用户经常要把鼠标移出网页区域，去点击浏览器的地址栏、后退按钮、书签栏，或者操作系统的任务栏。

**实现**：

1. 偶尔将鼠标坐标移出视口边界（例如 y < 0）
2. 触发 `document.mouseleave` 事件
3. 移出期间，网页内的 mousemove 事件应当完全停止

## 2. 硬件渲染一致性 (Hardware Consistency)

这是目前zw检测最狠的一招：一致性检测 (Consistency Check)。

fk系统不会只看 User-Agent，它会检查 User-Agent 声称的设备与实际硬件 API 返回的特征是否矛盾。

### 2.1 GPU 渲染器zw (WebGL Renderer)

**致命破绽**：

```
UA: Mozilla/5.0 (iPhone; CPU iPhone OS 15...)
WebGL Renderer: NVIDIA GeForce RTX 3080
```

iPhone 不可能插一张 RTX 3080 显卡。Bot 确认。

**顶尖方案**：

- **数据库匹配**：建立真实的zw数据库。如果你伪装成 iPhone 13，必须通过 zrgz 设置对应的 WebGL 参数（Apple GPU）
- **禁止随机**：绝对不要随机生成一个不存在的显卡型号
- Hook `WEBGL_debug_renderer_info` 扩展，返回与 UA 匹配的字符串

### 2.2 字体zw

**原理**：浏览器渲染文字时，需要调用操作系统安装的字体。不同 OS 的预装字体完全不同。

**致命破绽**：伪装成 Windows Chrome，结果测不到 Calibri 或 Consolas 字体，却测到了 Linux 特有的 Ubuntu-Regular。

**实现**：

- Docker 容器化时，必须安装微软核心字体库（`ttf-mscorefonts-installer`）
- 或通过 JS Hook `measureText` / `offsetWidth`，伪造 Windows 字体应有的宽度值

### 2.3 屏幕与窗口几何 (Screen Geometry)

**破绽**：`window.innerWidth` (视口) > `window.screen.width` (屏幕)。这是物理上不可能的。

**拟人**：

- 始终设置 `window.screen` 尺寸为常见分辨率（1920x1080, 1366x768）
- 视口大小必须**小于**屏幕大小（减去任务栏、浏览器边框、滚动条的宽度）
- **不要使用标准尺寸**：不要正好 1920x1080。真实浏览器视口可能是 1920x937 这种奇怪的数字

## 3. 原生对象完整性 (Native Object Integrity)

高级fk会检测"你是否在撒谎"。

### 3.1 toString() 保护

**检测**：网站会执行 `navigator.plugins.refresh.toString()`

**原生**：返回 `"function refresh() { [native code] }"`

**被 Hook**：返回 JS 函数代码，或者格式略有不同的字符串

**对策**：使用 Proxy 包装原生对象，并拦截 toString 方法，确保存取时返回标准的 `[native code]` 字符串。这叫做 "ToString Trap"。

### 3.2 navigator.webdriver 隐藏

**初级**：`Object.defineProperty(navigator, 'webdriver', {get: () => false})`

**高级检测**：检查该属性的描述符（Descriptor）。原生的 webdriver 属性是不可配置的（non-configurable）。如果你的伪造属性描述符与原生不一致，直接判定为 Bot。

**CDP 方案**：使用 Chrome 启动参数 `--disable-blink-features=AutomationControlled` 从底层移除该标志。

## 4. 浏览器特征熵 (Browser Entropy)

**Canvas 噪点检测**：

- 旧方法：在 Canvas 绘图结果上增加随机噪点，让zw哈希变动
- 新风险：这种"每台机器都不一样"的唯一性，反而成了超级zw

**拟人趋势**：

> 目标不是"唯一"，而是"平庸"。你的zw越普通、与大众越撞车（Collisions），你越安全。不要让自己变得特别，要让自己消失在人群中。

## 技术栈清单

| 组件     | 实现方式                                                                                        |
| -------- | ----------------------------------------------------------------------------------------------- |
| zw库     | 收集或购买真实的浏览器zw数据（包含 UserAgent, Screen, WebGL, Fonts, AudioContext 等的完整组合） |
| CDP      | 使用 `Page.addScriptToEvaluateOnNewDocument` 在页面加载前修改环境特征                           |
| 底层补丁 | 使用修改编译过的 Chromium 内核，从 C++ 层面移除 `cdc_` 变量和 webdriver 标记                    |
