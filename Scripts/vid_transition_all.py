'''
#!/bin/bash
# 设置固定路径
source_dir="Genshin_Zip"
dest_dir="Genshin_Zip_RN"
# 创建目标目录（如果不存在）
mkdir -p "$dest_dir"
# 计数器，用于生成序列号
counter=1
echo "开始处理目录: $source_dir"
echo "输出目录: $dest_dir"
# 查找所有.mp4文件，按名称排序，并处理
find "$source_dir" -maxdepth 1 -type f -name "*.mp4" | sort | while read -r file; do
    # 生成新文件名（格式：0001.mp4, 0002.mp4等）
    new_name=$(printf "%04d.mp4" "$counter")
    # 拷贝文件到目标目录
    cp -v "$file" "$dest_dir/$new_name"
    # 显示处理信息
    echo "已重命名: $(basename "$file") -> $new_name"
    # 增加计数器
    counter=$((counter + 1))
done
echo "处理完成！共处理了 $((counter-1)) 个文件"

python vid_transition_all.py Genshin_Zip_4 --output genshin-merge-4.mp4

python vid_transition_all.py Genshin_Zip_RN --output genshin-merge.mp4


'''

import os
import glob
import argparse
import subprocess
from itertools import cycle

# 可用的动画效果列表（按照您原始脚本中的选项）
ANIMATIONS = [
    'rotation',
    'rotation_inv',
    'zoom_in',
    'zoom_out',
    'translation',
    'translation_inv',
    'long_translation',
    'long_translation_inv'
]

def get_sorted_videos(input_path):
    """获取输入路径下所有视频文件并按字典序排序"""
    video_files = glob.glob(os.path.join(input_path, '*.mp4'))  # 假设都是mp4文件
    video_files.sort()
    return video_files

def merge_videos(video1, video2, output, animation):
    """使用原始脚本合并两个视频"""
    cmd = [
        'python',
        'vid_transition_cpl.py',  # 替换为您的原始脚本文件名
        "--num_frames", "40",
        '-i', video1, video2,
        '-o', output,
        '-a', animation
    ]
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser(description='批量合并视频并轮换动画效果')
    parser.add_argument('input_path', help='包含要合并的视频文件的目录路径')
    parser.add_argument('--output', default='final_output.mp4', help='最终输出视频路径')

    args = parser.parse_args()

    # 获取排序后的视频文件
    video_files = get_sorted_videos(args.input_path)
    if len(video_files) < 2:
        print("至少需要2个视频文件进行合并")
        return

    print(f"找到 {len(video_files)} 个视频文件:")
    for i, v in enumerate(video_files, 1):
        print(f"{i}. {os.path.basename(v)}")

    # 准备动画效果循环器
    animation_cycle = cycle(ANIMATIONS)

    # 初始设置
    current_video = video_files[0]
    temp_files = []

    try:
        # 依次合并视频
        for i in range(1, len(video_files)):
            next_video = video_files[i]
            animation = next(animation_cycle)

            # 如果不是最后一次合并，使用临时文件
            if i < len(video_files) - 1:
                output_file = f"temp_merged_{i}.mp4"
                temp_files.append(output_file)
            else:
                output_file = args.output

            print(f"\n正在合并 {os.path.basename(current_video)} 和 {os.path.basename(next_video)}")
            print(f"使用动画效果: {animation}")
            print(f"输出到: {output_file}")

            merge_videos(current_video, next_video, output_file, animation)
            current_video = output_file

        print(f"\n最终视频已保存到: {args.output}")

    finally:
        # 清理临时文件
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"已删除临时文件: {temp_file}")

if __name__ == "__main__":
    main()
