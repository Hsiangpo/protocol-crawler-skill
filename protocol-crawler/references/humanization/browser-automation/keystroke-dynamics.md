# 键盘输入拟人 (Keystroke Dynamics)

`send_keys()` 是瞬间完成的，这是绝对的机器特征。击键动力学 (Keystroke Dynamics) 甚至是生物识别认证的一种方式。

## 1. 键入间隔 (Inter-key Latency / Flight Time)

我们要模拟的是两个键被按下之间的时间差（Flight Time）。

### 1.1 基于 N-Gram 的延迟模型

**不要**使用统一的随机范围（如 `random(50ms, 200ms)`）。人类的肌肉记忆对不同的字母组合有完全不同的反应速度。

**熟练区 (Fast Zones)**:

- 交替手 (Alternating Hands)：左手按 A，右手按 L。大脑可以并行下达指令，极快
- 常用词根：th, he, in, er, an。固化在肌肉记忆中，延迟极低（30ms - 60ms）

**生疏区 (Slow Zones)**:

- 同指连击 (Same Finger)：如 dec，大脑需要重新寻址，延迟会飙升（150ms - 400ms）
- 大跨度跳跃：从 q 到 p

**顶尖实现**：
建立一个 "QWERTY 距离热力图"。计算上一个键和当前键在物理键盘上的欧几里得距离，结合常用双字表 (Digraph Frequency Table) 来动态生成延迟时间。

```
Delay = Base + (Distance × W₁) - (Frequency × W₂) + Noise
```

### 1.2 认知停顿 (Cognitive Pauses / Chunking)

人不是一个字符一个字符录入的，而是以"词"或"短语"为单位（Chunking）。

**现象**：输入邮箱时 `name (停顿) @ (停顿) gmail (停顿) . (停顿) com`

**策略**：在输入长字符串时，检测空格、标点符号或特殊的分割位（如 @），在此处强行插入一个较长的高斯分布停顿（300ms - 800ms）。

## 2. 按键停留时间 (Dwell Time & Overlap)

这是大多数 Python 脚本根本无法做到，但真人普遍存在的特征。

### 2.1 停留时间 (Hold Time / Dwell Time)

**原理**：KeyDown 和 KeyUp 不是同时发生的。按下到弹簧回弹通常持续 80ms - 150ms。

**拟人**：

- 小指/无名指按下的键（如 A, Q, Z, P），力量较弱，停留时间比食指（F, J）要长
- Shift/Ctrl 键的 Hold Time 极长，通常覆盖其他按键的整个输入周期

### 2.2 键位重叠 (Key Rollover) — 核心杀手锏

这是区分"模拟器"和"硬件输入"的最强特征。

**机器逻辑 (Serial Processing)**:

```
Down(A) -> Up(A) -> Wait -> Down(B) -> Up(B)
```

**真人逻辑 (Parallel / Rollover)**:

```
Down(A) -> Down(B) -> Up(A) -> Up(B)
```

当你打字很快时，A 键还没完全抬起来，B 键就已经按下去了。

**实现难度**：极高。Selenium 的 send_keys 不支持这种并行。需要通过 CDP (Chrome DevTools Protocol) 发送底层的 Input 事件流来实现重叠。

## 3. 错误与修正 (Typos & Correction)

完美的输入 = 机器人。为了通过图灵测试，必须"演戏"。

### 3.1 邻键错误 (Adjacency Errors)

**不要**随机输错字符。要模拟物理误触。

**算法**：建立键盘坐标映射。

- 目标是 H
- 误触候选集：G, J, Y, N, B (物理上在 H 旁边的键)
- 不要误触成 P 或 Z（距离太远，不符合逻辑）

**Shift 丢失**：想输入 @ (Shift+2)，结果因为 Shift 松开太快，输成了 2。

### 3.2 修正行为模式 (Correction Patterns)

真人的修正也是有"性格"的：

| 类型                     | 行为                                                                           |
| ------------------------ | ------------------------------------------------------------------------------ |
| 点对点修正 (The Surgeon) | 发现输错了 -> 停止 -> 按 Backspace N次 -> 重新输入                             |
| 全选重来 (The Rage)      | 输错太多 -> Ctrl + A -> Backspace -> 重新输入                                  |
| 方向键修正               | 发现中间错了一个字 -> ArrowLeft 移动光标 -> 修正 -> ArrowRight 或 End 回到末尾 |

## 4. 焦点与环境交互 (Focus & Environment)

输入不仅仅是键盘的事，还涉及鼠标和浏览器的配合。

### 4.1 焦点获取 (Focus Acquisition)

**机器**：直接 JS 聚焦或 `element.focus()`

**人**：

1. 鼠标移动到输入框
2. Hover 样式触发
3. MouseDown -> MouseUp -> Click 事件触发
4. 光标闪烁
5. 开始输入

**必做**：在 send_keys 之前，必须先跑一套完整的"点击输入框"的鼠标拟人脚本。

### 4.2 光标游走 (Cursor Meandering)

在打字过程中，特别是停顿思考时，鼠标光标不会像钉子一样钉在输入框上。

**实现**：在输入长文本的中间停顿期，插入微小的鼠标移动事件。

## 技术栈清单

| 组件     | 实现方式                                                                              |
| -------- | ------------------------------------------------------------------------------------- |
| 数据结构 | QWERTY 键盘布局的二维坐标图、常用二元组 (Bigram) 频率表                               |
| 底层驱动 | 放弃 `send_keys()`，使用 CDP (`Input.dispatchKeyEvent`) 精确控制时间戳                |
| 算法     | 生成器：输入目标字符串，输出 `[KeyCode, EventType, Timestamp]` 事件流，混入误触和回退 |
