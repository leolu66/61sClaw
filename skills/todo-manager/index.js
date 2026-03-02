const path = require('path');
const TaskManager = require('./src/core/task-manager');
const TaskFormatter = require('./src/display/task-formatter');

const dataPath = path.join(__dirname, 'data/tasks.json');
const manager = new TaskManager(dataPath);

module.exports = {
  manager,
  TaskFormatter
};
