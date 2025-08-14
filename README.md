# SGFormer-SSCBench-KITTI-360 数据集卫星图像下载脚本

## 概述

这是一个 Python 脚本，用于为  [SGFormer](https://github.com/gxytcrc/SGFormer)的[SSCBench-KITTI-360](https://huggingface.co/datasets/ai4ce/SSCBench/tree/main/sscbench-kitti) 数据集自动下载对应的卫星图像。脚本会读取数据集中每个时间帧的 GPS 坐标，并从 Google Maps Static API 获取高质量的卫星视图图像。

## 主要功能

  - **批量处理**: 一次性处理多个 SSCBench-KITTI-360 的行驶序列（sequence）。
  - **高效率下载**: 使用多线程并发下载，显著提升大规模数据集的下载速度。
  - **URL签名**: 支持 Google Maps API 的 URL 签名，增强安全性并适用于企业级密钥。
  - **代理支持**: 内置网络代理（Proxy）支持，方便在受限网络环境下使用。
  - **进度可视化**: 使用 `tqdm` 提供实时的下载进度条，方便监控。
  - **断点续传**: 自动跳过已下载的图像，可随时中断和恢复下载任务。
  - **高度可配置**: 所有关键参数（如API密钥、路径、并发数等）都集中在脚本顶部，易于修改。

## 环境准备

在运行此脚本之前，请确保您已准备好以下内容：

1.  **Python 3.x**: 建议使用 Python 3.6 或更高版本。
2.  **必要的 Python 库**:
    ```bash
    pip install requests tqdm
    ```
3.  **KITTI-360 数据集**: 您需要已经下载了 `OXTS Sync Measurements (37.3M) ` 部分，特别是包含了 `oxts` 数据的文件夹。
4.  **Google Maps API 密钥**:
      - 一个有效的 Google Maps Static API 密钥。
      - 一个URL签名密钥（URL Signing Secret）以提高安全性。
5.  **网络代理**: 如果您所在的地区无法直接访问 Google 服务，需要一个可用的网络代理工具。

## 配置与设置

1.  **克隆或下载脚本**: 将 `download_satellite_images.py` 保存到您的本地项目文件夹中。
2.  **打开脚本文件**: 使用代码编辑器打开 `download_satellite_images.py`。
3.  **修改参数**: 找到 `main` 函数下的 `>>> 需要你修改的路径和参数 <<<` 部分，并根据您的实际情况填写以下信息：
      - `API_KEY`: 您的 Google Maps API 密钥。
      - `URL_SIGNING_SECRET`: 您的 URL 签名密钥。
      - `DATASET_ROOT`: 您存放 SSCBench-KITTI-360 数据集的根目录路径。
      - `SEQUENCES_TO_DOWNLOAD`: 一个 Python 列表，包含了您希望下载的所有行驶序列的名称。
      - `ZOOM_LEVEL`: 地图的缩放级别，**19** 是为了匹配约0.2米/像素的比例尺（实际应为[0.19](https://timwhitlock.info/blog/2010/04/google-maps-zoom-scales/)米/像素）。
      - `MAX_WORKERS`: 并发下载的线程数。根据您的网络状况调整，建议从10开始。
      - `proxies` (在`download_satellite_image`函数内): 如果需要，请修改代理的地址和端口号。

## 如何运行

配置好所有参数后，打开终端（或命令行），进入脚本所在的目录，然后运行：

```bash
python download_satellite_images.py
```

脚本将开始处理您在 `SEQUENCES_TO_DOWNLOAD` 列表中定义的每一个序列，并显示总体进度。

## 重要提示

  - **API 成本**: 请注意，Google Maps API 的使用可能会产生费用。请务必在 [Google Cloud Console](https://console.cloud.google.com/) 中监控您的用量并设置预算提醒。
  - **代理配置**: 脚本中的代理设置为 `http://127.0.0.1:7890`。请务必将其修改为您自己代理工具的**真实HTTP代理地址和端口**。
  - **数据结构**: 脚本默认 `oxts` 数据位于 `DATASET_ROOT/SEQUENCE_NAME/oxts/data/` 目录下。如果您的数据集结构不同，请相应地修改 `OXTS_DIR_PATH` 变量。
  - **URL 签名**: URL 签名是 Google 推荐的安全实践，可以保护您的 API 密钥不被滥用。请在 Google Cloud Console 中为您的项目启用它并生成密钥。
