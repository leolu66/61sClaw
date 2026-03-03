#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具箱 - v2.0
包含两种功能：
1. 日志归档 - 将工作区日志复制到外部归档目录
2. 快速备份 - 备份整个工作区到指定位置
"""
import os
import sys
import shutil
import json
from datetime import datetime
from pathlib import Path

# 解决 Windows 中文编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def get_workspace_dir():
    """获取工作区根目录"""
    script_dir = Path(__file__).parent
    return script_dir.parent.parent.parent


def load_config(config_file):
    """加载配置文件"""
    if config_file and config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


class LogArchiver:
    """日志归档器 - 将日志复制到外部归档目录"""

    def __init__(self, config=None):
        self.config = config or {}
        workspace_dir = get_workspace_dir()

        # 配置参数
        archive_config = self.config.get('log_archive', {})
        self.source_dir = workspace_dir / archive_config.get('source_dir', 'logs')
        self.archive_base = Path(archive_config.get('archive_base', r'D:\openclaw\archive'))
        self.create_date_subdir = archive_config.get('create_date_subdir', True)

        # 统计
        self.archived_files = []
        self.skipped_files = []
        self.error_files = []
        self.total_size = 0

    def run(self):
        """执行日志归档"""
        print("=" * 60)
        print("日志归档")
        print("=" * 60)
        print(f"源目录: {self.source_dir}")
        print(f"归档目录: {self._get_archive_dir()}")
        print("-" * 60)

        # 检查源目录
        if not self.source_dir.exists():
            print(f"❌ 源目录不存在: {self.source_dir}")
            return False

        # 创建目标目录
        archive_dir = self._get_archive_dir()
        archive_dir.mkdir(parents=True, exist_ok=True)

        # 扫描并复制文件
        self._scan_and_copy(self.source_dir, archive_dir)

        # 输出统计
        print("-" * 60)
        if self.archived_files:
            print(f"✅ 归档完成！")
            print(f"  归档文件: {len(self.archived_files)}")
            size_kb = self.total_size / 1024
            print(f"  总大小: {size_kb:.1f} KB")
            print(f"  归档目录: {archive_dir}")
        else:
            print("ℹ️ 没有文件需要归档")

        print()
        print("=" * 60)
        return True

    def _get_archive_dir(self):
        """获取归档目标目录"""
        if self.create_date_subdir:
            date_str = datetime.now().strftime('%Y-%m-%d')
            return self.archive_base / date_str
        return self.archive_base

    def _scan_and_copy(self, source_dir, target_dir):
        """扫描并复制文件"""
        if not source_dir.exists():
            return

        # 遍历源目录
        for item in sorted(source_dir.rglob('*')):
            if item.is_file():
                # 计算相对路径
                rel_path = item.relative_to(source_dir)
                target_path = target_dir / rel_path

                # 创建子目录
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # 复制文件
                try:
                    # 获取文件大小
                    file_size = item.stat().st_size
                    self.total_size += file_size

                    # 复制
                    shutil.copy2(str(item), str(target_path))
                    print(f"  ✅ {rel_path}")
                    self.archived_files.append(str(rel_path))
                except Exception as e:
                    print(f"  ❌ {rel_path} - {e}")
                    self.error_files.append(str(rel_path))


class QuickBackup:
    """快速备份器 - 备份整个工作区"""

    def __init__(self, config=None):
        self.config = config or {}
        workspace_dir = get_workspace_dir()

        # 配置参数
        backup_config = self.config.get('quick_backup', {})
        self.target_base = Path(backup_config.get('target_base', r'D:\anthropic\.openclaw'))
        self.backup_suffix = backup_config.get('backup_suffix', 'bak')
        self.date_format = backup_config.get('date_format', '%y%m%d')

        # 工作区路径
        self.source_dir = workspace_dir
        self.target_dir = self.target_base / 'workspace-main'

        # 统计
        self.backup_files = []
        self.total_size = 0

    def run(self):
        """执行快速备份"""
        print("=" * 60)
        print("快速备份")
        print("=" * 60)
        print(f"当前工作区: {self.source_dir}")
        print(f"备份目标: {self.target_dir}")
        print("-" * 60)

        # 检查目标目录
        print("📋 检查目标目录...")
        if not self.target_base.exists():
            print(f"❌ 目标根目录不存在: {self.target_base}")
            return False

        if not self.target_dir.exists():
            print(f"ℹ️ 目标目录不存在，将直接复制")
            self._do_backup()
            return True

        # 需要重命名旧备份
        old_backup_name = self._get_backup_name()
        old_backup_path = self.target_base / old_backup_name

        if old_backup_path.exists():
            print(f"⚠️ 备份已存在: {old_backup_name}")
            print(f"  请手动删除后再执行备份")
            return False

        # 重命名旧备份
        print(f"  🔄 将重命名: workspace-main → {old_backup_name}")

        try:
            self.target_dir.rename(old_backup_path)
            print(f"  ✅ 重命名成功")
        except Exception as e:
            print(f"  ❌ 重命名失败: {e}")
            return False

        # 执行备份
        self._do_backup()

        return True

    def _get_backup_name(self):
        """获取备份目录名称（带日期后缀）"""
        date_str = datetime.now().strftime(self.date_format)
        return f"workspace-main.{date_str}{self.backup_suffix}"

    def _do_backup(self):
        """执行备份操作"""
        print("📦 开始备份...")
        print()

        try:
            # 复制整个目录
            shutil.copytree(
                str(self.source_dir),
                str(self.target_dir),
                dirs_exist_ok=False,
                copy_function=shutil.copy2
            )

            # 统计文件数量和大小
            for item in self.target_dir.rglob('*'):
                if item.is_file():
                    self.backup_files.append(item.relative_to(self.target_dir))
                    self.total_size += item.stat().st_size

            print("-" * 60)
            print(f"✅ 备份完成！")
            print(f"  备份文件: {len(self.backup_files)}")
            size_mb = self.total_size / 1024 / 1024
            print(f"  总大小: {size_mb:.2f} MB")
            print(f"  备份目录: {self.target_dir}")
            print()
            print("=" * 60)

        except Exception as e:
            print(f"❌ 备份失败: {e}")
            print()
            print("=" * 60)
            return False

        return True


def main():
    """主函数"""
    # 加载配置
    script_dir = Path(__file__).parent
    config = load_config(script_dir / "config.json")

    # 检查参数
    if len(sys.argv) < 2:
        print("用法:")
        print("  python log_tools.py archive    # 日志归档")
        print("  python log_tools.py backup     # 快速备份")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode in ('archive', '归档'):
        archiver = LogArchiver(config)
        archiver.run()
    elif mode in ('backup', '备份'):
        backup = QuickBackup(config)
        backup.run()
    else:
        print(f"未知模式: {mode}")
        print("可用模式: archive, backup")
        sys.exit(1)


if __name__ == "__main__":
    main()
