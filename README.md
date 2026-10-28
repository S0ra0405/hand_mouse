# Hand Gesture Mouse

Webカメラで手の動きを認識し、Windows のマウス操作・スクロール・ズームを行う Python プログラムです。

## 機能

- 人差し指でマウスカーソルを移動
- 親指と人差し指を短くタップして左クリック
- 人差し指と中指を伸ばして動かすと縦・横スクロール
- 親指と人差し指を触れた状態から開閉して拡大・縮小
- `Q` または `Esc` キーで終了
- カーソルを画面左上へ移動すると緊急停止

## 必要な環境

- Windows
- Python 3.13 以降
- Webカメラ

## インストール

必要なライブラリをインストールします。

```powershell
py -m pip install opencv-python mediapipe pyautogui
```

次に、MediaPipe の手認識モデルを `hand_mouse.py` と同じフォルダーへダウンロードします。

```powershell
curl.exe -L -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

フォルダー構成は以下のようになります。

```text
hand_mouse/
├── hand_mouse.py
├── hand_landmarker.task
└── README.md
```

## 実行方法

PowerShell でプログラムのフォルダーを開き、実行します。

```powershell
py hand_mouse.py
```

カメラ映像のウィンドウが開いたら、手をカメラに映してください。

## 操作方法

- 人差し指だけを伸ばして動かす  
  マウスカーソルを移動します。

- 親指と人差し指を素早く触れてから離す  
  左クリックします。

- 人差し指と中指を伸ばして動かす  
  縦・横スクロールします。

- 親指と人差し指を少し長めに触れた後で開く  
  拡大します。

- 開いた親指と人差し指を閉じる  
  縮小します。

- `Q` または `Esc`  
  プログラムを終了します。

## 感度の調整

`hand_mouse.py` の冒頭にある数値で操作感を変更できます。

```python
CURSOR_SMOOTHING = 0.25
SCROLL_SENSITIVITY = 1000
SCROLL_MULTIPLIER = 3
```

- カーソルが速すぎる・揺れる場合  
  `CURSOR_SMOOTHING` を小さくします。例：`0.15`

- スクロールが遅い場合  
  `SCROLL_SENSITIVITY` を大きくします。例：`1500`

- スクロールが速すぎる場合  
  `SCROLL_SENSITIVITY` を小さくします。例：`600`

## トラブルシューティング

### カメラが開かない

`hand_mouse.py` 内の次の数値を `1` に変更して試してください。

```python
CAMERA_INDEX = 1
```

### `hand_landmarker.task が見つかりません` と表示される

`hand_landmarker.task` が `hand_mouse.py` と同じフォルダーにあるか確認してください。

### 管理者として起動したアプリを操作できない

通常権限で起動した Python プログラムからは、管理者権限のアプリを操作できない場合があります。まずはブラウザやメモ帳で動作確認してください。

## 使用ライブラリ

- [OpenCV](https://opencv.org/)
- [MediaPipe](https://ai.google.dev/edge/mediapipe)
- [PyAutoGUI](https://pyautogui.readthedocs.io/)