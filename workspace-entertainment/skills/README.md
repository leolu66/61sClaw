# Entertainment Skills 娱乐技能目录

本目录包含 **4** 个娱乐类 Agent 技能，用于游戏、音乐等娱乐场景。

## 📊 技能列表

| 技能 | 触发方式 | 功能 | 类型 |
|------|---------|------|------|
| gobang-game | "玩五子棋" | 五子棋游戏 | 游戏 |
| solitaire-game | "玩纸牌" | 纸牌接龙游戏 | 游戏 |
| jhwg-auto | "代玩几何王国" | 几何王国自动任务、领取奖励 | 游戏辅助 |
| potplayer-music | "播放音乐" | PotPlayer音乐播放控制 | 音乐 |

---

## 🎮 技能详情

### gobang-game（五子棋）
- **触发**: "玩五子棋"、"打开五子棋"
- **功能**: 浏览器中运行五子棋游戏
- **文件**: `gobang.html`, `scripts/open_gobang.py`

### solitaire-game（纸牌接龙）
- **触发**: "玩纸牌"、"打开纸牌游戏"
- **功能**: 浏览器中运行纸牌接龙游戏
- **文件**: `assets/solitaire.html`, `scripts/open_solitaire.py`

### jhwg-auto（江湖武功自动）
- **触发**: "代玩几何王国"、"江湖武功自动"
- **功能**: 几何王国游戏自动任务、领取奖励、自动钓鱼等
- **文件**: `scripts/task_*.py`, `任务介绍.md`

### potplayer-music（音乐播放）
- **触发**: "播放音乐"、"停止音乐"
- **功能**: 控制 PotPlayer 播放音乐
- **文件**: `scripts/play_music.py`

---

## 📝 开发规范

- 参考 `workspace-main/skills/SKILL_DO.md` 开发规范
- 参考 `workspace-main/skills/SKILL_TEMPLATE.md` 技能模板

---

*娱乐技能工作区 | 共 4 个技能*
