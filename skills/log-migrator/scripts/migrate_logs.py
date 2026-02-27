#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志迁移工具
自动将超过指定天数的工作日志迁移到归档目录
"""
import os
import sys
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path

# 解决 Windows 中文编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class LogMigrator:
    def __init__(self, config_file=None):
        """初始化迁移器"""
        script_dir = Path(__file__).parent
        workspace_dir = script_dir.parent.parent.parent

        # 加载配置
        self.config = self._load_config(config_file or (script_dir / "config.json"))

        # 目录路径
        self.source_dir = workspace_dir / self.config.get('source_dir', 'logs/daily')
        self.archive_base = Path(self.config.get('archive_base', r'D:\openclaw\logs\daily\archive'))
        self.log_dir = workspace_dir / self.config.get('log_dir', 'logs/errors')

        # 参数
        self.retention_days = self.config.get('retention_days', 7)
        self.dry_run = self.config.get('dry_run', False)

        # 统计
        self.migrated_files = []
        self.skipped_files = []
        self.error_files = []

    def _load_config(self, config_file):
        """加载配置文件"""
        if config_file and config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _is_old_log(self, filename):
        """判断日志文件是否超过保留天数"""
        # 直接使用文件的修改时间判断
        source_file = self.source_dir / filename

        if not source_file.exists():
            return False

        try:
            # 获取文件修改时间（最后修改时间）
            modify_time = datetime.fromtimestamp(source_file.stat().st_mtime)

            # 计算截止日期
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            # 返回是否需要迁移
            is_old = modify_time < cutoff_date

            # 调试输出
            if is_old:
                print(f"  📁 {filename} (修改时间: {modify_time.strftime('%Y-%m-%d %H:%M')})")

            return is_old

        except Exception as e:
            # 获取时间失败，跳过此文件
            print(f"  ⚠️  {filename} - 无法获取时间: {e}")
            return False

    def _get_archive_path(self, filename):
        """获取归档路径（按年/月组织）"""
        # 文件名格式：YYYY-MM-DD-*.md
        parts = filename.replace('.md', '').split('-')
        if len(parts) >= 2:
            year = parts[0]
            month = parts[1]
            archive_dir = self.archive_base / year / month
            archive_dir.mkdir(parents=True, exist_ok=True)
            return archive_dir / filename
        return self.archive_base / filename

    def scan_old_logs(self):
        """扫描需要迁移的旧日志"""
        if not self.source_dir.exists():
            print(f"⚠️  源目录不存在: {self.source_dir}")
            return []

        old_logs = []
        print(f"\n🔍 扫描目录: {self.source_dir}")

        # 使用 pathlib 而不是 os.listdir，更好地处理编码
        for file_path in sorted(self.source_dir.iterdir()):
            filename = file_path.name
            if not filename.endswith('.md'):
                continue

            is_old = self._is_old_log(filename)
            if is_old:
                old_logs.append(filename)

        print(f"✅ 扫描完成，发现 {len(old_logs)} 个需要迁移的文件")
        return old_logs

    def migrate_file(self, filename):
        """迁移单个日志文件"""
        source_file = self.source_dir / filename
        target_file = self._get_archive_path(filename)

        # 检查目标文件是否已存在
        if target_file.exists():
            print(f"  ⏭️  {filename} - 目标文件已存在，跳过")
            self.skipped_files.append(filename)
            return False

        # 检查源文件是否可读
        if not os.access(source_file, os.R_OK):
            print(f"  ❌ {filename} - 无法读取，跳过")
            self.error_files.append(filename)
            return False

        # 干运行模式
        if self.dry_run:
            print(f"  🔍 {filename} → {target_file.parent.name}\\{filename}")
            self.migrated_files.append(filename)
            return True

        # 实际迁移
        try:
            shutil.move(str(source_file), str(target_file))
            print(f"  ✅ {filename} → {target_file.parent.name}\\")
            self.migrated_files.append(filename)
            return True
        except Exception as e:
            print(f"  ❌ {filename} - 迁移失败: {e}")
            self.error_files.append(filename)
            return False

    def run(self):
        """执行迁移"""
        print("=" * 60)
        print("日志自动归档")
        print("=" * 60)
        print(f"扫描目录: {self.source_dir}")
        print(f"保留天数: {self.retention_days} 天")
        print(f"目标目录: {self.archive_base}")
        print(f"试运行模式: {'是' if self.dry_run else '否'}")
        print("-" * 60)

        # 扫描旧日志
        old_logs = self.scan_old_logs()

        if not old_logs:
            print("✅ 没有需要迁移的文件")
            return

        print(f"📋 发现 {len(old_logs)} 个文件需要迁移:")
        print()

        # 迁移文件（先计算总大小）
        total_size = 0
        for filename in old_logs:
            file_path = self.source_dir / filename
            if file_path.exists():
                try:
                    total_size += file_path.stat().st_size
                except:
                    pass

        print("📦 开始迁移...")
        print()

        for filename in old_logs:
            self.migrate_file(filename)

        # 统计信息
        print("-" * 60)
        print("✅ 迁移完成！")
        print(f"  迁移文件: {len(self.migrated_files)}")
        print(f"  跳过文件: {len(self.skipped_files)}")
        print(f"  错误文件: {len(self.error_files)}")

        # 计算节省空间
        size_mb = total_size / 1024 / 1024
        print(f"  节省空间: {size_mb:.2f} MB")

        # 生成迁移日志
        self._generate_migration_log()

        print()
        print("=" * 60)
        print(f"迁移日志已保存: {self.log_dir}")
        print("=" * 60)

    def _generate_migration_log(self):
        """生成迁移日志"""
        self.log_dir.mkdir(parents=True, exist_ok=True)

        log_filename = f"log-migration-{datetime.now().strftime('%Y-%m-%d')}.md"
        log_file = self.log_dir / log_filename

        content = f"""# 日志迁移报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 迁移时间 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
| 源目录 | {self.source_dir} |
| 目标目录 | {self.archive_base} |
| 保留天数 | {self.retention_days} 天 |
| 试运行模式 | {'是' if self.dry_run else '否'} |

---

## 迁移统计

| 项目 | 数量 |
|------|------|
| 扫描到的文件 | {len(self.migrated_files) + len(self.skipped_files) + len(self.error_files)} |
| 成功迁移 | {len(self.migrated_files)} |
| 跳过文件 | {len(self.skipped_files)} |
| 错误文件 | {len(self.error_files)} |

---

## 迁移文件列表

"""

        if self.migrated_files:
            content += "### ✅ 成功迁移\n\n"
            for filename in self.migrated_files:
                content += f"- {filename}\n"
            content += "\n"

        if self.skipped_files:
            content += "### ⏭️  跳过文件\n\n"
            for filename in self.skipped_files:
                content += f"- {filename} (目标已存在)\n"
            content += "\n"

        if self.error_files:
            content += "### ❌ 错误文件\n\n"
            for filename in self.error_files:
                content += f"- {filename} (迁移失败)\n"
            content += "\n"

        content += "---\n\n"
        content += "*报告生成时间：" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*\n"

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"📝 迁移日志: {log_file.name}")


def main():
    """主函数"""
    migrator = LogMigrator()
    migrator.run()


if __name__ == "__main__":
    main()
