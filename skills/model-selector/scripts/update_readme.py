import re

# 读取 README
with open(r'C:\Users\luzhe\.openclaw\workspace-main\skills\README.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加模型选择器描述到模型推荐器后面
new_section = """

---

#### 4. 模型选择器 (model-selector)
**描述**: 交互式模型选择器 - 显示所有可用模型清单，支持通过序号快速切换模型

**触发词**:
- "换模型"、"切换模型"、"选择模型"
- "model selector"、"换个模型"

**功能**:
- 显示所有可用模型清单（带序号）
- 显示价格、上下文、定位等关键信息
- 当前使用模型高亮标识
- 输入序号即可切换模型
- 切换后自动重启 Gateway

**脚本**: `scripts/model_selector.py`
"""

# 找到模型推荐器的位置，在其后插入
insert_marker = "#### 3. 模型推荐器 (model-recommender)"
if insert_marker in content:
    # 找到下一个 "###" 或文件末尾
    parts = content.split(insert_marker, 1)
    if len(parts) == 2:
        # 在模型推荐器内容后面插入
        content = parts[0] + insert_marker + parts[1].replace("\n---\n\n### 🎮", new_section + "\n---\n\n### 🎮", 1)

# 写回
with open(r'C:\Users\luzhe\.openclaw\workspace-main\skills\README.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("OK: README.md updated")
