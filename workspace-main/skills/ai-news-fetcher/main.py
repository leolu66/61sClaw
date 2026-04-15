"""
主入口 - 运行新闻采集任务
"""
import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from spider.config_loader import ConfigLoader
from spider.engine import SpiderEngine
from spider.storage import StorageFactory, auto_save
from spider.monitor import get_monitor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            Path("logs") / f"spider_{datetime.now():%Y%m%d}.log",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="新闻采集机器人")
    parser.add_argument(
        "--site", "-s",
        help="指定采集站点（默认采集所有启用的站点）",
    )
    parser.add_argument(
        "--max-items", "-n",
        type=int,
        default=10,
        help="每个站点最大采集条目数（默认10）",
    )
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "jsonl", "csv", "md", "auto"],
        default="auto",
        help="输出格式（默认auto，同时输出多种格式）",
    )
    parser.add_argument(
        "--config-dir",
        help="配置目录路径（默认 site-configs/）",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=3,
        help="并发请求数（默认3）",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="请求间隔（秒，默认1.0）",
    )
    
    args = parser.parse_args()
    
    # 创建日志目录
    Path("logs").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)
    
    logger.info("=" * 50)
    logger.info("🕷️  新闻采集机器人启动")
    logger.info("=" * 50)
    
    # 加载配置
    loader = ConfigLoader(args.config_dir)
    
    if args.site:
        # 采集指定站点
        config = loader.load_single(args.site)
        if not config:
            logger.error(f"未找到站点配置: {args.site}")
            sys.exit(1)
        configs = [config]
    else:
        # 采集所有启用的站点
        configs = loader.load_all(enabled_only=True)
    
    if not configs:
        logger.warning("没有可用的站点配置")
        sys.exit(0)
    
    logger.info(f"加载了 {len(configs)} 个站点配置")
    for config in configs:
        logger.info(f"  - {config['site']['name']}")
    
    # 采集数据
    all_items = []
    
    async with SpiderEngine(
        max_concurrent=args.concurrent,
        default_delay=args.delay,
    ) as engine:
        for config in configs:
            site_name = config["site"]["name"]
            logger.info(f"\n📰 开始采集: {site_name}")
            
            try:
                async for item in engine.crawl_site(config, args.max_items):
                    all_items.append(item)
                    logger.info(f"  ✅ {item.title[:40]}...")
            except Exception as e:
                logger.error(f"采集 {site_name} 失败: {e}")
                continue
    
    # 保存结果
    logger.info(f"\n💾 采集完成，共 {len(all_items)} 条数据")
    
    if all_items:
        if args.output:
            # 指定输出文件
            format_type = args.format if args.format != "auto" else "json"
            storage = StorageFactory.create(format_type, args.output)
            storage.save(all_items)
            logger.info(f"结果已保存到: {args.output}")
        elif args.format == "auto":
            # 自动保存为多种格式
            results = auto_save(all_items, output_dir="output")
            logger.info("结果已保存:")
            for fmt, path in results.items():
                logger.info(f"  [{fmt}] {path}")
        else:
            # 单一格式输出
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"news_{timestamp}.{args.format}"
            if args.format == "md":
                filename = f"news_{timestamp}.md"
            filepath = Path("output") / filename
            storage = StorageFactory.create(args.format, filepath)
            storage.save(all_items)
            logger.info(f"结果已保存到: {filepath}")
    
    # 保存监控状态
    get_monitor().save_state()
    
    logger.info("\n✨ 所有任务完成")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  用户中断")
        sys.exit(0)
    except Exception as e:
        logger.exception("运行异常")
        sys.exit(1)
