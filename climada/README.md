[![DOI](https://zenodo.org/badge/112729129.svg)](https://zenodo.org/badge/latestdoi/112729129)
[![Build Status](http://ied-wcr-jenkins.ethz.ch/buildStatus/icon?job=climada_branches/develop)](http://ied-wcr-jenkins.ethz.ch/job/climada_branches/)
[![Documentation build status](https://img.shields.io/readthedocs/climada-python.svg?style=flat-square)](https://readthedocs.org/projects/climada-python/builds/)

# CLIMADA

CLIMADA（CLIMate ADAptation）是一个免费的开源软件框架，用于气候风险评估和适应方案评估。它由一个庞大的科学界共同设计，旨在帮助研究人员、政策制定者和企业分析自然灾害的影响并探索适应策略。

截至目前，CLIMADA 通过数据 API提供高分辨率（4x4 公里）的全球主要气候相关极端天气灾害覆盖。对于特定灾害，在不同时间范围内存在针对过去、现在和未来气候的历史事件集和概率事件集。您可以在此处找到一个包含科学同行

评审文章的存储库，这些文章解释了 CLIMADA 中实现的软件组件。

CLIMADA 分为两部分（两个存储库）：
1.核心climada_python包含概率影响、避免损害、不确定性和预测计算所需的所有模块。灾害、暴露和影响函数的数据可以通过数据 API 获取。Litpop包含在演示暴露模块中，热带气旋包含在演示灾害模块中。

2.花瓣climada_petals包含所有用于生成数据的模块（例如 TC_Surge、WildFire、OpenStreeMap 等）。大部分开发工作都在这里完成。花瓣构建于核心之上，不能独立运行。

建议新用户从核心（1）及其教程开始。

## 环境部署

Climada无复杂环境要求，我们选择将climada部署在conda环境中，并且使用jupyter notebook运行脚本文件。

## 输入文件

Climada进行火灾灾损计算的数入文件主要包含三部分：
BlackMarble数据集：该数据集是夜间灯光数据集，命名为BlackMarble_2016_A1_geo_gray.tif的四个栅格数据。

GPW全球人口网格数据集：命名为gpw-v4-population-count-rev11_2020_30_sec_tif的栅格数据。

FIRMS数据集：该数据集是NASA遥感数据集，用于生成起火点文件。命名为fire_archive_M-C61_106125.csv的文件。

## 运行说明

首先安装climada-python仓库，使用的是climada的最新版本，特别注意：climada在之前的版本更新后被分为了两个部分，用户在使用脚本前务必下载climada_petals仓库，一个方法是在命令行界面输入：pip install climada_petals。

接着从以下网盘中获取输入数据：
通过网盘分享的文件：data等3个文件
链接: https://pan.baidu.com/s/1nKBwmlfDEGO9s7XLLuuL5g?pwd=2025 提取码: 2025

并且获取运行脚本：run_climada.ipynb，将脚本文件中的文件路径更改为实际路径。

运行脚本就可以得到最终结果。

## 网盘文件说明

网盘共包含三个文件夹：
climadaresults：包含了脚本文件和这个脚本文件的所有图形化输出结果

data：包含了进行火灾灾损计算的全部数据集以及climada自带的其他数据集

demo：一个climada的示例输入文件夹

若用户想要了解更多有关climada的信息，可以阅读climada的官方文档等，climada_python的仓库链接为：

https://github.com/CLIMADA-project/climada_python.git


