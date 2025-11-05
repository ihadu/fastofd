#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试字体名称规范化函数
验证修复后的normalize_font_name函数能正确处理STSong-Light
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
project_dir = os.path.join(os.path.dirname(os.getcwd()), "fastofd")
sys.path.insert(0, project_dir)

# 导入字体工具类
from fastofd.draw.font_tools import FontTools

def test_font_normalization():
    """测试各种字体名称格式的规范化处理"""
    font_tool = FontTools()
    
    # 测试用例
    test_cases = [
        ("STSong-Light", "STSong-Light"),  # 已正确格式化的字体
        ("Times New Roman Bold", "TimesNewRoman-Bold"),  # 带空格的标准格式
        ("Arial Regular", "Arial-Regular"),  # 常规字体
        ("Courier New Italic", "CourierNew-Italic"),  # 斜体
        ("TimesNewRoman", "Times-Roman"),  # 特殊转换
        ("STSong", "STSong"),  # 无样式后缀
    ]
    
    print("=== 字体名称规范化测试 ===")
    all_passed = True
    
    for input_font, expected_output in test_cases:
        actual_output = font_tool.normalize_font_name(input_font)
        result = "✓ 通过" if actual_output == expected_output else "✗ 失败"
        print(f"输入: '{input_font}'")
        print(f"输出: '{actual_output}'")
        print(f"期望: '{expected_output}'")
        print(f"结果: {result}")
        print("---")
        
        if actual_output != expected_output:
            all_passed = False
    
    if all_passed:
        print("🎉 所有测试通过!")
    else:
        print("❌ 部分测试失败!")

if __name__ == "__main__":
    test_font_normalization()