---
name: solitaire-game
description: 打开纸牌接龙（Solitaire）游戏。当用户说"玩纸牌"、"玩纸牌接龙"、"play card"、"play cards"、"玩接龙"、"纸牌游戏"、"solitaire"、"card game"时触发此技能。
---

# 纸牌接龙游戏

打开本地纸牌接龙 HTML 游戏，让用户可以在浏览器中玩经典的单人纸牌游戏。

## 游戏特性

- **标准规则**：经典纸牌接龙玩法
- **操作方式**：
  - 单击：选中/取消选牌
  - 双击：自动将牌放入基础牌堆
- **游戏功能**：
  - 计时、步数和得分统计
  - 撤销功能
  - 自动检测胜利

## 使用方法

直接调用脚本打开游戏：

```bash
python scripts/open_solitaire.py
```

或者使用浏览器打开 assets/solitaire.html 文件。

## 游戏规则

1. **目标**：将所有牌按花色从 A 到 K 移到四个基础牌堆
2. **牌桌**：7列牌，每列最下面的牌可以移动
3. **移动规则**：牌可以移到比它大1且颜色相反的牌上
4. **空列**：只有 K 可以放到空列
5. **发牌**：点击牌库发牌，可以循环发牌

## 文件位置

- 游戏文件：`assets/solitaire.html`
- 启动脚本：`scripts/open_solitaire.py`
