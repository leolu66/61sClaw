import json

with open('output/models_data_full.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("所有模型分类列表：")
print("-" * 50)
for i, category in enumerate(data):
    print(f"{i+1}. {category['name']} (共 {category['expected_count']} 个模型)")
    # 打印子分类（如果有）
    if 'subGroups' in category:
        for j, sub in enumerate(category['subGroups']):
            print(f"   └─ {sub['name']} (共 {sub['expected_count']} 个模型)")
