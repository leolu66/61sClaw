---
name: totp-query
description: |
  动态口令查询工具。根据坐标从8x8密码本中查询对应的密码并拼接生成动态口令。
  当用户说"查询卡密"、"查询动态口令"、"动态口令"、"口令"或需要查询密码本中的密码时触发。
  支持坐标格式：A1:C7 或 A1：C7（中英文冒号均可）。
---

# 动态口令查询

根据坐标从密码本中查询动态口令。

## 密码本结构

密码本是一个8x8的表格：
- **行**：A, B, C, D, E, F, G, H
- **列**：1, 2, 3, 4, 5, 6, 7, 8
- **每个格子**：一个3位字母/数字密码

| 行 \ 列 | 1   | 2   | 3   | 4   | 5   | 6   | 7   | 8   |
| ------- | --- | --- | --- | --- | --- | --- | --- | --- |
| A       | MGZ | ZKA | QPF | HFT | G3N | YEA | HAD | 6AL |
| B       | GND | BJD | LEE | 5GB | 9RJ | YE9 | PQ4 | KY9 |
| C       | WSG | VEX | CVK | KKH | Q7P | JGJ | YXH | NFE |
| D       | SXL | WB9 | 873 | BQZ | 75H | ZX5 | EL4 | JDL |
| E       | K9G | KDA | 5SZ | UDZ | ZJ7 | ARX | M2X | TE4 |
| F       | E79 | 3VZ | 6SN | SPR | AJX | NU7 | MSP | BS6 |
| G       | 77Y | QU4 | D7Z | H9V | LID | 8TX | CUT | 9Q5 |
| H       | 86L | VNR | WNN | VPQ | URB | NPA | 5KV | FSL |

## 查询动态口令

### 触发指令

- "查询卡密 A1:C7"
- "查询动态口令 A1:C7"
- "动态口令 A1:C7"
- "口令 A1:C7"
- "查询 A1:C7"

### 坐标格式

- 支持英文冒号：`A1:C7`
- 支持中文冒号：`A1：C7`

### 查询逻辑

输入 `A1:C7` 表示：
1. 取 **A行1列** 的密码：**MGZ**
2. 取 **C行7列** 的密码：**YXH**
3. 拼接结果：**MGZYXH**

### 执行查询

```powershell
# 查询动态口令（结果自动复制到剪贴板）
python "C:\Users\luzhe\.openclaw\workspace-main\skills\totp-query\scripts\query_totp.py" "A1:C7"

# 或使用中文冒号
python "C:\Users\luzhe\.openclaw\workspace-main\skills\totp-query\scripts\query_totp.py" "A1：C7"
```

**输出示例：**
```
MGZYXH
(已复制到剪贴板)
```

### 查看完整密码本

```powershell
python "C:\Users\luzhe\.openclaw\workspace-main\skills\totp-query\scripts\query_totp.py"
```

## 示例

| 输入坐标 | 第一个密码 | 第二个密码 | 动态口令 |
| -------- | ---------- | ---------- | -------- |
| A1:C7    | MGZ (A1)   | YXH (C7)   | MGZYXH   |
| B3:H5    | LEE (B3)   | URB (H5)   | LEEURB   |
| D8:E2    | JDL (D8)   | KDA (E2)   | JDLKDA   |

## 错误处理

- **无效行**：行必须是 A-H
- **无效列**：列必须是 1-8
- **格式错误**：坐标格式必须是 `行+列`，如 A1, C7

## 脚本位置

- **查询脚本**：`scripts/query_totp.py`
