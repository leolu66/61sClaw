# -*- coding: utf-8 -*-
f=open('task_lifetime_card.py','r',encoding='utf-8')
lines=f.readlines()
f.close()

idx=None
for i,line in enumerate(lines):
    if '# 步骤 10' in line and '返回按钮' in line:
        idx=i
        break

if idx:
    new_lines=[
        '        # 步骤 9.5：再次点击当前位置关闭第二个提示框\n',
        '        print("\\n[步骤 9.5] 关闭第二个提示框...", flush=True)\n',
        '        print(f"再次点击位置：({close_x}, {close_y})", flush=True)\n',
        '        controller.move_and_click(close_x, close_y)\n',
        '        print("[OK] 已关闭第二个提示框", flush=True)\n',
        '        time.sleep(0.5)\n',
        '        \n'
    ]
    for j,new_line in enumerate(new_lines):
        lines.insert(idx+j, new_line)
    f=open('task_lifetime_card.py','w',encoding='utf-8')
    f.writelines(lines)
    f.close()
    print('Inserted step 9.5 at line', idx)
else:
    print('Could not find insertion point')
