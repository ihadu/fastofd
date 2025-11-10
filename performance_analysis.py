#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import importlib
import concurrent.futures
import multiprocessing
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stdout, level="INFO")

def test_environment():
    """测试运行环境参数"""
    logger.info("=== 运行环境分析 ===")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"CPU核心数: {multiprocessing.cpu_count()}")
    logger.info(f"进程ID: {os.getpid()}")
    logger.info(f"Python路径: {sys.executable}")
    logger.info(f"当前工作目录: {os.getcwd()}")
    logger.info(f"模块导入路径: {sys.path}")

def test_concurrent_performance():
    """测试并发性能"""
    logger.info("=== 并发性能测试 ===")
    
    def dummy_task(task_id):
        """模拟耗时任务"""
        start = time.time()
        # 模拟CPU密集型计算
        result = 0
        for i in range(10**7):
            result += i
        end = time.time()
        return task_id, end - start
    
    # 测试单线程
    logger.info("测试单线程性能...")
    single_start = time.time()
    for i in range(4):
        dummy_task(i)
    single_end = time.time()
    logger.info(f"单线程完成4个任务耗时: {single_end - single_start:.2f}秒")
    
    # 测试多线程
    logger.info("测试多线程性能...")
    thread_start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(dummy_task, i) for i in range(4)]
        concurrent.futures.wait(futures)
    thread_end = time.time()
    logger.info(f"多线程完成4个任务耗时: {thread_end - thread_start:.2f}秒")
    
    # 计算加速比
    speedup = (single_end - single_start) / (thread_end - thread_start)
    logger.info(f"多线程加速比: {speedup:.2f}x")
    
    # 分析线程池行为
    logger.info("\n=== 线程池行为分析 ===")
    logger.info(f"系统线程池默认设置分析:")
    try:
        import threading
        logger.info(f"当前活跃线程数: {threading.active_count()}")
        logger.info(f"线程名称列表: {[t.name for t in threading.enumerate()]}")
    except Exception as e:
        logger.error(f"线程分析失败: {e}")

def test_import_performance():
    """测试模块导入性能"""
    logger.info("\n=== 模块导入性能测试 ===")
    
    # 测试关键依赖的导入时间
    modules_to_test = [
        'reportlab.pdfgen.canvas',
        'pypdf',
        'PIL.Image',
        'concurrent.futures',
        'xmltodict'
    ]
    
    for module_name in modules_to_test:
        start = time.time()
        try:
            importlib.import_module(module_name)
            end = time.time()
            logger.info(f"导入 {module_name} 耗时: {(end - start)*1000:.2f}毫秒")
        except ImportError as e:
            logger.error(f"导入 {module_name} 失败: {e}")

def analyze_packaging_impact():
    """分析打包对性能的潜在影响"""
    logger.info("\n=== 打包影响分析 ===")
    
    # 检查是否在打包环境中运行
    is_packaged = hasattr(sys, 'frozen') or hasattr(sys, '_MEIPASS')
    logger.info(f"是否在打包环境中运行: {is_packaged}")
    
    if is_packaged:
        logger.info("检测到打包环境特征，这可能是性能差异的原因之一")
    
    # 分析可能的性能瓶颈点
    logger.info("\n=== 可能的性能瓶颈分析 ===")
    logger.info("1. 并发执行限制: 打包环境可能有线程池执行限制或GIL行为差异")
    logger.info("2. 模块导入开销: 打包后每次运行都需要重新加载模块")
    logger.info("3. 资源访问路径: 打包后资源文件访问可能有额外开销")
    logger.info("4. Python解释器优化: 不同环境下解释器优化级别可能不同")
    logger.info("5. 文件系统访问: 打包后对临时文件的操作可能更慢")

def suggest_optimizations():
    """提供优化建议"""
    logger.info("\n=== 优化建议 ===")
    logger.info("1. 预导入关键模块: 在程序启动时预导入所有必要模块")
    logger.info("2. 优化并发策略:")
    logger.info("   - 尝试调整max_workers参数，对于IO密集型任务可以设置更大值")
    logger.info("   - 考虑使用进程池而非线程池避免GIL限制")
    logger.info("3. 实现缓存机制:")
    logger.info("   - 缓存已解析的字体信息")
    logger.info("   - 缓存重复使用的图像处理结果")
    logger.info("4. 优化打包配置:")
    logger.info("   - 确保打包时包含所有必要依赖")
    logger.info("   - 考虑使用--optimize=2参数进行打包")
    logger.info("5. 资源路径优化:")
    logger.info("   - 避免在循环中进行路径解析")
    logger.info("   - 使用绝对路径而非相对路径")

def main():
    """主函数"""
    logger.info("FastOFD性能差异分析工具")
    logger.info("========================")
    
    test_environment()
    test_concurrent_performance()
    test_import_performance()
    analyze_packaging_impact()
    suggest_optimizations()
    
    logger.info("\n分析完成！请根据分析结果调整您的代码或打包配置。")

if __name__ == "__main__":
    main()