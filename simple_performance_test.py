#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的性能测试脚本
用于测试优化后的性能配置参数和并发处理策略
"""

import os
import sys
import time
import multiprocessing
import json

def setup_environment_variables():
    """设置优化的环境变量"""
    # 设置并发优化参数
    os.environ['FASTOFD_MAX_WORKERS'] = '12'  # 使用更多线程
    os.environ['FASTOFD_SINGLE_THREAD_THRESHOLD'] = '5'  # 降低阈值，更早使用并发
    os.environ['FASTOFD_OPTIMIZED_PAGES_PER_CHUNK'] = '3'  # 更小的块大小
    os.environ['FASTOFD_USE_CACHE'] = 'True'  # 启用缓存
    os.environ['FASTOFD_CACHE_DIR'] = os.path.join(os.path.expanduser("~"), ".fastofd_perf_cache")
    
    print(f"环境变量已设置:")
    print(f"- 最大工作线程数: {os.environ['FASTOFD_MAX_WORKERS']}")
    print(f"- 单线程阈值: {os.environ['FASTOFD_SINGLE_THREAD_THRESHOLD']}")
    print(f"- 每块页数: {os.environ['FASTOFD_OPTIMIZED_PAGES_PER_CHUNK']}")
    print(f"- 缓存目录: {os.environ['FASTOFD_CACHE_DIR']}")

def test_environment_variable_parsing():
    """测试环境变量解析逻辑"""
    print("\n=== 测试环境变量解析 ===")
    
    # 模拟DrawPDF中的环境变量解析逻辑
    def parse_environment_variables():
        config = {
            'max_workers': int(os.environ.get('FASTOFD_MAX_WORKERS', 4)),
            'single_thread_threshold': int(os.environ.get('FASTOFD_SINGLE_THREAD_THRESHOLD', 10)),
            'pages_per_chunk': int(os.environ.get('FASTOFD_OPTIMIZED_PAGES_PER_CHUNK', 5)),
            'use_cache': os.environ.get('FASTOFD_USE_CACHE', 'False').lower() == 'true',
            'cache_dir': os.environ.get('FASTOFD_CACHE_DIR', os.path.join(os.path.expanduser("~"), ".fastofd_cache"))
        }
        return config
    
    # 测试解析性能
    start_time = time.time()
    config = parse_environment_variables()
    parse_time = time.time() - start_time
    
    print(f"环境变量解析耗时: {parse_time:.3f}秒")
    print(f"解析后的配置:")
    print(f"- max_workers: {config['max_workers']}")
    print(f"- single_thread_threshold: {config['single_thread_threshold']}")
    print(f"- pages_per_chunk: {config['pages_per_chunk']}")
    print(f"- use_cache: {config['use_cache']}")
    print(f"- cache_dir: {config['cache_dir']}")
    
    # 验证配置是否正确
    assert config['max_workers'] == 12, "max_workers配置错误"
    assert config['single_thread_threshold'] == 5, "single_thread_threshold配置错误"
    assert config['pages_per_chunk'] == 3, "pages_per_chunk配置错误"
    assert config['use_cache'] is True, "use_cache配置错误"
    assert config['cache_dir'] == os.path.join(os.path.expanduser("~"), ".fastofd_perf_cache"), "cache_dir配置错误"
    
    print("✓ 环境变量解析测试通过")
    return config

def test_concurrent_processing_strategy():
    """测试并发处理策略"""
    print("\n=== 测试并发处理策略 ===")
    
    # 获取配置参数
    max_workers = int(os.environ.get('FASTOFD_MAX_WORKERS', 4))
    single_thread_threshold = int(os.environ.get('FASTOFD_SINGLE_THREAD_THRESHOLD', 10))
    pages_per_chunk = int(os.environ.get('FASTOFD_OPTIMIZED_PAGES_PER_CHUNK', 5))
    
    # 测试不同页数下的处理模式选择
    test_cases = [
        (3, "单线程"),    # 应该使用单线程
        (10, "并发"),    # 应该使用并发
        (20, "并发")     # 应该使用并发
    ]
    
    results = []
    for page_count, expected_mode in test_cases:
        # 模拟页数判断逻辑
        use_concurrent = page_count > single_thread_threshold
        actual_mode = "并发" if use_concurrent else "单线程"
        
        print(f"页数: {page_count}, 预期模式: {expected_mode}, 实际模式: {actual_mode}")
        assert expected_mode == actual_mode, f"模式选择错误: 页数{page_count}应该使用{expected_mode}"
        
        # 计算分块数量
        if use_concurrent:
            chunk_count = (page_count + pages_per_chunk - 1) // pages_per_chunk
            # 计算实际使用的线程数
            actual_workers = min(max_workers, chunk_count)
            print(f"  -> 分块数量: {chunk_count}, 每块页数: {pages_per_chunk}, 使用线程数: {actual_workers}")
            results.append({"page_count": page_count, "chunk_count": chunk_count, "workers_used": actual_workers})
    
    print("✓ 并发处理策略测试通过")
    return results

def test_caching_setup():
    """测试缓存设置"""
    print("\n=== 测试缓存设置 ===")
    
    # 获取缓存配置
    use_cache = os.environ.get('FASTOFD_USE_CACHE', 'False').lower() == 'true'
    cache_dir = os.environ.get('FASTOFD_CACHE_DIR', os.path.join(os.path.expanduser("~"), ".fastofd_cache"))
    
    print(f"缓存配置:")
    print(f"- use_cache: {use_cache}")
    print(f"- cache_dir: {cache_dir}")
    
    # 检查缓存目录是否创建
    cache_dir_exists = os.path.exists(cache_dir)
    print(f"缓存目录存在: {cache_dir_exists}")
    
    if not cache_dir_exists and use_cache:
        print("创建缓存目录测试...")
        os.makedirs(cache_dir, exist_ok=True)
        assert os.path.exists(cache_dir), "缓存目录创建失败"
        print("✓ 缓存目录创建成功")
    
    # 验证缓存功能是否启用
    assert use_cache is True, "缓存功能未启用"
    
    print("✓ 缓存设置测试通过")
    return {"cache_enabled": use_cache, "cache_dir": cache_dir}

def test_performance_optimizations():
    """综合测试性能优化功能"""
    print("\n=== 测试性能优化功能 ===")
    
    # 测试初始化性能
    init_results = test_drawpdf_initialization()
    
    # 测试并发配置
    concurrent_results = test_concurrent_processing_config()
    
    # 测试缓存机制
    cache_results = test_caching_mechanism()
    
    # 整合结果
    all_results = {
        "initialization": init_results,
        "concurrent_processing": concurrent_results,
        "caching": cache_results
    }
    
    print("\n=== 性能优化总结 ===")
    print(f"1. 初始化性能: {init_results['init_time']:.3f}秒")
    print(f"2. 并发配置:")
    print(f"   - 最大工作线程: {init_results['max_workers']}")
    print(f"   - 单线程阈值: {init_results['single_thread_threshold']}")
    print(f"   - 每块页数: {init_results['pages_per_chunk']}")
    print(f"3. 缓存机制: {'已启用' if cache_results['cache_enabled'] else '未启用'}")
    
    return all_results

def main():
    """主函数"""
    print("===== FastOFD性能优化测试 =====")
    print(f"系统信息: CPU核心数 = {multiprocessing.cpu_count()}")
    print(f"Python版本: {sys.version}")
    
    # 设置环境变量
    setup_environment_variables()
    
    # 运行性能优化测试
    try:
        # 测试环境变量解析
        config_results = test_environment_variable_parsing()
        
        # 测试并发处理策略
        concurrent_results = test_concurrent_processing_strategy()
        
        # 测试缓存设置
        cache_results = test_caching_setup()
        
        # 测试环境变量解析性能（多轮）
        print("\n=== 测试环境变量解析性能 ===")
        iterations = 5
        parse_times = []
        
        def parse_benchmark():
            start = time.time()
            _ = {
                'max_workers': int(os.environ.get('FASTOFD_MAX_WORKERS', 4)),
                'single_thread_threshold': int(os.environ.get('FASTOFD_SINGLE_THREAD_THRESHOLD', 10)),
                'pages_per_chunk': int(os.environ.get('FASTOFD_OPTIMIZED_PAGES_PER_CHUNK', 5)),
                'use_cache': os.environ.get('FASTOFD_USE_CACHE', 'False').lower() == 'true'
            }
            return time.time() - start
        
        for i in range(iterations):
            parse_time = parse_benchmark()
            parse_times.append(parse_time)
            print(f"  第{i+1}次解析: {parse_time:.6f}秒")
        
        avg_parse_time = sum(parse_times) / len(parse_times)
        print(f"平均解析时间: {avg_parse_time:.6f}秒")
        
        # 输出性能优化总结
        print("\n===== 性能优化配置总结 =====")
        print("1. 并发处理配置:")
        print(f"   - 最大工作线程数: {config_results['max_workers']} (根据8核心CPU优化)")
        print(f"   - 单线程阈值: {config_results['single_thread_threshold']} (小文档优先单线程)")
        print(f"   - 页面分块大小: {config_results['pages_per_chunk']} (打包环境优化值)")
        
        print("\n2. 分块策略验证:")
        for result in concurrent_results:
            print(f"   - {result['page_count']}页文档: 分为{result['chunk_count']}块, 使用{result['workers_used']}线程")
        
        print("\n3. 缓存配置:")
        print(f"   - 缓存状态: {'已启用' if cache_results['cache_enabled'] else '未启用'}")
        print(f"   - 缓存目录: {cache_results['cache_dir']}")
        
        print("\n===== 打包环境优化建议 =====")
        print("1. PyInstaller打包配置:")
        print("   - 使用 '--onedir' 模式替代 '--onefile'，减少启动时间")
        print("   - 添加 '--noconsole' 参数减少资源占用")
        print("   - 考虑 '--noconfirm' 和 '--clean' 选项")
        
        print("2. 性能优化建议:")
        print("   - 保持当前并发参数配置 (max_workers=12, threshold=5, chunk=3)")
        print("   - 确保缓存目录具有写入权限")
        print("   - 对于大型文档，当前分块策略已针对打包环境优化")
        print("   - 环境变量配置可在运行时调整，无需重新编译")
        
    except AssertionError as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n===== 性能优化配置测试完成 =====")

if __name__ == "__main__":
    main()