
import streamlit as st
import cv2
import mediapipe as mp
import tempfile
import os
import subprocess
import math

st.set_page_config(page_title="AI Fitness Trainer")
st.title("🏋️ AI Fitness Trainer")
st.write("Upload a workout video for pose detection and repetition counting.")

exercise = st.selectbox("Select Exercise", ["Squat", "Pull-up"])

uploaded = st.file_uploader(
    "Upload workout video",
    type=["mp4", "avi", "mov"]
)


def calculate_angle(a, b, c):
    angle = math.degrees(
        math.atan2(c[1] - b[1], c[0] - b[0])
        - math.atan2(a[1] - b[1], a[0] - b[0])
    )
    angle = abs(angle)
    return 360 - angle if angle > 180 else angle


if uploaded:
    video_path = None
    output_path = None
    converted_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".mp4"
        ) as f:
            f.write(uploaded.read())
            video_path = f.name

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            st.error("Unable to open this video.")
            st.stop()

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25

        output_path = video_path.replace(".mp4", "_out.mp4")
        converted_path = video_path.replace(".mp4", "_converted.mp4")

        writer = cv2.VideoWriter(
            output_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height)
        )

        mp_pose = mp.solutions.pose
        draw = mp.solutions.drawing_utils

        rep_count = 0
        exercise_state = "UP"
        visibility_threshold = 0.5

        with mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as pose:
            while cap.isOpened():
                ok, frame = cap.read()
                if not ok:
                    break

                result = pose.process(
                    cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                )

                label = ""
                visibility = 0

                if result.pose_landmarks:
                    landmarks = result.pose_landmarks.landmark

                    draw.draw_landmarks(
                        frame,
                        result.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS
                    )

                    if exercise == "Squat":
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
                    else:
                        left_ids = [
                            mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                            mp_pose.PoseLandmark.LEFT_ELBOW.value,
                            mp_pose.PoseLandmark.LEFT_WRIST.value
                        ]
                        right_ids = [
                            mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
                            mp_pose.PoseLandmark.RIGHT_ELBOW.value,
                            mp_pose.PoseLandmark.RIGHT_WRIST.value
                        ]

                    left_vis = min(landmarks[i].visibility for i in left_ids)
                    right_vis = min(landmarks[i].visibility for i in right_ids)

                    chosen_ids = (
                        left_ids if left_vis >= right_vis else right_ids
                    )
                    visibility = max(left_vis, right_vis)

                    if visibility >= visibility_threshold:
                        a, b, c = [
                            (
                                landmarks[i].x * width,
                                landmarks[i].y * height
                            )
                            for i in chosen_ids
                        ]

                        angle = calculate_angle(a, b, c)

                        if exercise == "Squat":
                            if angle < 110 and exercise_state == "UP":
                                exercise_state = "DOWN"
                            elif angle > 160 and exercise_state == "DOWN":
                                rep_count += 1
                                exercise_state = "UP"

                            label = f"Knee angle: {int(angle)} deg"

                        else:
                            # Count a pull-up when arms bend, then extend.
                            if angle < 90 and exercise_state == "UP":
                                exercise_state = "PULLING"
                            elif angle > 150 and exercise_state == "PULLING":
                                rep_count += 1
                                exercise_state = "UP"

                            label = f"Elbow angle: {int(angle)} deg"

                        cv2.putText(
                            frame, label, (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 255, 255), 2
                        )

                    cv2.putText(
                        frame,
                        f"{exercise} reps: {rep_count}",
                        (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 255, 0), 2
                    )

                    display_state = (
                        exercise_state
                        if visibility >= visibility_threshold
                        else "Not visible"
                    )

                    cv2.putText(
                        frame, f"State: {display_state}", (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (255, 255, 0), 2
                    )

                else:
                    cv2.putText(
                        frame, "No pose detected", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8, (0, 0, 255), 2
                    )

                writer.write(frame)

        cap.release()
        writer.release()

        st.success(f"{exercise} pose detection completed!")

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
            st.metric(f"{exercise} repetitions", rep_count)
            st.video(converted_path)
        else:
            st.error("Video conversion failed.")
            st.code(conversion.stderr[-2000:])

    finally:
        for path in [video_path, output_path, converted_path]:
            if path and os.path.exists(path):
                os.remove(path)
