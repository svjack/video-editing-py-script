'''
python vid_transition.py -i 0000.mp4  0001.mp4 --animation translation --num_frames 30 --max_brightness 1.5 -m y

python vid_transition_cpl.py -i 0000.mp4  0001.mp4 -o 00-01-merge.mp4

python vid_transition_cpl.py -i qiqi.mp4 Bjiuqiren.mp4 -o qi-jiu-merge.mp4 -a rotation_inv --num_frames 40
'''

import os
import glob
import argparse
from moviepy.editor import VideoFileClip, concatenate_videoclips

def get_latest_transition_video():
    """获取当前目录下最新生成的过渡视频文件"""
    # 查找所有可能的过渡视频文件
    transition_files = glob.glob('*.mp4')
    if not transition_files:
        raise FileNotFoundError("未找到过渡视频文件，请先运行vid_transition.py生成过渡部分")

    # 获取最新的文件
    latest_file = max(transition_files, key=os.path.getctime)
    return latest_file

def concatenate_videos(video1_path, video2_path, transition_path, output_path, num_frames=20, fps=None):
    """拼接三个视频部分"""
    # 加载视频文件
    clip1 = VideoFileClip(video1_path)
    clip2 = VideoFileClip(video2_path)
    transition = VideoFileClip(transition_path)

    # 获取视频的帧率（如果未提供则使用第一个视频的帧率）
    if fps is None:
        fps = clip1.fps

    # 计算过渡部分的持续时间（秒）
    transition_duration = num_frames / fps

    # 计算需要保留的部分
    # 第一个视频保留过渡部分之前的内容
    duration1 = clip1.duration - transition_duration
    part1 = clip1.subclip(0, max(0, duration1))  # 确保不会出现负值

    # 第二个视频保留过渡部分之后的内容
    start_time2 = transition_duration
    part2 = clip2.subclip(min(start_time2, clip2.duration))  # 确保不超过视频长度

    # 拼接三个部分
    final_clip = concatenate_videoclips([part1, transition, part2])

    # 写入输出文件
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

    # 关闭所有剪辑以释放资源
    clip1.close()
    clip2.close()
    transition.close()
    final_clip.close()

def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='拼接两个视频及其过渡部分')
    parser.add_argument('-i', '--input', nargs=2, required=True,
                       help='输入的两个视频文件路径')
    parser.add_argument('-o', '--output', default='final_output.mp4',
                       help='输出视频文件路径')
    parser.add_argument('-n', '--num_frames', type=int, default=30,
                       help='过渡动画的帧数 (默认: 30)')
    parser.add_argument('-a', '--animation',
                       choices=['rotation', 'rotation_inv', 'zoom_in', 'zoom_out',
                               'translation', 'translation_inv',
                               'long_translation', 'long_translation_inv'],
                       default='translation',
                       help='选择过渡动画效果 (默认: translation)')

    args = parser.parse_args()

    # 获取输入文件路径
    video1_path, video2_path = args.input
    output_path = args.output
    animation = args.animation
    num_frames = args.num_frames

    try:
        # 1. 首先运行过渡生成命令
        transition_cmd = f"python vid_transition.py -i {video1_path} {video2_path} --animation {animation} --num_frames {num_frames} --max_brightness 1.5 -m y"
        print(f"正在生成过渡部分: {transition_cmd}")
        os.system(transition_cmd)

        # 2. 获取最新生成的过渡视频
        transition_path = get_latest_transition_video()
        print(f"找到过渡视频: {transition_path}")

        # 3. 拼接三个部分
        print("正在拼接视频...")
        concatenate_videos(video1_path, video2_path, transition_path, output_path, num_frames)

        print(f"视频拼接完成，输出文件: {output_path}")

    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()
