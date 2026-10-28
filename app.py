
import streamlit as st
import cv2
import mediapipe as mp
import tempfile
import os
import subprocess
import math

st.set_page_config(page_title="AI Fitness Trainer")
st.title("🏋️ AI Fitness Trainer")
st.write("Upload a workout video for pose detection and squat rep counting.")

uploaded = st.file_uploader(
    "Upload workout video",
    type=["mp4", "avi", "mov"]
)


def calculate_angle(a, b, c):
    """Calculate angle ABC using 2D landmark coordinates."""
    angle = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0])
        - math.atan2(a[1] - b[1], a[0] - b[0])
    )
    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle
    return angle


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

    rep_count = 0
    squat_state = "UP"
    knee_angle = None
    visibility_threshold = 0.5

    with mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = pose.process(rgb)

            if result.pose_landmarks:
                landmarks = result.pose_landmarks.landmark

                draw.draw_landmarks(
                    frame,
                    result.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )

                # Use the more visible side of the body.
                left_ids = [
                    mp_pose.PoseLandmark.LEFT_HIP.value,
                    mp_pose.PoseLandmark.LEFT_KNEE.value,
                    mp_pose.PoseLandmark.LEFT_ANKLE.value
                ]
                right_ids = [
                    mp_pose.PoseLandmark.RIGHT_HIP.value,
                    mp_pose.PoseLandmark.RIGHT_KNEE.value,
                    mp_pose.PoseLandmark.RIGHT_ANKLE.value
                ]

                left_visibility = min(
                    landmarks[i].visibility for i in left_ids
                )
                right_visibility = min(
                    landmarks[i].visibility for i in right_ids
                )

                chosen_ids = (
                    left_ids if left_visibility >= right_visibility
                    else right_ids
                )
                chosen_visibility = max(
                    left_visibility, right_visibility
                )

                if chosen_visibility >= visibility_threshold:
                    hip, knee, ankle = [
                        (
                            landmarks[i].x * width,
                            landmarks[i].y * height
                        )
                        for i in chosen_ids
                    ]

                    knee_angle = calculate_angle(hip, knee, ankle)

                    # Simple squat state machine.
                    if knee_angle < 110 and squat_state == "UP":
                        squat_state = "DOWN"

                    elif knee_angle > 160 and squat_state == "DOWN":
                        rep_count += 1
                        squat_state = "UP"

                    cv2.putText(
                        frame,
                        f"Knee angle: {int(knee_angle)} deg",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 255, 255), 2
                    )

                cv2.putText(
                    frame,
                    f"Squat reps: {rep_count}",
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2
                )

                cv2.putText(
                    frame,
                    f"State: {squat_state}",
                    (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (255, 255, 0), 2
                )

            else:
                cv2.putText(
                    frame,
                    "No pose detected",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 0, 255), 2
                )

            writer.write(frame)

    cap.release()
    writer.release()

    st.success("Pose detection and squat counting completed!")

    converted_path = output_path.replace(
        ".mp4", "_converted.mp4"
    )

    conversion = subprocess.run(
        [
            "ffmpeg", "-y", "-i", output_path,
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            converted_path
        ],
        capture_output=True,
        text=True
    )

    if conversion.returncode == 0:
        st.metric("Squat repetitions", rep_count)
        st.video(converted_path)
    else:
        st.error("Video conversion failed")
        st.code(conversion.stderr[-2000:])

    for path in [video_path, output_path, converted_path]:
        if os.path.exists(path):
            os.remove(path)
