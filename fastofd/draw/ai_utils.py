#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI工具模块，用于管理多模态模型的图片描述功能
"""
import os
from openai import OpenAI
from loguru import logger

class ImageDescriber:
    """
    图片描述器类，封装了使用多模态模型描述图片的功能
    """
    
    # 图片描述提示词模板（用于多模态模型）
    IMAGE_DESCRIPTION_PROMPT = """
请仔细分析以下图像内容，并将其完整、准确地转换为适合嵌入正式投标文件的文本描述。要求如下：

若图像包含表格：以 Markdown 表格形式还原所有行列内容，保留表头和单位；若表格跨页或复杂，请说明结构。
若图像为流程图、组织架构图或示意图：用清晰的层级文字描述各节点及其关系（例如：“第一步：XXX → 第二步：XXX” 或 “顶层部门：A，下属部门包括 B 和 C”）。
若图像为资质证书、营业执照、盖章文件等：提取所有关键字段，包括但不限于：
企业名称
证书编号
发证机关
有效期限
签发日期
所含许可范围或认证内容
若图像包含手写内容或模糊文字：如实标注“[无法辨识]”或“[疑似：XXX]”，不要猜测。
保持客观、正式语气，避免主观评价。
不要添加原文未出现的信息。
请开始处理图像。
    """
    
    def __init__(self, **kwargs):
        """
        初始化图片描述器
        
        参数：
        - openai_api_key: OpenAI API密钥
        - openai_api_base: API基础URL
        - openai_model: 使用的模型名称
        """

        self.openai_api_key = "sk-b33341a5217d4d7ea7ba27075e7432c1"
        self.openai_api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.openai_model = "qwen3-vl-flash"
        
        # 创建OpenAI客户端实例
        self.openai_client = None
        if self.openai_api_key:
            self.openai_client = OpenAI(
                api_key=self.openai_api_key,
                base_url=self.openai_api_base if self.openai_api_base else None
            )
    
    def describe_image(self, img_b64, file_name):
        """
        使用多模态模型描述图片内容
        
        参数：
        - img_b64: 图片的base64编码
        - file_name: 图片原始文件名
        
        返回：
        - 格式化的图片描述文本 [image:文件名]描述内容[image:文件名]
        """
        try:
            # 检查是否配置了API客户端
            if not self.openai_client:
                logger.warning(f"未配置OpenAI API客户端，无法描述图片{file_name}")
                return f"[image:{file_name}]未配置OpenAI API客户端，无法描述图片内容[image:{file_name}]"
            
            # 使用配置的模型进行图片描述
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的图片内容分析师，擅长将各种类型的图片转换为结构化的文本描述。"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.IMAGE_DESCRIPTION_PROMPT
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=10240  # 增加token限制以支持更详细的描述
            )
            
            # 获取描述结果
            description = response.choices[0].message.content.strip()
            
            # 格式化为 [image:文件名]描述内容[image:文件名]
            formatted_description = f"[image:{file_name}]{description}[image:{file_name}]"
            return formatted_description
        except Exception as e:
            logger.error(f"使用AI描述图片{file_name}时出错: {str(e)}")
            # 如果API调用失败，返回默认描述
            return f"[image:{file_name}]无法描述图片内容[image:{file_name}]"