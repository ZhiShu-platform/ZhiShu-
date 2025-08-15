
# NFDRS4 - National Fire Danger Rating System 4.0
该存储库包含美国国家火灾危险评级系统 4.0 版的源代码。源代码提供对命令行界面 (CLI) 以及用于构建 Python 库的 SWIG 包装器的访问。它还提供了 CLI 输入格式的文档以及 FW13 到 FW21 天气数据文件转换器。

该库提供了 NFDRS 版本 4.0 的所有源代码，包括 Nelson 死燃料水分模型、基于生长季节指数的活燃料水分模型和 NFDRS 计算器。

还生产两个应用程序：FireWxConverter 和 NFDRS4_cli（命令行界面）。

FireWxConverter 将 FW13 火灾天气数据文件转换为 FW21 火灾天气数据文件，NFDRS4_cli 从 FW21 火灾天气数据文件中生成活燃料和死燃料水分以及 NFDRS 索引。

## 环境部署
我们使用docker容器进行部署。

NFDRS4依赖项较少，其是由他的命令行工具软件进行运行的。一个构建其命令行软件的方法如下：

sudo apt-get install build-essential cmake

cmake ..

make

## 输入数据

NFDRS4进行火灾风险预测的输入文件主要包含以下部分：

海拔、坡向、坡度：作为地形数据输入

燃料模型数据

天气数据：包含了降水、气温、风速、风向、太阳辐射、降雪量和相对湿度等输入数据。

## 运行说明
首先创建NFDRS的命令行运行软件。

从以下网盘链接中获取输入数据：

通过网盘分享的文件：NFDRS4

链接: https://pan.baidu.com/s/1Ny9FALH0NzQ90R2om3-iqQ?pwd=2025 提取码: 2025 

运行prepare_data_for_nfdrs.py来处理输入数据，注意把文件中的路径改为实际路径

运行NFDRS运行命令：./NFDRS4_cli  RunNFDRS_Palisades.txt

或直接利用网盘中的数据运行命令行

等待运行结果

## 网盘数据说明
内含InputFile文件夹，包含所有输入输出数据和数据准备脚本，其中prepare_data_for_nfdrs.py是数据准备脚本，Palisades_NFDRS_Output.csv为示例输出。

若用户想要了解更多有关NFDRS4的信息，可以阅读NFDRS4的官方文档等，NFDRS4的仓库链接为：

https://github.com/firelab/NFDRS4.git
