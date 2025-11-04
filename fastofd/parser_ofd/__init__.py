
from loguru import logger
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont

# from ofd_parser import *


# font_map = {"宋体.ttc":["宋体","SWPMEH+SimSun","SimSun","SWDKON+SimSun"],
#             '楷体.ttf':["KaiTi","楷体","SWLCQE+KaiTi","SWHGME+KaiTi","BWSimKai"],
#             # 'STKAITI.TTF':["华文楷体 常规","STKAITI","华文楷体"],
#             "COURI.TTF":["CourierNewPSMT","CourierNew","SWCRMF+CourierNewPSMT","SWANVV+CourierNewPSMT"],
#             "courbd.TTF":["Courier New"],
#             "黑体.ttf":["SimHei","hei","黑体"]
#             }
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))

# # 初始化字体
# for font,names in font_map.items():
#     for name in names:
#         try:
#             pdfmetrics.registerFont(TTFont(name, font))
#         except:
#             logger.warning(f"FONT  registerFont failed {font}: {name}")

from fastofd.parser_ofd.ofd_parser import OFDParser
__all__=["OFDParser"]
                                    



