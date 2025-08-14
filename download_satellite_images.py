import os
import math
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import base64
import hmac
import hashlib
import urllib.parse

# ==============================================================================
# URL 签名函数
# ==============================================================================
def sign_url(url, secret):
    """
    对Google Maps Platform URL进行签名。
    """
    try:
        # URL解码
        decoded_secret = base64.urlsafe_b64decode(secret)
        
        # 使用 urllib.parse 来正确提取路径和查询参数
        url_components = urllib.parse.urlparse(url)
        path_and_query = url_components.path + '?' + url_components.query
        
        # 对URL进行签名
        signature = hmac.new(decoded_secret, path_and_query.encode('utf-8'), hashlib.sha1).digest()
        encoded_signature = base64.urlsafe_b64encode(signature).decode('utf-8')
        
        return f"{url}&signature={encoded_signature}"
    except Exception as e:
        print(f"Error signing URL: {e}")
        return None

# ==============================================================================
#  下载函数
# ==============================================================================
def download_satellite_image(session, lat, lon, zoom, api_key, url_signing_secret, output_path):
    """
    从Google Maps Static API下载卫星图像并保存。
    """
    IMAGE_SIZE = "YOUR_IMAGE_SIZE"  # 替换为你的图像大小

    MAP_TYPE = "satellite"

    # 构建基础URL
    base_url = (
        f"https://maps.googleapis.com/maps/api/staticmap?"
        f"center={lat},{lon}&"
        f"zoom={zoom}&"
        f"size={IMAGE_SIZE}&"
        f"maptype={MAP_TYPE}&"
        f"key={api_key}"
    )
    
    # 签名URL
    signed_url = sign_url(base_url, url_signing_secret)
    if not signed_url:
        return False, f"无法对URL进行签名，跳过下载: {output_path}"

    # 请将 'http://127.0.0.1:7890' 中的 7890 替换为您自己代理工具的真实HTTP端口号
    proxies = {
        'http': 'http://127.0.0.1:7890',
        'https': 'http://127.0.0.1:7890',
    }

    try:
        response = session.get(signed_url, timeout=20, proxies=proxies)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True, output_path
        else:
            return False, f"下载失败: {output_path}. 状态码: {response.status_code}. 响应内容: {response.text}"
    except requests.exceptions.RequestException as e:
        return False, f"下载时发生网络错误: {output_path}. 原因: {e}"

# ==============================================================================
#  主执行函数
# ==============================================================================
def main():
    # --------------------------------------------------------------------------
    #  >>> 需要你修改的路径和参数 <<<
    # --------------------------------------------------------------------------
    API_KEY = "YOUR_API_KEY"  # 替换为你的Google Maps API密钥
    URL_SIGNING_SECRET = "YOUR_URL_SIGNING_SECRET"  # 替换为你的URL签名密钥 
    
    DATASET_ROOT = "PATH/TO/YOUR/KITTI-DATASET"  # 替换为你的KITTI数据集路径
    
    SEQUENCES_TO_DOWNLOAD = [
        "2013_05_28_drive_0000_sync",
        "2013_05_28_drive_0002_sync",
        "2013_05_28_drive_0003_sync",
        "2013_05_28_drive_0004_sync",
        "2013_05_28_drive_0005_sync",
        "2013_05_28_drive_0006_sync",
        "2013_05_28_drive_0007_sync",
        "2013_05_28_drive_0009_sync",
        "2013_05_28_drive_0010_sync"
    ]
    
    ZOOM_LEVEL = 19     #  每个像素的比例因子约为0.2米（实际为0.19米）

    # *** 关键参数：并发下载的线程数 ***
    # 可以根据你的网络情况和代理稳定性调整，建议从10开始尝试
    # 如果遇到大量错误，可以适当调低；如果网络很好，可以调高
    MAX_WORKERS = 10   
    # --------------------------------------------------------------------------

    # 遍历您定义的所有序列
    for sequence_name in SEQUENCES_TO_DOWNLOAD:
        print(f"\n=========================================================")
        print(f"=== 开始处理序列: {sequence_name} ===")
        print(f"=========================================================")

        OXTS_DIR_PATH = os.path.join(DATASET_ROOT, sequence_name, "oxts", "data")
        OUTPUT_DIR = os.path.join(DATASET_ROOT, sequence_name, f"data_2d_satellite_zoom={ZOOM_LEVEL}_512x512")

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        tasks_to_process = []
        try:
            oxts_files = sorted(os.listdir(OXTS_DIR_PATH))
            if not oxts_files:
                print(f"错误: 序列 {sequence_name} 的oxts文件夹为空或不存在: {OXTS_DIR_PATH}")
                continue
            
            for oxts_filename in oxts_files:
                if not oxts_filename.endswith(".txt"):
                    continue

                frame_id_str = os.path.splitext(oxts_filename)[0]
                frame_id = int(frame_id_str)
                output_filename = f"{frame_id:010d}.png"
                output_filepath = os.path.join(OUTPUT_DIR, output_filename)

                if os.path.exists(output_filepath):
                    continue

                current_oxts_path = os.path.join(OXTS_DIR_PATH, oxts_filename)
                with open(current_oxts_path, 'r') as f:
                    line = f.readline()
                    parts = line.split(' ')
                    target_lat = float(parts[0])
                    target_lon = float(parts[1])
                
                tasks_to_process.append((target_lat, target_lon, ZOOM_LEVEL, API_KEY, URL_SIGNING_SECRET, output_filepath))

        except FileNotFoundError:
            print(f"错误: 找不到序列 {sequence_name} 的oxts文件夹: {OXTS_DIR_PATH}")
            continue
        
        if not tasks_to_process:
            print(f"序列 {sequence_name} 的所有文件均已下载，跳过。")
            continue

        print(f"在序列 {sequence_name} 中找到 {len(tasks_to_process)} 个新文件需要下载。")

        with requests.Session() as session:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = [executor.submit(download_satellite_image, session, *task) for task in tasks_to_process]
                
                for future in tqdm(as_completed(futures), total=len(tasks_to_process), desc=f"下载 {sequence_name}"):
                    try:
                        success, message = future.result()
                        if not success:
                            tqdm.write(message)
                    except Exception as e:
                        tqdm.write(f"一个下载任务发生严重错误: {e}")
        
        print(f"--- 序列 {sequence_name} 处理完毕 ---")

    print("\n>>> 所有指定序列均已处理完毕! <<<")


if __name__ == "__main__":
    main()