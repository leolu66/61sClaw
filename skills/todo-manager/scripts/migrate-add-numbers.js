const path = require('path');
const TaskManager = require('../src/core/task-manager');

const dataPath = path.join(__dirname, '../data/tasks.json');
const manager = new TaskManager(dataPath);

// 迁移脚本：给所有现有任务添加编号
function migrateExistingTasks() {
  const storage = manager.storage;
  const tasks = storage.getTasks();
  
  let modified = false;
  
  tasks.forEach(task => {
    // 如果没有 uniqueId，生成一个
    if (!task.uniqueId) {
      const createdDate = task.createdAt ? task.createdAt.substring(0, 10).replace(/-/g, '') : '20260301';
      const existingIds = tasks.filter(t => t.uniqueId && t.uniqueId.startsWith(createdDate));
      let maxSeq = 0;
      existingIds.forEach(t => {
        const match = t.uniqueId.match(/-(\d+)$/);
        if (match) {
          const seq = parseInt(match[1]);
          if (seq > maxSeq) maxSeq = seq;
        }
      });
      const nextSeq = (maxSeq + 1).toString().padStart(3, '0');
      task.uniqueId = `${createdDate}-${nextSeq}`;
      modified = true;
    }
    
    // 如果是 pending 状态且没有 todoNumber，分配一个
    if (task.status === 'pending' && !task.todoNumber) {
      const usedNumbers = tasks
        .filter(t => t.status === 'pending' && t.todoNumber)
        .map(t => t.todoNumber)
        .sort((a, b) => a - b);
      
      let number = 1;
      for (const used of usedNumbers) {
        if (used === number) {
          number++;
        } else {
          break;
        }
      }
      
      task.todoNumber = number;
      modified = true;
    }
  });
  
  if (modified) {
    storage.saveTasks(tasks);
    console.log('✅ 迁移完成，所有任务已添加编号');
  } else {
    console.log('✅ 所有任务已有编号，无需迁移');
  }
}

migrateExistingTasks();
