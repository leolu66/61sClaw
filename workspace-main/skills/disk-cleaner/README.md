# C 盘清理技能使用说明

## 📋 技能位置
```
C:\Users\luzhe\.openclaw\workspace-main\skills\disk-cleaner\
```

## 📁 文件结构
```
disk-cleaner/
├── safe.ps1           # 推荐：安全版本（英文界面）
├── run.ps1            # 完整版本（中文界面，需修复编码）
├── clean_disk.ps1     # 早期版本（不推荐）
├── SKILL.md           # 技能说明文档
└── README.md          # 本文件
```

---

## ⚠️ 清理原则

### ✅ 安全清理（可自动执行）
**临时文件** - 这些文件可以随时删除，不影响系统和应用：
- 用户临时文件 (`AppData\Local\Temp`)
- 系统临时文件 (`Windows\Temp`)
- npm 缓存 (`AppData\Local\npm-cache`)
- 回收站

### ❌ 重要数据（不自动删除）
**需要用户手动确认** - 这些可能包含重要数据：
- Documents 目录
- 应用缓存（微信、QQ、浏览器等）
- 用户文档、下载、桌面文件

---

## 🛠️ 使用方法

### 方法 1：运行脚本

```powershell
# 仅分析（默认，最安全）
powershell -ExecutionPolicy Bypass -File "C:\Users\luzhe\.openclaw\workspace-main\skills\disk-cleaner\safe.ps1"

# 分析 + 清理临时文件
powershell -ExecutionPolicy Bypass -File "...\safe.ps1" -Mode clean-temp
```

### 方法 2：通过 AI 助手
对助手说：
- "分析 C 盘"
- "清理临时文件"
- "C 盘清理"

---

## 📊 清理内容清单

### 🔵 阶段 1：自动清理（安全）

| 项目 | 路径 | 说明 | 风险 |
|------|------|------|------|
| 用户临时文件 | `C:\Users\luzhe\AppData\Local\Temp\*` | 应用运行时产生的临时文件 | ✅ 无风险 |
| 系统临时文件 | `C:\Windows\Temp\*` | Windows 系统临时文件 | ✅ 无风险 |
| npm 缓存 | `C:\Users\luzhe\AppData\Local\npm-cache` | Node.js 包缓存 | ✅ 无风险 |
| 锁定文件处理 | - | 被其他应用占用的文件会跳过 | ✅ 自动跳过 |

**预计释放**: 1-5 GB（取决于上次清理时间）

**清理策略**:
- 逐个文件尝试删除
- 遇到锁定文件自动跳过
- 显示删除数量和跳过数量
- 锁定的文件重启后会自动删除

---

### 🟡 阶段 2：分析显示（不删除）

**仅分析并显示占用情况，不会删除任何文件！**

| 类别 | 检查项目 | 占用 | 清理建议 |
|------|---------|------|---------|
| **社交应用** | 微信 | ~17.9 GB | 微信设置 → 存储空间管理 |
| | QQ (Tencent Files) | 2.62 GB | QQ 设置 → 文件管理 → 更改位置 |
| | 飞书 | 1.52 GB | 飞书设置 → 高级 → 清理缓存 |
| | 钉钉 | - | 钉钉设置 → 存储管理 |
| **浏览器** | Chrome | 1.59 GB | Chrome 设置 → 隐私和安全 |
| | Edge | 1.38 GB | Edge 设置 → 隐私 |
| | Firefox | - | Firefox 设置 → 隐私与安全 |
| **办公应用** | 印象笔记 | 1.18 GB | 印象笔记 → 工具 → 选项 |
| | WPS 云盘 | 1 GB | WPS 设置 → 高级 |
| **开发工具** | npm | 0.2 GB | `npm cache clean --force` |

---

### 🔴 阶段 3：重要目录（重点保护）

**这些目录绝对不会自动删除！**

| 目录 | 占用 | 建议 |
|------|------|------|
| Documents | 4.94 GB | 手动检查，或迁移到 D 盘 |
| Downloads | 0.44 GB | 定期手动清理 |
| Desktop | 0.15 GB | 保持整洁 |
| AppData | 37.42 GB | 应用数据，不建议手动删除 |

**Documents 子目录详情**:
```
Tencent Files           2.62 GB  → QQ 文件，可迁移
WPS Cloud Files         1.00 GB  → WPS 云文档，可迁移
印象笔记同步助手       1.18 GB  → 可迁移
```

---

