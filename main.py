import cv2
from pose_detector import PoseDetector

cap = cv2.VideoCapture("squat.mp4")
detector = PoseDetector()

count = 0
direction = 0

# check video opened or not
if not cap.isOpened():
    print("Error: Video not found or cannot open")
    exit()

while True:
    success, img = cap.read()

    # VERY IMPORTANT FIX
    if not success:
        print("Video ended")
        break

    img = detector.findPose(img)
    lmList = detector.getPosition(img)

    if lmList:
        shoulder = lmList[12][2]
        elbow = lmList[14][2]

        if elbow > shoulder:
            if direction == 0:
                count += 0.5
                direction = 1
        else:
            if direction == 1:
                count += 0.5
                direction = 0

    cv2.putText(img, f'Pushups: {int(count)}', (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

    cv2.imshow("AI Fitness Trainer", img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()