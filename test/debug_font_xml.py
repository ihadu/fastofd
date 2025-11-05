#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from lxml import etree

# 测试XML文件路径
xml_path = '/Users/mac/soft/studySpace/fastofd/金晟建设集团有限公司04整本响应文件 (12)(1)_xml/Doc_0/PublicRes.xml'

def debug_xml_parsing(xml_path):
    print(f"=== 开始调试XML解析 ===")
    print(f"XML文件路径: {xml_path}")
    
    # 检查文件是否存在
    if not os.path.exists(xml_path):
        print(f"错误: 文件不存在: {xml_path}")
        return
    
    try:
        # 解析XML文件
        tree = etree.parse(xml_path)
        root = tree.getroot()
        
        # 打印根元素信息
        print(f"根元素标签: {root.tag}")
        print(f"根元素属性: {root.attrib}")
        print(f"根元素命名空间映射: {root.nsmap}")
        
        # 获取默认命名空间
        default_ns = root.nsmap.get(None, None)
        print(f"默认命名空间: {default_ns}")
        
        # 尝试不同的命名空间配置
        ns_configs = [
            {'ofd': 'http://www.ofdspec.org/2016/ofd'},
            {'ofd': 'http://www.ofdspec.org/2016'},
            {'': default_ns} if default_ns else {}
        ]
        
        for i, ns in enumerate(ns_configs):
            print(f"\n--- 尝试命名空间配置 {i+1}: {ns} ---")
            try:
                # 尝试直接访问Fonts元素
                fonts_elements = tree.xpath('//ofd:Fonts', namespaces=ns) if ns else tree.xpath('//Fonts')
                print(f"找到Fonts元素数量: {len(fonts_elements)}")
                
                # 尝试直接访问Font元素
                font_elements = tree.xpath('//ofd:Font', namespaces=ns) if ns else tree.xpath('//Font')
                print(f"找到Font元素数量: {len(font_elements)}")
                
                # 如果找到Font元素，打印详细信息
                for font in font_elements:
                    print(f"  字体标签: {font.tag}")
                    print(f"  字体属性: {font.attrib}")
                    # 尝试查找FontFile子元素
                    if ns:
                        font_file = font.find('ofd:FontFile', namespaces=ns)
                    else:
                        font_file = font.find('FontFile')
                    print(f"  FontFile元素: {font_file}")
                    if font_file is not None:
                        print(f"  FontFile内容: {font_file.text}")
            except Exception as e:
                print(f"错误: {e}")
        
        # 尝试使用命名空间通配符
        print("\n--- 尝试使用命名空间通配符 ---")
        try:
            all_font_elements = tree.xpath('//*[local-name()="Font"]')
            print(f"使用local-name()找到Font元素数量: {len(all_font_elements)}")
            
            for font in all_font_elements:
                print(f"  字体标签: {font.tag}")
                print(f"  字体属性: {font.attrib}")
                # 查找FontFile子元素
                font_file = font.find('./*[local-name()="FontFile"]')
                print(f"  FontFile元素: {font_file}")
                if font_file is not None:
                    print(f"  FontFile内容: {font_file.text}")
        except Exception as e:
            print(f"错误: {e}")
            
    except Exception as e:
        print(f"XML解析错误: {e}")

if __name__ == '__main__':
    debug_xml_parsing(xml_path)