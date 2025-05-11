import os
import glob
import gradio as gr
from moviepy.editor import VideoFileClip, concatenate_videoclips
import subprocess
import tempfile
import shutil

def get_latest_transition_video():
    """获取最新生成的过渡视频文件"""
    transition_files = glob.glob('*.mp4')
    if not transition_files:
        raise FileNotFoundError("未找到过渡视频文件")
    latest_file = max(transition_files, key=os.path.getctime)
    return latest_file

def concatenate_videos(video1_path, video2_path, transition_path, output_path, num_frames, fps):
    """拼接三个视频部分"""
    clip1 = VideoFileClip(video1_path)
    clip2 = VideoFileClip(video2_path)
    transition = VideoFileClip(transition_path)

    transition_duration = num_frames / fps

    duration1 = clip1.duration - transition_duration
    part1 = clip1.subclip(0, max(0, duration1))

    start_time2 = transition_duration
    part2 = clip2.subclip(min(start_time2, clip2.duration))

    final_clip = concatenate_videoclips([part1, transition, part2])
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

    clip1.close()
    clip2.close()
    transition.close()
    final_clip.close()

def get_video_info(video_path):
    """获取视频信息"""
    clip = VideoFileClip(video_path)
    fps = clip.fps
    duration = clip.duration
    total_frames = int(duration * fps)
    clip.close()
    return fps, duration, total_frames

def process_videos(video1, video2, animation, num_frames):
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 保存上传的视频到临时目录
        video1_path = os.path.join(temp_dir, "video1.mp4")
        video2_path = os.path.join(temp_dir, "video2.mp4")
        shutil.copyfile(video1, video1_path)
        shutil.copyfile(video2, video2_path)
        
        # 获取视频信息
        fps1, duration1, frames1 = get_video_info(video1_path)
        fps2, duration2, frames2 = get_video_info(video2_path)
        
        # 使用两个视频中较小的FPS
        fps = min(fps1, fps2)
        
        # 计算最大可用帧数
        max_possible_frames = min(
            int(duration1 * fps),
            int(duration2 * fps)
        )
        num_frames = min(num_frames, max_possible_frames)
        
        # 1. 生成过渡部分
        transition_cmd = [
            "python", "vid_transition.py",
            "-i", video1_path, video2_path,
            "--animation", animation,
            "--num_frames", str(num_frames),
            "--max_brightness", "1.5",
            "-m", "y"
        ]
        subprocess.run(transition_cmd, check=True)
        
        # 2. 获取过渡视频
        transition_path = get_latest_transition_video()
        
        # 3. 拼接视频
        #output_path = os.path.join(temp_dir, "output.mp4")
        output_path = "output.mp4"
        concatenate_videos(video1_path, video2_path, transition_path, output_path, num_frames, fps)
        
        return output_path
        
    except Exception as e:
        raise gr.Error(f"处理视频时出错: {str(e)}")
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

def validate_inputs(video1, video2, num_frames):
    """验证输入参数"""
    if not video1 or not video2:
        raise gr.Error("请上传两个视频文件")
    
    try:
        fps1, duration1, frames1 = get_video_info(video1)
        fps2, duration2, frames2 = get_video_info(video2)
    except:
        raise gr.Error("上传的视频文件无效")
    
    fps = min(fps1, fps2)
    max_possible_frames = min(frames1, frames2)
    
    if num_frames > max_possible_frames:
        raise gr.Error(f"视频太短，最大可用过渡帧数为: {max_possible_frames}")
    
    return fps, max_possible_frames

def process_and_validate(video1, video2, animation, num_frames):
    try:
        fps, max_frames = validate_inputs(video1, video2, num_frames)
        if num_frames > max_frames:
            num_frames = max_frames
            gr.Info(f"自动调整过渡帧数为: {num_frames}")
            
        output_path = process_videos(video1, video2, animation, num_frames)
        return output_path
    except Exception as e:
        raise gr.Error(str(e))

# 创建Gradio界面
with gr.Blocks(title="视频过渡与拼接工具") as demo:
    gr.Markdown("""
    # 视频过渡与拼接工具
    上传两个视频，选择过渡效果，生成平滑过渡的合并视频。
    """)
    
    with gr.Row():
        with gr.Column():
            video1 = gr.Video(label="第一个视频")
            video2 = gr.Video(label="第二个视频")
            
            animation = gr.Dropdown(
                label="过渡动画效果",
                choices=[
                    'translation', 'translation_inv',
                    'rotation', 'rotation_inv',
                    'zoom_in', 'zoom_out',
                    'long_translation', 'long_translation_inv'
                ],
                value='translation'
            )
            
            num_frames = gr.Slider(
                label="过渡帧数",
                minimum=10,
                maximum=100,
                step=5,
                value=30,
                info="会根据视频长度自动调整"
            )
            
            submit_btn = gr.Button("生成过渡视频", variant="primary")
        
        with gr.Column():
            output_video = gr.Video(label="合并后的视频")
            info_box = gr.Textbox(label="处理信息", visible=False)
    
    submit_btn.click(
        fn=process_and_validate,
        inputs=[video1, video2, animation, num_frames],
        outputs=output_video
    )
    
    # 示例部分 - 使用0000.mp4和0001.mp4展示所有动画效果
    examples = []
    animations = [
        'translation', 'translation_inv',
        'rotation', 'rotation_inv',
        'zoom_in', 'zoom_out',
        'long_translation', 'long_translation_inv'
    ]
    
    for anim in animations:
        examples.append([
            "examples/abc.mp4",
            "examples/bcd.mp4",
            anim,
            30  # 使用30帧作为示例
        ])
    
    gr.Examples(
        examples=examples,
        inputs=[video1, video2, animation, num_frames],
        outputs=output_video,
        fn=process_and_validate,
        cache_examples=False,
        label="不同过渡效果"
    )

if __name__ == "__main__":
    demo.launch(share = True)
