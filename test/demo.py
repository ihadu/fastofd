#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PROJECT_NAME: F:\code\easyofd\test
# CREATE_TIME: 2023-10-18
# E_MAIL: renoyuan@foxmail.com
# AUTHOR: reno
# note:  use demo
import base64
import os
import sys
import time

# 配置日志级别为INFO，只打印INFO及以上级别的日志
from loguru import logger
logger.remove()  # 移除默认的日志处理器
logger.add(sys.stdout, level="INFO")  # 添加一个新的处理器，只输出INFO级别日志

from PIL import Image
from PIL.Image import Image as ImageClass

project_dir = os.path.join(os.path.dirname(os.getcwd()), "fastofd")
pkg_dir = os.path.dirname(os.getcwd())
print(project_dir)
print(pkg_dir)
sys.path.insert(0, project_dir)
sys.path.insert(0, pkg_dir)

from fastofd.ofd import OFD


def test_img2(dir_path):
    """
    jpg2ofd 
    jpg2pfd
    """
    # img_path = os.path.join(".", r"test\Doc_0\Res") # 多页排序问题
    imgs_p = os.listdir(dir_path)
    imgs = []
    for img_p in imgs_p:
        imgs.append(Image.open(os.path.join(dir_path, img_p)))  # 传入改为pil
    ofdbytes = OFD().jpg2ofd(imgs)
    pdfbytes = OFD().jpg2pfd(imgs)
    with open(r"img2test.pdf", "wb") as f:
        f.write(pdfbytes)
    with open(r"img2test.ofd", "wb") as f:
        f.write(ofdbytes)


def test_ofd2(file_path, output_dir=None):
    """
    ofd2pdf
    ofd2img
    """
    # with open(r"0e7ff724-1011-4544-8464-ea6c025f6ade.ofd","rb") as f:

    file_prefix = os.path.splitext(os.path.split(file_path)[1])[0]
    with open(file_path, "rb") as f:
        ofdb64 = str(base64.b64encode(f.read()), "utf-8")
    ofd = OFD()  # 初始化OFD 工具类
    ofd.read(ofdb64, save_xml=True, xml_name=f"{file_prefix}_xml")  # 读取ofdb64
    # print("ofd.data", ofd.data) # ofd.data 为程序解析结果
    pdf_bytes = ofd.to_pdf(render_mode='char')  # 转pdf
    # img_np = ofd.to_jpg()  # 转图片
    ofd.del_data()

    # 确定输出路径
    if output_dir:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{file_prefix}.pdf")
    else:
        output_file = f"{file_prefix}.pdf"

    with open(output_file, "wb") as f:
        f.write(pdf_bytes)

    # 处理图片输出（如果需要）
    # if img_np:
    #     for idx, img in enumerate(img_np):
    #         img_path = os.path.join(output_dir, f"{file_prefix}_{idx}.jpg") if output_dir else f"{file_prefix}_{idx}.jpg"
    #         img.save(img_path)


def test_pdf2(file_path):
    """
    pdf2ofd
    pdf2img
    """
    file_prefix = os.path.splitext(os.path.split(file_path)[1])[0]
    with open(file_path, "rb") as f:
        pdfb64 = f.read()
    ofd = OFD()
    ofd_bytes = ofd.pdf2ofd(pdfb64, optional_text=False)  # 转ofd # optional_text 生成可操作文本 True 输入也需要可编辑pdf
    img_np = ofd.pdf2img(pdfb64)
    ofd.del_data()
    with open(f"{file_prefix}.ofd", "wb") as f:
        f.write(ofd_bytes)
    for idx, img in enumerate(img_np):
        img.save(f"{file_prefix}_{idx}.jpg")


if __name__ == "__main__":

    file_path = rf"/Volumes/PSSD/ofd/湖北圳康安后勤管理服务有限公司.ofd"
    # 指定输出目录为当前目录下的output文件夹
    output_dir = os.path.join(os.getcwd(), "output")
    
    # 添加耗时计算
    start_time = time.time()
    
    # 执行OFD转换操作
    test_ofd2(file_path, output_dir)
    
    # 计算并显示耗时
    elapsed_time = time.time() - start_time
    print(f"文件处理完成！")
    print(f"总耗时: {elapsed_time:.2f} 秒")

    # root_dir = r"/Volumes/PSSD/新ofd"
    # for dirpath, dirnames, filenames in os.walk(root_dir):
    #     for fn in filenames:
    #         if fn.lower().endswith(".ofd"):
    #             file_path = os.path.join(dirpath, fn)
    #             # 指定输出目录为当前目录下的output文件夹
    #             output_dir = os.path.join(os.getcwd(), "output")
    #             try:
    #                 print(f"Converting: {file_path}")
    #                 test_ofd2(file_path, output_dir)    
    #             except Exception as e:
    #                 print(f"Failed: {file_path} -> {e}")

    # data = ofd.data
    # json.dump(data,open("data.json","w",encoding="utf-8"),ensure_ascii=False,indent=4)
    # print(ofd.data)



