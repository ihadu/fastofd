#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from fastofd.ofd import OFD
from fastofd.draw.draw_pdf import DrawPDF
from loguru import logger
import time

# 配置日志，只显示INFO级别
logger.remove()
logger.add(sys.stdout, level="INFO")

def find_ofd_files(directory):
    """查找目录中的OFD文件"""
    ofd_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.ofd'):
                ofd_files.append(os.path.join(root, file))
    return ofd_files

def test_default_config(ofd_path):
    """测试默认配置"""
    logger.info("=== 测试默认配置 ===")
    start_time = time.time()
    
    # 读取OFD文件
    with open(ofd_path, 'rb') as f:
        ofd_content = f.read()
    
    # 创建OFD实例
    ofd = OFD(ofd_content)
    # 解析OFD文件
    data = ofd.parse()
    
    # 创建DrawPDF实例（使用默认配置）
    draw_pdf = DrawPDF(data)
    # 生成PDF
    draw_pdf.draw_pdf()
    
    # 保存PDF文件
    output_pdf = f"output/default_config_{os.path.basename(ofd_path).replace('.ofd', '.pdf')}"
    with open(output_pdf, 'wb') as f:
        f.write(draw_pdf.pdf_io.getvalue())
    
    logger.info(f"默认配置测试完成，耗时: {time.time() - start_time:.2f}秒")
    logger.info(f"PDF保存路径: {output_pdf}")

def test_custom_config(ofd_path):
    """测试自定义配置"""
    logger.info("=== 测试自定义配置 ===")
    start_time = time.time()
    
    # 读取OFD文件
    with open(ofd_path, 'rb') as f:
        ofd_content = f.read()
    
    # 创建OFD实例
    ofd = OFD(ofd_content)
    # 解析OFD文件
    data = ofd.parse()
    
    # 创建DrawPDF实例（使用自定义配置）
    draw_pdf = DrawPDF(data, 
                       max_workers=4,                    # 限制为4个线程
                       single_thread_threshold=5,         # 少于5页时使用单线程
                       min_pages_per_chunk=2,             # 每个子PDF至少2页
                       optimized_pages_per_chunk=3,       # 优化性能的每块页数为3
                       force_single_thread=False)         # 不强制单线程
    
    # 生成PDF
    draw_pdf.draw_pdf()
    
    # 保存PDF文件
    output_pdf = f"output/custom_config_{os.path.basename(ofd_path).replace('.ofd', '.pdf')}"
    with open(output_pdf, 'wb') as f:
        f.write(draw_pdf.pdf_io.getvalue())
    
    logger.info(f"自定义配置测试完成，耗时: {time.time() - start_time:.2f}秒")
    logger.info(f"PDF保存路径: {output_pdf}")

def test_force_single_thread(ofd_path):
    """测试强制单线程模式"""
    logger.info("=== 测试强制单线程模式 ===")
    start_time = time.time()
    
    # 读取OFD文件
    with open(ofd_path, 'rb') as f:
        ofd_content = f.read()
    
    # 创建OFD实例
    ofd = OFD(ofd_content)
    # 解析OFD文件
    data = ofd.parse()
    
    # 创建DrawPDF实例（强制单线程）
    draw_pdf = DrawPDF(data, force_single_thread=True)
    
    # 生成PDF
    draw_pdf.draw_pdf()
    
    # 保存PDF文件
    output_pdf = f"output/single_thread_{os.path.basename(ofd_path).replace('.ofd', '.pdf')}"
    with open(output_pdf, 'wb') as f:
        f.write(draw_pdf.pdf_io.getvalue())
    
    logger.info(f"强制单线程模式测试完成，耗时: {time.time() - start_time:.2f}秒")
    logger.info(f"PDF保存路径: {output_pdf}")

def main():
    """主函数"""
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)
    
    # 查找OFD文件
    ofd_files = find_ofd_files('.')
    
    if not ofd_files:
        logger.error("未找到OFD文件，请确保当前目录或子目录中有OFD文件")
        return
    
    logger.info(f"找到 {len(ofd_files)} 个OFD文件")
    
    # 使用第一个OFD文件进行测试
    test_file = ofd_files[0]
    logger.info(f"使用测试文件: {test_file}")
    
    # 运行测试
    test_default_config(test_file)
    test_custom_config(test_file)
    test_force_single_thread(test_file)
    
    logger.info("所有测试完成！")

if __name__ == "__main__":
    main()