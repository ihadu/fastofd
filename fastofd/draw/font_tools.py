#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME: E:\code\easyofd\easyofd\draw
# CREATE_TIME: 2023-08-22
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# NOTE:  字体处理工具
import os
import re
import base64
import zipfile
from typing import List, Tuple

from loguru import logger
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class FontTool(object):
    """字体处理工具
    用于字体归一化、系统字体收集与回退策略
    """
    # 预设的常用字体名称（可被 OFD 指定）
    FONTS = [
        "STSong-Light",  # 保证首位为已注册字体
        "宋体",
        "SimSun",
        "KaiTi",
        "SimKai",
        "黑体",
        "SimHei",
        "仿宋",
        "FangSong",
        "Times-Roman",
        "TimesNewRoman",
        "Courier",
        "Helvetica",
        "PingFang SC",
        "Songti SC",
        "Microsoft YaHei",
        "Source Han Serif SC",
        "Source Han Sans SC",
    ]

    def __init__(self, font_dir: str = None):
        self.font_dir = font_dir
        # 动态构建并覆盖实例的回退列表，供外部使用
        self.FONTS = self.get_installed_fonts()
        self.all_fonts = self.FONTS[:]

    @staticmethod
    def is_valid_font_name(name: str) -> bool:
        """过滤无效字体名（URL、邮箱、异常字符或过长）"""
        if not isinstance(name, str):
            return False
        n = name.strip()
        if not n:
            return False
        if len(n) > 80:
            return False
        if re.search(r"(https?://|mailto:)", n, re.I):
            return False
        if any(ch in n for ch in [":", "@", "\n", "\r", "\t"]):
            return False
        return True

    def _process_ttc_font(self, file_path: str) -> List[Tuple[str, str]]:
        """处理 TTC 字体包，返回内部可用字体名称列表"""
        names = []
        try:
            from fontTools.ttLib import TTCollection
            ttc = TTCollection(file_path)
            for i, tf in enumerate(ttc.fonts):
                name_record = None
                try:
                    name_record = tf["name"].getDebugName(1) or tf["name"].getDebugName(4)
                except Exception:
                    pass
                if name_record and self.is_valid_font_name(name_record):
                    names.append((name_record, f"{file_path},{i}"))
        except Exception as e:
            logger.warning(f"TTC parse failed {file_path}: {e}")
        return names

    def get_installed_fonts(self) -> List[str]:
        """构建安全的系统字体回退列表，首位保证为已注册字体 STSong-Light"""
        safe_defaults = ["STSong-Light"]

        # 收集系统字体（示例：从 ReportLab 已注册字体或系统路径扫描，这里保持简化）
        registered = list(getattr(pdfmetrics, "_fonts", {}).keys())
        system_fonts = []
        for n in registered:
            if self.is_valid_font_name(n):
                system_fonts.append(n)

        # 合并并去重，保证 STSong-Light 在首位
        seen = set()
        final = []
        for n in safe_defaults + self.FONTS + system_fonts:
            if n not in seen and self.is_valid_font_name(n):
                final.append(n)
                seen.add(n)

        logger.debug(f"Font fallback order: {final[:10]} ... total {len(final)}")
        return final

    def normalize_font_name(self, font_name):
        """将字体名称规范化，例如 'Times New Roman Bold' -> 'TimesNewRoman-Bold'"""
        # 替换空格为无
        normalized = font_name.replace(' ', '')
        # 处理常见的样式后缀
        for style in ['Bold', 'Italic', 'Regular', 'Light', 'Medium']:
            # 只有当样式后缀不是以连字符开头时才添加连字符
            # 避免重复添加连字符，如 STsong-Light 不会变成 STsong--Light
            if style in normalized and f'-{style}' not in normalized:
                normalized = normalized.replace(style, f'-{style}')

        # 特殊字体名规范
        if normalized == "TimesNewRoman":
            normalized = normalized.replace("TimesNewRoman", "Times-Roman")
        return normalized

    def normalize_font_nameV2(self, font_name: str) -> str:
        """字体名归一化：
        - 增强版本，支持更多字体名称映射
        - 去除多余空格，统一大小写风格
        - 针对规格型号和总价等特殊字段的字体做特殊处理
        """
        if not isinstance(font_name, str):
            return self.all_fonts[0] if self.all_fonts else "STSong-Light"
        
        name = font_name.strip()
        if not name:
            return self.all_fonts[0] if self.all_fonts else "STSong-Light"

        # 转换为小写用于匹配，保留原始名称的大小写风格
        name_lower = name.lower().replace(" ", "")
        
        # 字体名称映射字典
        font_mappings = {
            "timesnewroman": "Times-Roman",
            "simsun": "SimSun",
            "simhei": "SimHei",
            "simsong": "SimSun",
            "kai": "KaiTi",
            "simkai": "KaiTi",
            "fangsong": "FangSong",
            "msyh": "Microsoft YaHei",
            "microsoftyahei": "Microsoft YaHei",
            "pingfang": "PingFang SC",
            "pingfangsc": "PingFang SC",
            "songti": "Songti SC",
            "sourcehanserif": "Source Han Serif SC",
            "sourcehansans": "Source Han Sans SC",
            "helvetica": "Helvetica",
            "courier": "Courier"
        }
        
        # 查找映射
        if name_lower in font_mappings:
            mapped_font = font_mappings[name_lower]
            # 检查映射后的字体是否可用
            if mapped_font in self.FONTS:
                return mapped_font
            
        # 检查原始字体名是否在可用列表中
        if name in self.FONTS:
            return name
        
        # 尝试模糊匹配（前缀匹配）
        for font in self.FONTS:
            if font.lower().startswith(name_lower[:min(5, len(name_lower))]):
                return font
        
        # 针对规格型号和总价字段的特殊处理：优先使用等宽字体或中文字体
        # 检查是否包含数字、特殊符号等需要等宽显示的内容
        if re.search(r"[0-9%@#$&*()\[\]{}]", name):
            # 尝试使用等宽字体
            for mono_font in ["Courier", "SimHei", "Microsoft YaHei"]:
                if mono_font in self.FONTS:
                    return mono_font
        
        # 最后回退到第一个可用字体
        return self.FONTS[0] if self.FONTS else "STSong-Light"

    def register_font(self, file_name: str, font_name: str, font_b64: str):
        """注册嵌入字体（来自 OFD 的 base64 字体数据）
        - file_name: 原始字体文件名（用于暂存写入）
        - font_name: 希望注册的字体名称（OFD 提供的 @FontName）
        - font_b64: base64 编码的字体二进制
        """
        if not font_b64:
            return

        # 计算安全的字体名
        base_name = os.path.splitext(os.path.basename(file_name))[0]
        safe_name = self.normalize_font_name(font_name or base_name)
        if not self.is_valid_font_name(safe_name):
            safe_name = self.normalize_font_name(base_name) or "OFD-Fallback"

        # 暂存路径（写入后注册，再清理）
        out_dir = self.font_dir if self.font_dir else "."
        out_path = os.path.join(out_dir, os.path.basename(file_name))

        try:
            # 解码并写入临时文件
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(font_b64))

            pdfmetrics.registerFont(TTFont(safe_name, out_path))
            if safe_name not in self.FONTS:
                self.FONTS.append(safe_name)
            logger.info(f"Registered font '{safe_name}' from '{out_path}'")
        except Exception as e:
            logger.error(f"register_font_error: {e} \n包含不支持解析字体格式或字体文件异常")
        finally:
            try:
                if os.path.exists(out_path):
                    os.remove(out_path)
            except Exception:
                pass

