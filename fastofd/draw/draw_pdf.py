#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME: E:\code\easyofd\easyofd\draw
# CREATE_TIME: 2023-08-10
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# NOTE:  绘制pdf
import base64
import re
import time
import traceback
from io import BytesIO
import concurrent.futures
import io

from pypdf import PdfReader, PdfWriter
from PIL import Image as PILImage
from loguru import logger
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from fastofd.draw.font_tools import FontTool
from .find_seal_img import SealExtract


# print(reportlab_fonts)
class DrawPDF():
    """
    ofd 解析结果 绘制pdf
    OP ofd 单位转换
    """

    def __init__(self, data, *args, **kwargs):
        assert data, "未输入ofd解析结果"
        self.data = data
        self.author = "ihadyou"
        self.OP = 72 / 25.4
        # self.OP = 1
        self.pdf_uuid_name = self.data[0]["pdf_name"]
        self.pdf_io = BytesIO()
        self.SupportImgType = ("JPG", "JPEG", "PNG")
        # 使用已注册的基础中文字体作为默认字体，避免未注册的“宋体”导致异常
        self.init_font = "STSong-Light"
        self.font_tool = FontTool()
        # 文本渲染模式：'line'（整行写入优先，超出边界回退到字符写入）或'char'（始终使用字符写入）
        self.render_mode = kwargs.get('render_mode', 'line')
        
        # 并发处理相关配置参数
        self.max_workers = kwargs.get('max_workers', None)  # None表示自动计算
        self.single_thread_threshold = kwargs.get('single_thread_threshold', 10)  # 页面数量阈值，低于此值使用单线程
        self.min_pages_per_chunk = kwargs.get('min_pages_per_chunk', 1)  # 每个子PDF的最小页数
        self.optimized_pages_per_chunk = kwargs.get('optimized_pages_per_chunk', 5)  # 优化性能的每块页数
        self.force_single_thread = kwargs.get('force_single_thread', False)  # 强制使用单线程模式

    def draw_lines(my_canvas):
        """
        draw_line
        """
        my_canvas.setLineWidth(.3)

        start_y = 710
        my_canvas.line(30, start_y, 580, start_y)

        for x in range(10):
            start_y -= 10
            my_canvas.line(30, start_y, 580, start_y)

    def gen_empty_pdf(self):
        """
        """
        c = canvas.Canvas(self.pdf_io)
        c.setPageSize(A4)
        c.setFont(self.init_font, 20)
        c.drawString(0, 210, "ofd 格式错误,不支持解析", mode=1)
        c.save()


    def _expand_delta(self, DeltaRule: str) -> list[float]:
        """
        把 DeltaRule 展开成纯粹的浮点增量列表
        支持 g <count> <value> 语法
        """
        if not DeltaRule.strip():
            return []

        tokens = DeltaRule.strip().split()
        out, i = [], 0
        while i < len(tokens):
            tok = tokens[i]
            if tok == "g" and i + 2 < len(tokens):
                count = int(tokens[i + 1])
                value = float(tokens[i + 2])
                out.extend([value] * count)
                i += 3
            else:
                out.append(float(tok))
                i += 1
        return out


    def cmp_offsetV2(self, pos, offset, DeltaRule, text, CTM_info, dire="X") -> list[float]:
        """
        返回每个字符在 dire 方向上的绝对坐标（mm）
        """
        # ---- 1. 计算变换参数 ----
        if CTM_info:
            resize = CTM_info.get(f"resize{dire}", 1.0)
            move   = CTM_info.get(f"move{dire}",   0.0)
        else:
            resize, move = 1.0, 0.0

        # ---- 2. 展开增量 ----
        deltas = self._expand_delta(DeltaRule)          # 仅增量
        # 长度对齐：不足的间隙用“最后一个增量值”补齐，避免 0 造成重叠
        needed = (len(text) - 1) - len(deltas)
        if needed > 0:
            pad_val = deltas[-1] if deltas else 0.0
            deltas.extend([pad_val] * needed)

        # ---- 3. 首字符起点 ----
        start = float(pos or 0.0) + (float(offset or 0.0) + move) * resize
        coords = [start]

        # ---- 4. 累加 ----
        for d in deltas:
            start += d * resize
            coords.append(start)

        return coords[:len(text)]


    def draw_chars(self, canvas, text_list, fonts, page_size):
        """写入字符"""
        c = canvas
        for line_dict in text_list:
            # if line_dict.get("ID") == "246":
            #     print('>>>>>>>')
            
            text = line_dict.get("text")
            # font_info = fonts.get(line_dict.get("font"), {})
            # if font_info:
            #     font_name = font_info.get("FontName", "")
            # else:
            #     font_name = self.init_font

            # # TODO 判断是否通用已有字体 否则匹配相近字体使用
            # if font_name not in self.font_tool.FONTS:
            #     font_name = self.init_font

            # font = self.font_tool.normalize_font_name(font_name)

            font = self.init_font
            
            # 原点在页面的左下角 
            color = line_dict.get("color", [0, 0, 0])
            if len(color) < 3:
                color = [0, 0, 0]

            c.setFillColorRGB(int(color[0]) / 255, int(color[1]) / 255, int(color[2]) / 255)
            c.setStrokeColorRGB(int(color[0]) / 255, int(color[1]) / 255, int(color[2]) / 255)

            DeltaX = line_dict.get("DeltaX", "")
            DeltaY = line_dict.get("DeltaY", "")
            # print("DeltaX",DeltaX)
            X = line_dict.get("X", "")
            Y = line_dict.get("Y", "")
            CTM = line_dict.get("CTM", "")  # 因为ofd 增加这个字符缩放
            pos = line_dict.get("pos", [])
            resizeX = 1
            resizeY = 1
            # CTM =None # 有的数据不使用这个CTM
            if CTM and (CTMS:=CTM.split(" ")) and len(CTMS) == 6:
                CTM_info = {
                    "resizeX": float(CTMS[0]),
                    "rotateX": float(CTMS[1]),
                    "rotateY": float(CTMS[2]),
                    "resizeY": float(CTMS[3]),
                    "moveX": float(CTMS[4]),
                    "moveY": float(CTMS[5]),
                }
                resizeY = CTM_info.get("resizeY")
                font_size = line_dict["size"] * self.OP * resizeY
            else:
                CTM_info ={}
                font_size = line_dict["size"] * self.OP

            if pos and len(pos) == 4:
                x_mm = pos[0]
                y_mm = pos[1]
                width_mm = pos[2]
                height_mm = pos[3]

            x_list = self.cmp_offsetV2(x_mm, X, DeltaX, text, CTM_info, dire="X")
            y_list = self.cmp_offsetV2(y_mm, Y, DeltaY, text, CTM_info, dire="Y")

            # 检查文本长度是否超过坐标列表长度
            # 如果文本长度大于x坐标列表或y坐标列表，需要进行处理
            text_length = len(text)
            has_coordinate_mismatch = (
                text_length > len(x_list) or  # 文本长度超过x坐标列表
                text_length > len(y_list)     # 文本长度超过y坐标列表
            )
            
            if has_coordinate_mismatch:
                text = re.sub("[^\u4e00-\u9fa5]", "", text)
            try:
                # 计算最终坐标位置（考虑缩放因子）
                final_x = x_list[-1] * self.OP
                final_y = y_list[-1] * self.OP
                page_width = page_size[2] * self.OP
                page_height = page_size[3] * self.OP
                
                # 检查坐标是否超出页面边界或为负值
                is_outside_page = (
                    final_y > page_height or  # y坐标超出页面高度
                    final_x > page_width or    # x坐标超出页面宽度
                    x_list[-1] < 0 or          # 原始x坐标为负
                    y_list[-1] < 0             # 原始y坐标为负
                )
                
                # 渲染模式已在初始化时设置
                # 'line': 优先使用整行写入，如果超出边界则回退到字符写入
                # 'char': 始终使用字符写入，提供更精确的定位
                
                # 动态选择渲染模式的逻辑
                use_line_write = (self.render_mode == 'line' and not is_outside_page)
                
                # 尝试使用整行写入方式（当条件满足时）
                if use_line_write:
                    logger.debug(f"使用整行写入模式: {text}, ID={line_dict.get('ID')}")
                    
                    # 使用x_list和y_list中的精确坐标
                    if x_list and y_list:  # 确保坐标列表不为空
                        # 使用文本第一个字符的精确坐标作为起始位置
                        x_p = float(x_list[0]) * self.OP
                        y_p = (float(page_size[3]) - float(y_list[0])) * self.OP
                        
                        logger.debug(f"使用精确坐标绘制文本: x={x_p}, y={y_p}")
                    else:
                        # 作为回退方案，使用原有的X和Y坐标
                        x_p = abs(float(X)) * self.OP
                        y_p = abs(float(page_size[3]) - (float(Y))) * self.OP
                        logger.debug(f"使用回退坐标绘制文本: x={x_p}, y={y_p}")
                    
                    # 设置字体并绘制文本
                    font = self._set_font_with_fallback(c, font, font_size)
                    c.drawString(x_p, y_p, text, mode=0)  # mode=3 文字不可见 0可見
                    # text_write.append((x_p,  y_p, text))
                else:
                    # 使用字符写入模式（当self.render_mode为'char'或line模式下超出边界时）
                    fallback_reason = "超出页面边界" if self.render_mode == 'line' and is_outside_page else "选择了字符渲染模式"
                    logger.debug(f"使用字符写入模式 ({fallback_reason}): {text}, ID={line_dict.get('ID')}")
                    
                    # 按字符写入
                    for cahr_id, _cahr_ in enumerate(text):
                        if len(x_list) > cahr_id:
                            # 计算单个字符的精确位置
                            _cahr_x = float(x_list[cahr_id]) * self.OP
                            _cahr_y = (float(page_size[3]) - (float(y_list[cahr_id]))) * self.OP
                            
                            # 使用封装的字体设置方法
                            font = self._set_font_with_fallback(c, font, font_size)
                                
                            # 记录字符绘制信息
                            logger.debug(f"绘制字符: ID={line_dict.get('ID')}, 字符='{_cahr_}', 坐标=({_cahr_x}, {_cahr_y}), 字体={font}, 字号={font_size}")
                            c.drawString(_cahr_x, _cahr_y, _cahr_, mode=0) 
                        else:
                            logger.debug(f"字符 '{_cahr_}' 缺少位置信息，文本='{text}', 坐标列表={x_list}")
                        # text_write.append((_cahr_x,  _cahr_y, _cahr_))
            except Exception as e:
                logger.error(f"文本绘制错误: {e}")
                traceback.print_exc()
        

    def compute_ctm(self, CTM,x1, y1, img_width, img_height):
        """待定方法"""
        a,b,c,d,e,f = CTM.split(" ")
        a, b, c, d, e, f = float(a), float(b), float(c), float(d),float(e), float(f)
        # 定义变换矩阵的元素

        # 计算原始矩形的宽和高
        x2 = x1 + img_width
        y2 = y1 + img_height
        # print(f"ori x1 {x1} y1 {y1} x2 {x2} y2 {y2} img_width {img_width} img_height {img_height}")
        a = a/10
        d = d/10
        # 对左上角和右下角点进行变换
        x1_new = a * x1 + c * y1 + (e )
        y1_new = b * x1 + d * y1 + (f)
        x2_new = a * x2 + c * y2 + (e)
        y2_new = b * x2 + d * y2 + (f)
        # print(f"x1_new {x1_new} y1_new {y1_new} x2_new {x2_new} y2_new {y2_new}")
        # 计算变换后矩形的宽和高
        w_new = x2_new - x1_new
        h_new = y2_new - y1_new

        # print(f"原始矩形宽度: {img_width}, 高度: {img_height}")
        # print(f"变换后矩形宽度: {w_new}, 高度: {h_new}")
        return x1_new, y1_new, w_new, h_new

    def draw_img(self, canvas, img_list, images, page_size):
        """写入图片"""
        c = canvas
        # 用于存储已解码的图片，实现简单的图片缓存
        decoded_images_cache = {}
        
        for img_d in img_list:
            resource_id = img_d["ResourceID"]
            image = images.get(resource_id)

            if not image or image.get("suffix").upper() not in self.SupportImgType:
                continue
            
            # 使用缓存减少重复解码
            if resource_id not in decoded_images_cache:
                imgbyte = base64.b64decode(image.get('imgb64'))
                if not imgbyte:
                    logger.error(f"{image['fileName']} is null")
                    continue
                
                # 计算并缓存图片尺寸，避免创建不必要的ImageReader对象
                with PILImage.open(BytesIO(imgbyte)) as img:
                    img_width, img_height = img.size
                    # 缓存图片数据和尺寸
                    decoded_images_cache[resource_id] = {
                        'imgbyte': imgbyte,
                        'width': img_width,
                        'height': img_height
                    }
            else:
                # 使用缓存的尺寸信息
                img_width = decoded_images_cache[resource_id]['width']
                img_height = decoded_images_cache[resource_id]['height']

            CTM = img_d.get('CTM')
            wrap_pos = img_d.get("wrap_pos")
            pos = img_d.get('pos')

            # 仅在需要绘制时创建ImageReader对象，并在使用后释放
            if CTM and not wrap_pos and page_size == pos:
                x1_new, y1_new, w_new, h_new = self.compute_ctm(CTM, 0, 0, img_width, img_height)
                pdf_pos = [pos[0] * self.OP, pos[1] * self.OP, pos[2] * self.OP, pos[3] * self.OP]

                x1_new = (pos[0] + x1_new) * self.OP
                y1_new = (page_size[3] - y1_new) * self.OP
                if w_new > pdf_pos[2]:
                    w_new = pdf_pos[2]
                if h_new > pdf_pos[3]:
                    h_new = pdf_pos[3]
                
                # 在需要时才创建ImageReader，使用后会自动释放
                with PILImage.open(BytesIO(decoded_images_cache[resource_id]['imgbyte'])) as img:
                    imgReade = ImageReader(img)
                    c.drawImage(imgReade, x1_new, y1_new, w_new, -h_new, 'auto')
                    # 显式删除不再使用的对象
                    del imgReade
            else:
                x_offset = 0
                y_offset = 0

                x = (pos[0] + x_offset) * self.OP
                y = (page_size[3] - (pos[1] + y_offset)) * self.OP
                if wrap_pos:
                    x = x + (wrap_pos[0] * self.OP)
                    y = y - (wrap_pos[1] * self.OP)
                    w = img_d.get('pos')[2] * self.OP
                    h = -img_d.get('pos')[3] * self.OP

                    # 按需创建ImageReader
                    with PILImage.open(BytesIO(decoded_images_cache[resource_id]['imgbyte'])) as img:
                        imgReade = ImageReader(img)
                        c.drawImage(imgReade, x, y, w, h, 'auto')
                        del imgReade
                elif pos:
                    x = pos[0] * self.OP
                    y = (page_size[3] - pos[1]) * self.OP
                    w = pos[2] * self.OP
                    h = -pos[3] * self.OP

                    # 按需创建ImageReader
                    with PILImage.open(BytesIO(decoded_images_cache[resource_id]['imgbyte'])) as img:
                        imgReade = ImageReader(img)
                        c.drawImage(imgReade, x, y, w, h, 'auto')
                        del imgReade
        
        # 清理缓存，帮助垃圾回收
        decoded_images_cache.clear()

    def draw_signature(self, canvas, signatures_page_list, page_size):
        """
        写入签章
            {
            "sing_page_no": sing_page_no,
            "PageRef": PageRef,
            "Boundary": Boundary,
            "SignedValue": self.file_tree(SignedValue),
                            }
        """
        c = canvas
        try:
            if signatures_page_list:
                # print("signatures_page_list",signatures_page_list)
                for signature_info in signatures_page_list:
                    image = SealExtract()(b64=signature_info.get("SignedValue"))
                    if not image:
                        logger.info(f"提取不到签章图片")
                        continue
                    else:
                        image_pil = image[0]

                    pos = [float(i) for i in signature_info.get("Boundary").split(" ")]

                    imgReade = ImageReader(image_pil)

                    x = pos[0] * self.OP
                    y = (page_size[3] - pos[1]) * self.OP

                    w = pos[2] * self.OP
                    h = -pos[3] * self.OP
                    c.drawImage(imgReade, x, y, w, h, 'auto')
                    logger.debug(f"签章写入成功")
            else:
                # 无签章
                pass
        except Exception as e:
            logger.error(f"签章写入失败 {e}")
            traceback.print_exc()

    def draw_line_old(self, canvas, line_list, page_size):
        """绘制线条"""

        # print("绘制",line_list)

        def match_mode(Abbr: list):
            """
            解析AbbreviatedData
            匹配各种线条模式
            S 定义起始 坐标 x, y
            M 移动到指定坐标 x, y
            L 从当前点移动到指定点 x, y
            Q x1 y1 x2 y2 二次贝塞尔曲线
            B x1 y1 x2 y2 x3 y3 三次贝塞尔曲线
            A 到 x,y 的圆弧 并移动到 x,y  rx 长轴 ry 短轴 angle 旋转角度 large为1表示 大于180 的弧 为0时表示小于180的弧 swcpp 为1 表示顺时针旋转 0 表示逆时针旋转
            C 当前点和SubPath自动闭合
            """
            relu_list = []
            mode = ""
            modes = ["S", "M", "L", "Q", "B", "A", "C"]
            mode_dict = {}
            for idx, i in enumerate(Abbr):
                if i in modes:
                    mode = i
                    if mode_dict:
                        relu_list.append(mode_dict)
                    mode_dict = {"mode": i, "points": []}

                else:
                    mode_dict["points"].append(i)

                if idx + 1 == len(Abbr):
                    relu_list.append(mode_dict)
            return relu_list

        def assemble(relu_list: list):
            start_point = {}
            acticon = []
            for i in relu_list:
                if i.get("mode") == "M":
                    start_point = i
                elif i.get("mode") in ['B', "Q", 'L']:
                    acticon.append({"start_point": start_point,
                                    "end_point": i
                                    })
            return acticon

        def convert_coord(p_list, direction, page_size, pos):
            """坐标转换ofd2pdf"""
            new_p_l = []
            for p in p_list:
                if direction == "x":

                    new_p = (float(pos[0]) + float(p)) * self.OP
                else:
                    new_p = (float(page_size[3]) - float(pos[1]) - float(p)) * self.OP
                new_p_l.append(new_p)
            return new_p_l

        for line in line_list:
            Abbr = line.get("AbbreviatedData").split(" ")  # AbbreviatedData 
            color = line.get("FillColor", [0, 0, 0])

            relu_list = match_mode(Abbr)
            # TODO 组合 relu_list 1 M L 直线 2 M B*n 三次贝塞尔线 3 M Q*n 二次贝塞尔线

            # print(relu_list)

            acticons = assemble(relu_list)
            pos = line.get("pos")
            # print(color)
            if len(color) < 3:
                color = [0, 0, 0]
            canvas.setStrokeColorRGB(*(int(color[0]) / 255, int(color[1]) / 255, int(color[2]) / 255))  # 颜色

            # 设置线条宽度
            try:
                LineWidth = (float(line.get("LineWidth", "0.25").replace(" ", "")) if \
                                 line.get("LineWidth", "0.25").replace(" ", "") else 0.25) * self.OP
            except Exception as e:
                logger.error(f"{e}")
                LineWidth = 0.25 * self.OP

            canvas.setLineWidth(LineWidth)  # 单位为点，2 表示 2 点

            for acticon in acticons:
                if acticon.get("end_point").get("mode") == 'L':  # 直线
                    x1, y1, x2, y2 = *acticon.get("start_point").get("points"), *acticon.get("end_point").get("points")
                    x1, x2 = convert_coord([x1, x2], "x", page_size, pos)
                    y1, y2 = convert_coord([y1, y2], "y", page_size, pos)
                    # 绘制一条线 x1 y1 x2 y2
                    canvas.line(x1, y1, x2, y2)

                elif acticon.get("end_point").get("mode") == 'B':  # 三次贝塞尔线
                    continue
                    x1, y1, x2, y2, x3, y3, x4, y4 = *acticon.get("start_point").get("points"), *acticon.get(
                        "end_point").get("points")
                    x1, x2, x3, x4 = convert_coord([x1, x2, x3, x4], "x", page_size, pos)
                    y1, y2, y3, y4 = convert_coord([y1, y2, y3, y4], "y", page_size, pos)
                    # print(x1, y1, x2, y2, x3, y3, x4, y4)

                    # 绘制三次贝塞尔线
                    canvas.bezier(x1, y1, x2, y2, x3, y3, x4, y4)

                elif acticon.get("end_point").get("mode") == 'Q':  # 二次贝塞尔线
                    pass
                else:
                    continue

    def draw_line(self, canvas, line_list, page_size):
        def match_mode(Abbr: list):
            """
            解析AbbreviatedData
            匹配各种线条模式
            S 定义起始 坐标 x, y
            M 移动到指定坐标 x, y
            L 从当前点移动到指定点 x, y
            Q x1 y1 x2 y2 二次贝塞尔曲线 从当前点连接一条到点(x2,y2)的二次贝塞尔曲线，并将当前点移动到点(x2,y2)，此贝塞尔曲线使用点(x1,y1)作为其控制点。
            B x1 y1 x2 y2 x3 y3 三次贝塞尔曲线 从当前点连接一条到点(x3,y3)的三次贝塞尔曲线，并将当前点移动到点(x3,y3)，此贝塞尔曲线使用点(x1,y1)和点(x2,y2)作为其控制点。
            A Are 操作数为rx ry angle large sweep x y，从当前点连接一条到点(x,y)的圆弧，并将当前点移动到点(x,y)。
            其中，rx表示椭圆的长轴长度，ry表示椭圆的短轴长度，angle表示椭圆在当前坐标系下旋转的角度，正值为顺时针，
            负值为逆时针，large为 1 时表示对应度数大于 180° 的弧，为 0 时表示对应度数小于 180° 的弧，
            sweep为 1 时表示由圆弧起始点到结束点是顺时针旋转，为 0 时表示由圆弧起始点到结束点是逆时针旋转。
            C 无操作数，其作用是SubPath自动闭合，表示将当前点和SubPath的起始点用线段直接连接。
            """
            relu_list = []
            mode = ""
            modes = ["S", "M", "L", "Q", "B", "A", "C"]
            mode_dict = {}
            for idx, i in enumerate(Abbr):
                if i in modes:
                    mode = i
                    if mode_dict:
                        relu_list.append(mode_dict)
                    mode_dict = {"mode": i, "points": []}

                else:
                    mode_dict["points"].append(i)

                if idx + 1 == len(Abbr):
                    relu_list.append(mode_dict)
            return relu_list

        def assemble(relu_list: list):
            start_point = {}
            acticon = []

            for i in relu_list:
                if i.get("mode") == "M":
                    if not start_point:
                        start_point = i
                    acticon.append({
                        "start_point": start_point,"end_point": i})

                elif i.get("mode") in ['B', "Q", 'L']:
                    acticon.append({"start_point": start_point,
                                    "end_point": i
                                    })
                elif i.get("mode") == "C":
                    acticon.append({"start_point": start_point,
                                    "end_point": i
                                    })
                elif i.get("mode") == "A":
                    acticon.append({"start_point": start_point,
                                    "end_point": i
                                    })
                elif i.get("mode") == "S":
                    start_point = i

            return acticon

        def convert_coord(p_list, direction, page_size, pos):
            """坐标转换ofd2pdf"""
            new_p_l = []
            # print("p_list", p_list)
            for p in p_list:
                if direction == "x":
                    new_p = (float(pos[0]) + float(p)) * self.OP
                else:
                    new_p = (float(page_size[3]) - float(pos[1]) - float(p)) * self.OP
                new_p_l.append(new_p)
            # print("new_p_l", new_p_l)
            return new_p_l

        for line in line_list:
            path = canvas.beginPath()
            Abbr = line.get("AbbreviatedData").split(" ")  # AbbreviatedData
            color = line.get("FillColor", [0, 0, 0])

            relu_list = match_mode(Abbr)
            # TODO 组合 relu_list 1 M L 直线 2 M B*n 三次贝塞尔线 3 M Q*n 二次贝塞尔线

            # print(relu_list)

            acticons = assemble(relu_list)
            pos = line.get("pos")
            # print(color)
            if len(color) < 3:
                color = [0, 0, 0]
            canvas.setStrokeColorRGB(*(int(color[0]) / 255, int(color[1]) / 255, int(color[2]) / 255))  # 颜色

            # 设置线条宽度
            try:
                LineWidth = (float(line.get("LineWidth", "0.25").replace(" ", "")) if \
                                 line.get("LineWidth", "0.25").replace(" ", "") else 0.25) * self.OP
            except Exception as e:
                logger.error(f"{e}")
                LineWidth = 0.25 * self.OP

            canvas.setLineWidth(LineWidth)  # 单位为点，2 表示 2 点
            cur_point = []
            for acticon in acticons:
                if acticon.get("end_point").get("mode") == 'M':
                    x, y = acticon.get("end_point").get("points")
                    x = convert_coord([x], "x", page_size, pos)[0]
                    y = convert_coord([y], "y", page_size, pos)[0]
                    cur_point = [x, y]
                    path.moveTo(x, y)

                elif acticon.get("end_point").get("mode") == 'L':  # 直线
                    x, y = acticon.get("end_point").get("points")
                    x = convert_coord([x], "x", page_size, pos)[0]
                    y = convert_coord([y], "y", page_size, pos)[0]
                    path.lineTo(x, y)


                elif acticon.get("end_point").get("mode") == 'B':  # 三次贝塞尔线
                    x1, y1, x2, y2, x3, y3 = acticon.get("end_point").get("points")
                    # print(x1, y1, x2, y2, x3, y3)
                    x1, x2,x3 = convert_coord([x1, x2,x3], "x", page_size, pos)
                    y1, y2,y3 = convert_coord([y1, y2,y3], "y", page_size, pos)
                    cur_point = [x2, y2]
                    path.curveTo(x1, y1, x2, y2, x3, y3)
                    path.moveTo(x3, y3)

                elif acticon.get("end_point").get("mode") == 'Q':  # 二次贝塞尔线
                    x1, y1, x2, y2 = acticon.get("end_point").get("points")
                    x1, x2 = convert_coord([x1, x2], "x", page_size, pos)
                    y1, y2 = convert_coord([y1, y2], "y", page_size, pos)
                    cur_point = [x2, y2]
                    path.curveTo(x1, y1, x2, y2, x2, y2)
                    path.moveTo(x2, y2)
                elif acticon.get("end_point").get("mode") == 'A':  # 圆弧线
                    x1, y1 = acticon.get("start_point").get("points")
                    rx, ry, startAng, large_arc_flag, sweep_flag, x2, y2 = acticon.get("end_point").get("points")
                    rx_o = rx
                    ry_o = ry

                    x1,x2,rx = convert_coord([x1,x2,rx], "x", page_size, pos)
                    y1,y2,ry = convert_coord([y1,y2,ry], "y", page_size, pos)

                    cur_x,cur_y=cur_point

                    # 绘制圆弧 有问题
                    if rx_o==ry_o:
                        # path.circle(cur_x,cur_y, 20) # 圆
                        path.circle(rx,ry, 20) # 圆 # 莫名其妙的圆
                    else:
                        # print(rx, ry, x2, y2, startAng, large_arc_flag, sweep_flag)
                        path.ellipse(rx, ry,20, 20, ) # 椭圆
                    # path.arc(rx, ry, x2, y2, startAng=int(startAng), extent=int(sweep_flag))
                    # path.ellipse(rx, ry,x2, y2, ) # 椭圆
                    # path.curveTo(rx, ry ,x2, y2, startAng=int(startAng), extent=int(sweep_flag))
                    path.moveTo(x2, y2)
                    cur_point = [x2,y2]

                elif acticon.get("end_point").get("mode") == 'C':
                    # canvas.drawPath(path)
                    path.close()
            canvas.drawPath(path)

    def _set_font_with_fallback(self, canvas_obj, font_name, font_size):
        """
        设置字体，如果指定字体不可用，尝试回退策略
        
        Args:
            canvas_obj: canvas对象
            font_name: 尝试设置的字体名称
            font_size: 字体大小
            
        Returns:
            str: 最终使用的字体名称
        """
        try:
            # 尝试设置指定字体
            canvas_obj.setFont(font_name, font_size)
            return font_name
        except KeyError as key_error:
            logger.error(f"Font error: {key_error}")
            
            # 多级字体回退策略
            fallback_attempted = False
            for fallback_font in self.font_tool.FONTS[:10]:  # 尝试更多字体
                try:
                    canvas_obj.setFont(fallback_font, font_size)
                    fallback_attempted = True
                    logger.debug(f"字体回退到: {fallback_font}")
                    return fallback_font
                except KeyError:
                    continue
            
            # 如果都失败了，使用ReportLab的默认字体
            if not fallback_attempted:
                try:
                    default_font = "Helvetica"
                    canvas_obj.setFont(default_font, font_size)
                    logger.debug(f"所有字体回退失败，使用默认字体: {default_font}")
                    return default_font
                except Exception as e:
                    logger.error(f"默认字体设置失败: {e}")
            
            # 返回原始字体名称作为最后的尝试
            return font_name
            
    def draw_annotation(self, canvas, annota_info, images, page_size):
        """
        绘制标注
        处理文档中的各种标注信息，包括签章图片等
        
        Args:
            canvas: canvas对象
            annota_info: 标注信息
            images: 图片字典
            page_size: 页面大小
        """
        img_list = []
        for key, annotation in annota_info.items():
            if annotation.get("AnnoType").get("type") == "Stamp":
                pos = annotation.get("ImgageObject").get("Boundary","").split(" ")
                pos = [float(i) for i in pos] if pos else []
                wrap_pos = annotation.get("Appearance").get("Boundary","").split(" ")
                wrap_pos = [float(i) for i in wrap_pos] if wrap_pos else []
                CTM = annotation.get("ImgageObject").get("CTM","").split(" ")
                CTM = [float(i) for i in CTM] if CTM else []
                img_list.append({
                    "wrap_pos": wrap_pos,
                    "pos": pos,
                    "CTM": CTM,
                    "ResourceID": annotation.get("ImgageObject").get("ResourceID",""),
                })
        self.draw_img( canvas, img_list, images, page_size)
        
    def draw_pdf_multithread(self):
        """
        生成PDF文件，使用并发处理优化性能
        由于ReportLab不是线程安全的，采用并发生成子PDF然后合并的策略
        
        可配置参数（通过__init__方法的kwargs传入）：
        - max_workers: 最大线程数，None表示自动计算（默认为CPU核心数和8的较小值）
        - single_thread_threshold: 页面数量阈值，低于此值使用单线程（默认10）
        - min_pages_per_chunk: 每个子PDF的最小页数（默认1）
        - optimized_pages_per_chunk: 优化性能的每块页数（默认5）
        - force_single_thread: 强制使用单线程模式（默认False）
        """

        can_merge_pdfs = True
        start_draw_time = time.time()
        
        # 收集所有页面任务
        all_pages = []
        for doc_id, doc in enumerate(self.data):
            fonts = doc.get("fonts")
            images = doc.get("images")
            default_page_size = doc.get("default_page_size")
            page_size_details = doc.get("page_size")
            signatures_page_id = doc.get("signatures_page_id")
            annotation_info = doc.get("annotation_info")
            
            for pg_no, page in doc.get("page_info").items():
                # 确定页面尺寸
                page_size_found = False
                if len(page_size_details) > pg_no and page_size_details[pg_no]:
                    page_size = page_size_details[pg_no]
                    page_size_found = True
                else:
                    page_size = default_page_size
                    logger.warning(f"页码 {pg_no} 未找到详细页面尺寸信息，使用默认尺寸")
                
                # 收集页面数据，用于后续处理
                page_data = {
                    'doc_id': doc_id,
                    'pg_no': pg_no,
                    'page': page,
                    'fonts': fonts,
                    'images': images,
                    'page_size': page_size,
                    'signatures_page_id': signatures_page_id,
                    'annotation_info': annotation_info,
                    'is_last_page': pg_no == len(doc.get("page_info")) - 1 and doc_id == len(self.data) - 1
                }
                all_pages.append(page_data)
        
        total_pages = len(all_pages)
        logger.info(f"开始处理 {total_pages} 页")
        
        # 如果页面数量很少、不能合并PDF或强制使用单线程，直接使用单线程模式
        if total_pages <= self.single_thread_threshold or not can_merge_pdfs or self.force_single_thread:
            logger.info("页面数量较少或无法合并PDF，使用单线程模式处理")
            # 使用原始的单线程方式处理
            c = canvas.Canvas(self.pdf_io)
            c.setAuthor(self.author)
            
            for page_data in all_pages:
                page = page_data['page']
                fonts = page_data['fonts']
                images = page_data['images']
                page_size = page_data['page_size']
                pg_no = page_data['pg_no']
                
                # 设置页面尺寸
                c.setPageSize((page_size[2] * self.OP, page_size[3] * self.OP))
                
                # 写入图片
                if page.get("img_list"):
                    self.draw_img(c, page.get("img_list"), images, page_size)
                
                # 写入文本
                if page.get("text_list"):
                    self.draw_chars(c, page.get("text_list"), fonts, page_size)
                
                # 绘制线条
                if page.get("line_list"):
                    self.draw_line(c, page.get("line_list"), page_size)
                
                # 绘制签章
                if page_data['signatures_page_id']:
                    self.draw_signature(c, page_data['signatures_page_id'].get(pg_no), page_size)
                
                # 绘制注释
                if page_data['annotation_info'] and pg_no in page_data['annotation_info']:
                    self.draw_annotation(c, page_data['annotation_info'].get(pg_no), images, page_size)
                
                # 显示下一页（除了最后一页）
                if not page_data['is_last_page']:
                    c.showPage()
            
            # 保存PDF
            c.save()
            logger.info(f"PDF内容已保存，绘制总耗时: {time.time() - start_draw_time:.2f}秒")
            return
        
        # 使用并发生成子PDF然后合并的方式
        logger.info("使用并发生成子PDF然后合并的策略优化性能")
        
        # 动态确定线程池大小
        import multiprocessing
        if self.max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), 8)  # 默认最多使用8个线程
        else:
            max_workers = max(1, self.max_workers)  # 确保至少有1个线程
        logger.info(f"使用线程池大小: {max_workers}")
        
        # 计算每个子PDF处理的页面数
        pages_per_chunk = max(self.min_pages_per_chunk, total_pages // (max_workers * 2))
        # 确保每个子PDF至少处理指定的优化页数（除非总页数少于max_workers*optimized_pages_per_chunk）
        if total_pages >= max_workers * self.optimized_pages_per_chunk:
            pages_per_chunk = max(pages_per_chunk, self.optimized_pages_per_chunk)
        
        # 将页面分成多个块
        chunks = []
        for i in range(0, total_pages, pages_per_chunk):
            chunk = all_pages[i:i + pages_per_chunk]
            # 确保最后一页标记正确
            if chunk:
                chunk[-1]['is_last_page'] = i + len(chunk) == total_pages
            chunks.append(chunk)
        
        logger.info(f"将 {total_pages} 页分成 {len(chunks)} 个子PDF进行并发处理，每块 {pages_per_chunk} 页")
        
        # 子PDF生成函数
        def generate_sub_pdf(chunk_pages):
            """生成子PDF文件"""
            try:
                # 创建内存中的PDF
                sub_pdf_io = io.BytesIO()
                c = canvas.Canvas(sub_pdf_io)
                c.setAuthor(self.author)
                
                for page_data in chunk_pages:
                    page = page_data['page']
                    fonts = page_data['fonts']
                    images = page_data['images']
                    page_size = page_data['page_size']
                    pg_no = page_data['pg_no']
                    
                    # 设置页面尺寸
                    c.setPageSize((page_size[2] * self.OP, page_size[3] * self.OP))
                    
                    # 写入图片
                    if page.get("img_list"):
                        self.draw_img(c, page.get("img_list"), images, page_size)
                    
                    # 写入文本
                    if page.get("text_list"):
                        self.draw_chars(c, page.get("text_list"), fonts, page_size)
                    
                    # 绘制线条
                    if page.get("line_list"):
                        self.draw_line(c, page.get("line_list"), page_size)
                    
                    # 绘制签章
                    if page_data['signatures_page_id']:
                        self.draw_signature(c, page_data['signatures_page_id'].get(pg_no), page_size)
                    
                    # 绘制注释
                    if page_data['annotation_info'] and pg_no in page_data['annotation_info']:
                        self.draw_annotation(c, page_data['annotation_info'].get(pg_no), images, page_size)
                    
                    # 显示下一页（除了块内最后一页）
                    if page_data != chunk_pages[-1]:
                        c.showPage()
                
                # 保存子PDF
                c.save()
                sub_pdf_io.seek(0)
                
                # 返回子PDF内容和页码范围
                first_page = chunk_pages[0]['pg_no'] if chunk_pages else -1
                last_page = chunk_pages[-1]['pg_no'] if chunk_pages else -1
                return {
                    'pdf_content': sub_pdf_io.getvalue(),
                    'first_page': first_page,
                    'last_page': last_page
                }
            except Exception as e:
                logger.error(f"生成子PDF失败（页码范围 {chunk_pages[0]['pg_no'] if chunk_pages else 'unknown'}-{chunk_pages[-1]['pg_no'] if chunk_pages else 'unknown'}）: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # 并发生成子PDF
        sub_pdfs = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {executor.submit(generate_sub_pdf, chunk): i for i, chunk in enumerate(chunks)}
            
            for future in concurrent.futures.as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    sub_pdf_result = future.result()
                    if sub_pdf_result:
                        sub_pdfs.append((chunk_idx, sub_pdf_result))
                        logger.info(f"子PDF {chunk_idx + 1}/{len(chunks)} 生成成功（页码: {sub_pdf_result['first_page']}-{sub_pdf_result['last_page']}）")
                except Exception as e:
                    logger.error(f"处理子PDF {chunk_idx + 1} 时发生异常: {e}")
        
        # 按顺序排序子PDF
        sub_pdfs.sort(key=lambda x: x[0])
        
        # 合并子PDF
        logger.info(f"开始合并 {len(sub_pdfs)} 个子PDF")
        merger = PdfWriter()
        
        for idx, sub_pdf_info in sub_pdfs:
            try:
                pdf_reader = PdfReader(io.BytesIO(sub_pdf_info['pdf_content']))
                for page in pdf_reader.pages:
                    merger.add_page(page)
                logger.info(f"已合并子PDF {idx + 1}/{len(sub_pdfs)}")
            except Exception as e:
                logger.error(f"合并子PDF {idx + 1} 时发生异常: {e}")
        
        # 保存合并后的PDF到self.pdf_io
        merger.write(self.pdf_io)
        merger.close()
        
        # 将self.pdf_io指针移到开始位置
        self.pdf_io.seek(0)
        
        logger.info(f"PDF合并完成，总耗时: {time.time() - start_draw_time:.2f}秒")
    
    def draw_pdf(self):
        """
        生成PDF文件，使用单线程处理
        适用于页面数量较少的场景，避免多线程的开销
        """
        start_draw_time = time.time()
        
        # 收集所有页面任务
        all_pages = []
        for doc_id, doc in enumerate(self.data):
            fonts = doc.get("fonts")
            images = doc.get("images")
            default_page_size = doc.get("default_page_size")
            page_size_details = doc.get("page_size")
            signatures_page_id = doc.get("signatures_page_id")
            annotation_info = doc.get("annotation_info")
            
            for pg_no, page in doc.get("page_info").items():
                # 确定页面尺寸
                page_size_found = False
                if len(page_size_details) > pg_no and page_size_details[pg_no]:
                    page_size = page_size_details[pg_no]
                    page_size_found = True
                else:
                    page_size = default_page_size
                    logger.warning(f"页码 {pg_no} 未找到详细页面尺寸信息，使用默认尺寸")
                
                # 收集页面数据，用于后续处理
                page_data = {
                    'doc_id': doc_id,
                    'pg_no': pg_no,
                    'page': page,
                    'fonts': fonts,
                    'images': images,
                    'page_size': page_size,
                    'signatures_page_id': signatures_page_id,
                    'annotation_info': annotation_info,
                    'is_last_page': pg_no == len(doc.get("page_info")) - 1 and doc_id == len(self.data) - 1
                }
                all_pages.append(page_data)
        
        total_pages = len(all_pages)
        logger.info(f"开始单线程处理 {total_pages} 页")
        
        # 使用单线程方式处理
        c = canvas.Canvas(self.pdf_io)
        c.setAuthor(self.author)
        
        for page_data in all_pages:
            page = page_data['page']
            fonts = page_data['fonts']
            images = page_data['images']
            page_size = page_data['page_size']
            pg_no = page_data['pg_no']
            
            # 设置页面尺寸
            c.setPageSize((page_size[2] * self.OP, page_size[3] * self.OP))
            
            # 写入图片
            if page.get("img_list"):
                self.draw_img(c, page.get("img_list"), images, page_size)
            
            # 写入文本
            if page.get("text_list"):
                self.draw_chars(c, page.get("text_list"), fonts, page_size)
            
            # 绘制线条
            if page.get("line_list"):
                self.draw_line(c, page.get("line_list"), page_size)
            
            # 绘制签章
            if page_data['signatures_page_id']:
                self.draw_signature(c, page_data['signatures_page_id'].get(pg_no), page_size)
            
            # 绘制注释
            if page_data['annotation_info'] and pg_no in page_data['annotation_info']:
                self.draw_annotation(c, page_data['annotation_info'].get(pg_no), images, page_size)
            
            # 显示下一页（除了最后一页）
            if not page_data['is_last_page']:
                c.showPage()
        
        # 保存PDF
        c.save()
        # 将self.pdf_io指针移到开始位置并返回PDF字节数据
        self.pdf_io.seek(0)
        logger.info(f"PDF内容已保存，单线程绘制总耗时: {time.time() - start_draw_time:.2f}秒")
        return self.pdf_io.getvalue()

    def __call__(self):
        start_time = time.time()
        try:
            self.draw_pdf()
            pdfbytes = self.pdf_io.getvalue()
            end_time = time.time()
            logger.info(f"PDF生成成功，耗时: {end_time - start_time:.2f}秒")
        except Exception as e:
            end_time = time.time()
            logger.error(f"{e}")
            logger.error(f"ofd解析失败，耗时: {end_time - start_time:.2f}秒")
            traceback.print_exc()
            self.gen_empty_pdf()
            pdfbytes = self.pdf_io.getvalue()
        return pdfbytes