## 🔍 清理过程示例

### 运行分析模式
```
========================================
  C Disk Cleaner v1.2 (SAFE)
========================================

[Step 2] Analyzing disk...

  C Disk:
  Total: 200 GB
  Used: 142.74 GB (71.4%)
  Free: 57.26 GB

  Top Directories:
  - Windows: 41.59 GB
  - Users: 46.83 GB
  - Program Files: 21.2 GB

  User Directories:
  - AppData: 37.42 GB
  - Documents: 4.94 GB
  - Downloads: 0.44 GB

  App Caches (manual clean only):
  - QQ: 2.62 GB
  - Feishu: 1.52 GB
  - Chrome: 1.59 GB
  - Edge: 1.38 GB
  - WPS: 1 GB

[Step 3] Recommendations:

  [SAFE] Auto-clean:
  - Temp files, npm cache
  Command: .\run.ps1 -Mode clean-temp

  [MANUAL] Review and clean yourself:
  - WeChat: Settings -> Storage
  - QQ: Settings -> File Management
  - Browsers: Settings -> Privacy

  [IMPORTANT] Documents folder:
  DO NOT auto-delete! Manual review only.
  - Tencent Files: 2.62 GB
  - WPS Cloud Files: 1 GB
  - WizNote: 1.18 GB

========================================
  Analysis Complete!
========================================
  Status: 57.26 GB free (71.4% used)
```

### 运行清理临时文件模式
```
========================================
  C Disk Cleaner v1.2 (SAFE)
========================================

[Step 1] Cleaning temp files (SAFE)...

  [OK] User temp: 435 files deleted
      Skipped 36 locked files (in use by other apps)
  [OK] System temp: 128 files deleted
  [OK] npm cache cleaned

  Temp cleanup complete!

[Step 2] Analyzing disk...
...（后续显示分析结果）
```

---

## 📝 清理决策流程

```
开始
  │
  ├─→ [1] 分析 C 盘占用
  │     └─→ 显示各目录和应用占用
  │
  ├─→ [2] 自动清理临时文件（可选）
  │     ├─→ 用户临时文件
  │     ├─→ 系统临时文件
  │     └─→ npm 缓存
  │
  ├─→ [3] 显示需要手动清理的项目
  │     ├─→ 微信/QQ/飞书缓存
  │     ├─→ 浏览器缓存
  │     └─→ 办公应用缓存
  │
  └─→ [4] 重要目录警告
        └─→ Documents 不自动删除
```

---

## ⚙️ 高级选项

### 清理临时文件（安全）
```powershell
# 使用安全版本
.\safe.ps1 -Mode clean-temp

# 或使用完整版本
.\run.ps1 -Mode clean-temp
```

### 仅分析（推荐首次使用）
```powershell
.\safe.ps1 -Mode analyze
# 或
.\safe.ps1  # 默认就是 analyze
```

---

## 🔐 安全保障

1. **默认只分析不删除** - 除非明确指定 `-Mode clean-temp`
2. **跳过锁定文件** - 正在使用的文件不会强行删除
3. **重要目录保护** - Documents、Pictures 等目录只分析不删除
4. **详细统计** - 显示删除了多少文件、跳过了多少
5. **可逆操作** - 临时文件删除后不影响系统运行

---

## 📞 常见问题

### Q: 为什么有些文件被跳过？
A: 被其他应用占用的文件会跳过，这些文件重启后会自动删除。

### Q: 可以安全删除微信缓存吗？
A: 建议在微信设置中使用官方清理功能，不要直接删除文件。

### Q: 如何迁移 QQ 文件到 D 盘？
A: 在 QQ 设置 → 文件管理 → 更改文件保存位置，选择 D 盘目录。

### Q: 清理后 C 盘空间没有变化？
A: 可能跳过了锁定文件，重启后再检查。

---

## 📊 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2026-02-26 | 初始版本 |
| v1.1 | 2026-02-26 | 添加跳过锁定文件功能 |
| v1.2 | 2026-02-26 | **安全版**：临时文件和应用缓存分离，重要数据不自动删除 |

---

## ✅ 检查清单

使用前请确认：

- [ ] 已了解哪些文件会被自动删除
- [ ] 已了解哪些文件需要手动清理
- [ ] 已了解 Documents 目录不会自动删除
- [ ] 已备份重要数据（建议）
- [ ] 同意清理策略

---

**最后更新**: 2026-02-26  
**维护者**: 小天才
