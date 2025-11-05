import os
from lxml import etree
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 定义路径
ofd_root = '/Users/mac/soft/studySpace/fastofd/金晟建设集团有限公司04整本响应文件 (12)(1)_xml/Doc_0'
# XML文件路径
xml_path = os.path.join(ofd_root, 'PublicRes.xml')
# 字体文件目录（根据XML中的BaseLoc="Res"）
public_res_path = os.path.join(ofd_root, 'Res')

# 解析 publicRes.xml 提取字体映射
def parse_fonts_from_public_res(xml_path):
    """
    从PublicRes.xml文件中解析字体信息
    :param xml_path: XML文件路径
    :return: 字体字典，key为FontName，value为字体文件路径
    """
    # 定义正确的命名空间
    ns = {'ofd': 'http://www.ofdspec.org/2016'}
    
    try:
        print(f"开始解析XML文件: {xml_path}")
        tree = etree.parse(xml_path)
        fonts = {}
        
        # 从根元素获取实际的命名空间，如果有差异则使用根元素的命名空间
        root = tree.getroot()
        print(f"XML根元素标签: {root.tag}")
        print(f"根元素命名空间映射: {root.nsmap}")
        
        if root.nsmap and None in root.nsmap:
            actual_ns = root.nsmap[None]
            print(f"使用实际的命名空间: {actual_ns}")
            ns['ofd'] = actual_ns
        
        # 使用正确的XPath查询字体元素
        font_elements = tree.xpath('//ofd:Font', namespaces=ns)
        print(f"找到Font元素数量: {len(font_elements)}")
        
        for font in font_elements:
            font_name = font.get('FontName')
            font_file_element = font.find('ofd:FontFile', namespaces=ns)
            font_file = font_file_element.text if font_file_element is not None else None
            
            # 只存储有字体文件名的字体
            if font_name and font_file:
                fonts[font_name] = font_file
                print(f"已解析字体: {font_name} -> {font_file}")
        
        print(f"总共解析到{len(fonts)}个字体")
        return fonts
    except Exception as e:
        print(f"解析XML出错: {e}")
        return {}

# 注册字体到 ReportLab
def register_fonts_from_ofd(fonts_map):
    """
    注册OFD字体到ReportLab
    :param fonts_map: 字体映射字典，key为FontName，value为字体文件路径
    """
    # 遍历字体映射字典
    for font_name, font_file in fonts_map.items():
        try:
            # 获取字体文件完整路径
            ttf_path = os.path.join(public_res_path, font_file)
            
            # 检查字体文件是否存在
            if os.path.exists(ttf_path):
                # 注册字体
                font_name_clean = font_name.split('+')[-1]  # 提取实际字体名（去除前缀）
                print(f"[+] 注册字体: {font_name_clean} -> {ttf_path}")
                pdfmetrics.registerFont(TTFont(font_name, ttf_path))
                pdfmetrics.registerFont(TTFont(font_name_clean, ttf_path))
            else:
                print(f"[-] 字体文件不存在: {ttf_path}")
        except Exception as e:
            print(f"[-] 注册字体失败: {font_name} - {e}")

# 示例：使用字体绘制文本
def create_sample_pdf(output_path):
    """
    创建使用OFD字体的示例PDF
    :param output_path: 输出PDF路径
    """
    # 解析字体
    fonts_map = parse_fonts_from_public_res(xml_path)
    print(pdfmetrics._fonts.keys())
    
    register_fonts_from_ofd(fonts_map)

    # 所有已注册字体名（含内置 14 种）
    print(pdfmetrics._fonts.keys())

    # 仅想看你自己注册的 TTF/OTF 字体（排除 Base-14）
    ttf_fonts = {k for k, v in pdfmetrics._fonts.items()
                if v.__class__.__name__ in ('TTFont', 'TTFontFile')}
    print('TTF 字体:', ttf_fonts)

    c = canvas.Canvas(output_path)
    y_position = 750
    
    # 尝试使用所有字体绘制文本
    for font_name in fonts_map.keys():
        try:
            # 设置字体并绘制文本
            c.setFont(font_name, 14)
            c.drawString(100, y_position, f"字体测试: {font_name}")
            y_position -= 20
            
            # 检查是否需要换页
            if y_position < 100:
                c.showPage()
                y_position = 750
        except Exception as e:
            print(f"[-] 使用字体失败: {font_name} - {e}")
    
    # 保存PDF
    c.save()
    print(f"[+] 示例PDF已生成: {output_path}")

# 运行
if __name__ == '__main__':
    create_sample_pdf('output_with_ofd_fonts.pdf')