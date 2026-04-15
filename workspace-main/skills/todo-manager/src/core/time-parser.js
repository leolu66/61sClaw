const dayjs = require('dayjs');
const customParseFormat = require('dayjs/plugin/customParseFormat');
const weekday = require('dayjs/plugin/weekday');
const isSameOrBefore = require('dayjs/plugin/isSameOrBefore');
const isSameOrAfter = require('dayjs/plugin/isSameOrAfter');

dayjs.extend(customParseFormat);
dayjs.extend(weekday);
dayjs.extend(isSameOrBefore);
dayjs.extend(isSameOrAfter);

class TimeParser {
  /**
   * 解析用户输入的时间描述
   * @param {string} input - 用户输入（今天/明天/周三/3月2日/2026-03-02）
   * @returns {string} ISO 8601 格式的时间字符串
   */
  static parse(input) {
    const now = dayjs();
    const normalized = input.trim().toLowerCase();

    // 今天
    if (normalized === '今天' || normalized === 'today') {
      return now.endOf('day').toISOString();
    }

    // 明天
    if (normalized === '明天' || normalized === 'tomorrow') {
      return now.add(1, 'day').endOf('day').toISOString();
    }

    // 后天
    if (normalized === '后天') {
      return now.add(2, 'day').endOf('day').toISOString();
    }

    // 本周/这周
    if (normalized === '本周' || normalized === '这周' || normalized === 'this week') {
      return now.endOf('week').toISOString(); // 周日 23:59:59
    }

    // 下周
    if (normalized === '下周' || normalized === 'next week') {
      return now.add(1, 'week').endOf('week').toISOString();
    }

    // 本月/这个月
    if (normalized === '本月' || normalized === '这个月' || normalized === 'this month') {
      return now.endOf('month').toISOString();
    }

    // 下月
    if (normalized === '下月' || normalized === '下个月' || normalized === 'next month') {
      return now.add(1, 'month').endOf('month').toISOString();
    }

    // 星期几（周一到周日）
    const weekdayMap = {
      '周一': 1, '周二': 2, '周三': 3, '周四': 4, '周五': 5, '周六': 6, '周日': 0,
      'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4, 'friday': 5, 'saturday': 6, 'sunday': 0
    };

    for (const [key, value] of Object.entries(weekdayMap)) {
      if (normalized === key) {
        let target = now.weekday(value);
        // 如果目标日期已过，则取下周
        if (target.isSameOrBefore(now, 'day')) {
          target = target.add(1, 'week');
        }
        return target.endOf('day').toISOString();
      }
    }

    // 月-日格式（3月2日 / 3-2 / 03-02）
    const monthDayMatch = normalized.match(/(\d{1,2})[月\-](\d{1,2})[日]?/);
    if (monthDayMatch) {
      const month = parseInt(monthDayMatch[1]);
      const day = parseInt(monthDayMatch[2]);
      let target = dayjs().month(month - 1).date(day);
      // 如果日期已过，则取明年
      if (target.isBefore(now, 'day')) {
        target = target.add(1, 'year');
      }
      return target.endOf('day').toISOString();
    }

    // ISO 格式（2026-03-02）
    const isoMatch = normalized.match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
    if (isoMatch) {
      return dayjs(normalized).endOf('day').toISOString();
    }

    // 相对天数（3天后 / 5天内）
    const relativeDayMatch = normalized.match(/(\d+)天[后内]/);
    if (relativeDayMatch) {
      const days = parseInt(relativeDayMatch[1]);
      return now.add(days, 'day').endOf('day').toISOString();
    }

    // 默认返回今天
    return now.endOf('day').toISOString();
  }

  /**
   * 判断任务类型（daily/weekly/monthly）
   * @param {string} deadline - ISO 8601 格式的截止时间
   * @returns {string} 任务类型
   */
  static inferTaskType(deadline) {
    const now = dayjs();
    const target = dayjs(deadline);
    const diffDays = target.diff(now, 'day');

    if (diffDays <= 1) return 'daily';
    if (diffDays <= 7) return 'weekly';
    return 'monthly';
  }
}

module.exports = TimeParser;
