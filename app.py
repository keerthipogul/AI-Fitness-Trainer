
import streamlit as st
import cv2
import mediapipe as mp
import tempfile
import os
import subprocess

st.set_page_config(page_title="AI Fitness Trainer")
st.title("🏋️ AI Fitness Posture Detector")
st.write("Upload an exercise video to detect body posture.")

uploaded = st.file_uploader(
    "Upload workout video",
    type=["mp4", "avi", "mov"]
)

if uploaded:
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".mp4"
    ) as f:
        f.write(uploaded.read())
        video_path = f.name

    cap = cv2.VideoCapture(video_path)
    output_path = video_path.replace(".mp4", "_out.mp4")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25

    writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    mp_pose = mp.solutions.pose
    draw = mp.solutions.drawing_utils

    with mp_pose.Pose() as pose:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)

            if result.pose_landmarks:
                draw.draw_landmarks(
                    frame,
                    result.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )

            writer.write(frame)

   

    cap.release()
    writer.release()

    st.success("Pose detection completed!")

    converted_path = output_path.replace(
        ".mp4", "_converted.mp4"
    )

    result = subprocess.run(
        [
            "ffmpeg", "-y", "-i", output_path,
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            converted_path
        ],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        st.video(converted_path)
    else:
        st.error("Video conversion failed")
        st.code(result.stderr[-2000:])

    os.remove(video_path)
    os.remove(output_path)

    if os.path.exists(converted_path):
        os.remove(converted_path)
