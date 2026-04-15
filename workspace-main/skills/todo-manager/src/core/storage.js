const fs = require('fs');
const path = require('path');

class Storage {
  constructor(dataPath) {
    this.dataPath = dataPath;
    this.ensureDataFile();
  }

  ensureDataFile() {
    if (!fs.existsSync(this.dataPath)) {
      const dir = path.dirname(this.dataPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      this.save({ tasks: [], config: { workHours: { start: "09:00", end: "18:00" }, workdays: [1, 2, 3, 4, 5] } });
    }
  }

  load() {
    try {
      const data = fs.readFileSync(this.dataPath, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      console.error('Failed to load data:', error);
      return { tasks: [], config: { workHours: { start: "09:00", end: "18:00" }, workdays: [1, 2, 3, 4, 5] } };
    }
  }

  save(data) {
    try {
      fs.writeFileSync(this.dataPath, JSON.stringify(data, null, 2), 'utf-8');
      return true;
    } catch (error) {
      console.error('Failed to save data:', error);
      return false;
    }
  }

  getTasks() {
    return this.load().tasks;
  }

  getConfig() {
    return this.load().config;
  }

  saveTasks(tasks) {
    const data = this.load();
    data.tasks = tasks;
    return this.save(data);
  }
}

module.exports = Storage;
