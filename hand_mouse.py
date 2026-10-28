import math
import time
from pathlib import Path

import cv2
import mediapipe as mp
import pyautogui
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 画面左上にカーソルを移すと緊急停止
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

CAMERA_INDEX = 0

# 感度設定
CURSOR_SMOOTHING = 0.25
SCROLL_SENSITIVITY = 1000
SCROLL_MULTIPLIER = 3

# 指の距離（カメラ映像に対する割合）
TOUCH_THRESHOLD = 0.035
RELEASE_THRESHOLD = 0.065
ZOOM_STEP = 0.025

# タップと判定する最大時間（秒）
TAP_MAX_SECONDS = 0.25

# 手の骨格を描く線
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
]


def draw_hand(frame, landmarks):
    """認識した手の骨格をカメラ画面へ描く。"""
    height, width = frame.shape[:2]
    points = [(int(p.x * width), int(p.y * height)) for p in landmarks]

    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, points[start], points[end], (0, 255, 0), 2)

    for point in points:
        cv2.circle(frame, point, 4, (0, 0, 255), -1)


def zoom(steps):
    """Ctrl + ホイールで拡大・縮小する。"""
    if steps == 0:
        return

    pyautogui.keyDown("ctrl")
    pyautogui.scroll(steps)
    pyautogui.keyUp("ctrl")


def horizontal_scroll(steps):
    """Shift + ホイールで横スクロールする。"""
    if steps == 0:
        return

    pyautogui.keyDown("shift")
    pyautogui.scroll(steps)
    pyautogui.keyUp("shift")


def main():
    model_path = Path(__file__).with_name("hand_landmarker.task")
    if not model_path.exists():
        raise FileNotFoundError(
            "hand_landmarker.task が見つかりません。"
            " hand_mouse.py と同じフォルダーに置いてください。"
        )

    screen_w, screen_h = pyautogui.size()
    cursor_x, cursor_y = screen_w / 2, screen_h / 2

    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not camera.isOpened():
        raise RuntimeError(
            "カメラを開けません。CAMERA_INDEX を 1 に変更して試してください。"
        )

    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    )

    previous_index = None
    scroll_x_remainder = 0.0
    scroll_y_remainder = 0.0

    touching = False
    zooming = False
    touch_started_at = 0.0
    previous_zoom_distance = 0.0
    waiting_for_fingers_to_open = False

    with vision.HandLandmarker.create_from_options(options) as detector:    
        try:
            while True:
                ok, frame = camera.read()
                if not ok:
                    break

                # 鏡のように表示
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb,
                )

                result = detector.detect_for_video(
                    image,
                    int(time.monotonic() * 1000),
                )

                status = "HAND NOT FOUND"
                color = (0, 0, 255)

                if result.hand_landmarks:
                    hand = result.hand_landmarks[0]
                    draw_hand(frame, hand)

                    index_tip = hand[8]   # 人差し指の先
                    thumb_tip = hand[4]   # 親指の先
                    now = time.monotonic()

                    pinch_distance = math.hypot(
                        index_tip.x - thumb_tip.x,
                        index_tip.y - thumb_tip.y,
                    )

                    # タップ／ズーム終了後、いったん指を開くまで待つ
                    if waiting_for_fingers_to_open:
                        status = "RELEASE FINGERS"
                        color = (0, 200, 255)

                        if pinch_distance > RELEASE_THRESHOLD:
                            waiting_for_fingers_to_open = False

                    # 親指と人差し指を触れさせる
                    elif not touching and pinch_distance < TOUCH_THRESHOLD:
                        touching = True
                        zooming = False
                        touch_started_at = now
                        previous_zoom_distance = pinch_distance

                        status = "TOUCH"
                        color = (0, 255, 255)

                    # タップ／ズーム操作中
                    elif touching:
                        elapsed = now - touch_started_at

                        # 短く触れて離す = 左クリック
                        if (
                            not zooming
                            and pinch_distance > RELEASE_THRESHOLD
                            and elapsed <= TAP_MAX_SECONDS
                        ):
                            pyautogui.click()

                            touching = False
                            waiting_for_fingers_to_open = True
                            status = "CLICK"
                            color = (0, 255, 0)

                        # 少し長く触れた後、指を開く = ズーム開始
                        elif (
                            not zooming
                            and pinch_distance > RELEASE_THRESHOLD
                            and elapsed > TAP_MAX_SECONDS
                        ):
                            zooming = True
                            previous_zoom_distance = TOUCH_THRESHOLD

                        # 指を開くと拡大、閉じると縮小
                        if zooming:
                            difference = pinch_distance - previous_zoom_distance
                            zoom_steps = int(difference / ZOOM_STEP)

                            if zoom_steps:
                                zoom(zoom_steps)
                                previous_zoom_distance += (
                                    zoom_steps * ZOOM_STEP
                                )

                            status = "ZOOM"
                            color = (0, 255, 0)

                            # 指を再びくっつけたらズーム操作を終える
                            if pinch_distance < TOUCH_THRESHOLD:
                                touching = False
                                zooming = False
                                waiting_for_fingers_to_open = True

                    # 通常操作
                    else:
                        # 中指も伸ばすとスクロールモード
                        middle_extended = hand[12].y < hand[10].y

                        if middle_extended:
                            if previous_index is not None:
                                dx = index_tip.x - previous_index[0]
                                dy = index_tip.y - previous_index[1]

                                scroll_x_remainder += (
                                    dx * SCROLL_SENSITIVITY
                                )
                                scroll_y_remainder += (
                                    -dy * SCROLL_SENSITIVITY
                                )

                                vertical_steps = int(scroll_y_remainder)
                                horizontal_steps = int(scroll_x_remainder)

                                if vertical_steps:
                                    pyautogui.scroll(
                                        vertical_steps * SCROLL_MULTIPLIER
                                    )
                                    scroll_y_remainder -= vertical_steps

                                if horizontal_steps:
                                    horizontal_scroll(
                                        horizontal_steps * SCROLL_MULTIPLIER
                                    )
                                    scroll_x_remainder -= horizontal_steps

                            status = "SCROLL"
                            color = (255, 255, 255)

                        # 人差し指だけならカーソルを移動
                        else:
                            target_x = index_tip.x * screen_w
                            target_y = index_tip.y * screen_h

                            cursor_x += (
                                target_x - cursor_x
                            ) * CURSOR_SMOOTHING
                            cursor_y += (
                                target_y - cursor_y
                            ) * CURSOR_SMOOTHING

                            pyautogui.moveTo(int(cursor_x), int(cursor_y))

                            status = "MOVE"
                            color = (255, 255, 255)

                    previous_index = (index_tip.x, index_tip.y)

                else:
                    previous_index = None
                    touching = False
                    zooming = False
                    waiting_for_fingers_to_open = False

                cv2.putText(
                    frame,
                    f"{status}  |  Q / Esc: quit",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    color,
                    2,
                )
                cv2.imshow("Hand Gesture Control", frame)

                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break

        finally:
            camera.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()