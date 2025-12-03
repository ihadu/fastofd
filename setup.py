
import setuptools 
# 直接设置版本号，避免在构建过程中导入fastofd包
__version__ = "0.0.7"
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
 
setuptools.setup(
    name="fastofd", 
    version=__version__,
    author="ihadyou",    
    author_email="wohen@nivbi.com",    
    description="easy operate OFD",
    long_description=long_description,   
    long_description_content_type="text/markdown",
    url="https://github.com/ihadyou/fastofd",    
    packages=setuptools.find_packages(exclude=["README.md",".vscode", ".vscode.*", ".git", ".git.*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=[   ### 依赖包
        "reportlab==3.6.11",
        "xmltodict>=0.13.0",
        "loguru>=0.7.2",
        "fontTools>=4.43.1",
        "PyMuPDF>=1.23.4",
        "pyasn1>=0.6.0",
        "lxml>=6.0.2",
        "pypdf>=6.1.3"
                     ],
    python_requires='>=3.8',   
)