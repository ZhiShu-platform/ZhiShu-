# Cell2Fire: A Cell Based Forest Fire Growth Model  C++/Python
## Cristobal Pais, Jaime Carrasco, David Martell, David L. Woodruff, Andres Weintraub


# 介绍

Cell2Fire 是一款基于单元的全新森林和荒地景观火势蔓延模拟器。其火灾环境的特点是将景观划分为大量同质单元，并指定每个单元的可燃物、天气、可燃物湿度和地形属性。每个单元内的火势蔓延被假设为椭圆形，并受任何独立火

势蔓延模型（例如加拿大森林火灾行为预测系统）预测的蔓延速率控制。Cell2Fire 采用并行计算方法，允许用户在短时间内运行大规模模拟。它包含强大的统计、图形输出和空间分析功能，以便于显示和分析预测的火势蔓延情况。

@ARTICLE{Cell2Fire，作者={Pais, Cristobal、Carrasco, Jaime、Martell, David L.、Weintraub, Andres 和 Woodruff, David L.}，标题={Cell2Fire：基于单元的森林火灾增长模型，用于支持战略景观管理规划}，

期刊={Frontiers in Forests and Global Change}，卷={4}，年份={2021}，URL={ https://www.frontiersin.org/articles/10.3389/ffgc.2021.692706}，DOI={10.3389/ffgc.2021.692706}，ISSN={2624-893X } }

# 环境部署

我们使用docker容器进行Cell2Fire模型的部署，Cell2Fire的官方部署方法为：

cd Cell2Fire/cell2fire/Cell2FireC

Make

cd ../..

pip install -r requirements.txt # might not do anything

pip install -e
   
# 输入文件
Cell2Fire进行火灾蔓延模拟的输入数据主要包含以下几部分：

FIRMS数据集：点火点生成文件，命名为fire_archive_M-C61_106125.csv

燃料模型：命名为Forest.asc

海拔数据：命名为elevation.asc

坡度数据：命名为slope.asc

坡向数据：命名为saz.asc

燃料湿度文件：命名为cur.asc

燃料映射表：命名为fbp_lookup_table.csv

点火点文件：命名为Ignitions.csv

天气数据：命名为Weather.csv

# 运行说明

需要先安装Cell2Fire模型。

由以下网盘链接获取输入文件：

通过网盘分享的文件：Cell2Fire

链接: https://pan.baidu.com/s/18w_yd0fLAj8-rKqvvLEZAA?pwd=2025 提取码: 2025 

安装脚本文件所需库

我们的脚本分为两部分：您可以先运行prepare_run_caijian.py，这是对输入数据的准备；接着运行run_simulation.py，这是我们的主要运行脚本。里面包含了Cell2Fire运行的命令行，您只需运行后耐心等待。注：若您遇到段错

误问题，很大可能是由于内存不足导致的。

# 网盘文件说明
网盘内含Input_Landscape文件夹，内含所有的输入文件，output_cell2fire是测试数据输出文件夹。

若用户想要了解更多有关Cell2Fire的信息，可以阅读Cell2Fire的官方文档等，Cell2Fire的仓库链接为
：
https://github.com/cell2fire/Cell2Fire.git
