# AutoMap 🗺️

**Web Map Auto-Scroller & Panorama Stitcher / Web地図自動スクロール撮影＆パノラマ結合ツール**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

## 🇯🇵 日本語 (Japanese)

### 注意！
地図の著作権は地図制作者にあります。完全フリーの地図や、地図の利用規約に基づいて使用してください。
公的機関が発行している地図だと、利用可能の場合があります。
GoogleMAP等、企業作製の地図は利用が制限されている場合があります。ご注意ください。

### 概要
ブラウザ上の地図などを自動でジグザグ移動しながらスクリーンショットを撮影し、独自のアルゴリズムで継ぎ目のない巨大な一枚絵に結合するツールです。

### ⚠️ 開発について (重要)
**このツールのコードは、AI を使用して生成されました。**
私はプログラミングの知識がほとんどありません。アイデアと仕様をAIに伝え、生成されたコードを組み合わせて作成しました。
そのため、コードの品質や保守性には問題がある可能性があります。

**開発を手伝ってくれる方を募集しています！**
リファクタリング、バグ修正、機能追加など、プルリクエスト(Pull Request)を歓迎します。

### 機能
1.  **自動撮影**: 範囲を指定し、矢印キー操作で地図を自動スクロール撮影。
2.  **高度な結合**: テンプレートマッチングと特徴点マッチング(ORB)を併用し、ズレを自動補正。
3.  **大規模対応**: メモリ不足を防ぐ設計で、巨大な画像の生成が可能。

### 🛠️ 主な技術仕様 / Key Technical Specifications

このツールは、以下の主要な技術とアルゴリズムで構築されています。これらの技術に詳しい方からのリファクタリングや改善提案を特に歓迎します！

| カテゴリ                  | 主要技術・ライブラリ                                                               | 目的                                                           |
| ------------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **GUIフロントエンド**     | `Tkinter` (Python標準)                                                             | クロスプラットフォームで動作する軽量なGUIの実現                    |
| **画像処理・最適化**      | `OpenCV`, `NumPy`, `SciPy`                                                         | 高度な画像処理と数学的最適化の実行                             |
| &nbsp;&nbsp;↳ **マッチング** | ハイブリッド方式 (`テンプレートマッチング` + `ORB特徴点`)                         | 画像間の正確な相対位置の特定                                   |
| &nbsp;&nbsp;↳ **最適化**  | グローバル最適化 (`疎行列最小二乗法`)                                              | 全体的な歪み（ドリフト誤差）を最小化する最適な配置の計算         |
| &nbsp;&nbsp;↳ **メモリ管理** | メモリマップトファイル (`np.memmap`)                                               | RAM容量を超える巨大な画像のレンダリングを可能にする              |
| **自動操作**              | `PyAutoGUI`, `Keyboard`                                                            | スクリーンショット撮影、キーボード操作のエミュレート、ホットキー監視 |
| **CI/CD・テスト**         | `GitHub Actions` (`Flake8`, `Bandit`)                                              | コード品質の自動チェックとセキュリティスキャンの実行     


### 処理フローの概要 / Processing Flow Overview

このツールは、大きく分けて2つの独立したアプリケーション（撮影アプリと結合アプリ）で構成されており、それぞれが明確な役割を担っています。

1.  **撮影アプリ (`main_app.py`)**
    *   **役割:** ユーザーインターフェースの提供と、ブラウザの自動操作による画像収集。
    *   **起動:** `python main_app.py` で直接実行します。
    *   **GUI構築:** `Tkinter` を使用してメインウィンドウ（撮影タブ、結合タブ）を構築します。ウィンドウの位置や設定値は `config.json` に保存されます (`config_manager.py`)。
    *   **自動撮影プロセス:**
        1.  ユーザーが「▶ 開始」ボタンを押すと、GUIがフリーズしないように別スレッド (`threading`) で自動化ロジックが開始されます。
        2.  `pyautogui` ライブラリを使用して、設定された回数だけ矢印キーをエミュレートし、ブラウザ画面をスクロールさせます。
        3.  各位置で指定範囲のスクリーンショットを撮影し、`Rxx_Cxx.png` という命名規則で指定フォルダに保存します。
        4.  Windows環境では、撮影中にPCがスリープするのを防ぐため、`ctypes` を介してOSの省電力機能を一時的に抑制します。

2.  **結合アプリ (`stitcher_app.py` → `advanced_stitcher.py`)**
    *   **役割:** 撮影された多数の画像を、一枚の巨大なパノラマ画像に結合する。
    *   **起動:** 撮影アプリの「結合」タブからモーダルウィンドウとして起動されます。
    *   **プロセス分離:**
        1.  `stitcher_app.py` は結合設定を行うための `Tkinter` GUIです。
        2.  「結合開始」が押されると、非常に重い画像処理を `multiprocessing` を使用して完全に別のプロセスで実行し、GUIの応答性を維持します。
    *   **コアエンジン (`advanced_stitcher.py`):**
        1.  **ペアワイズマッチング:** `OpenCV` を利用し、隣接する全画像ペアの相対的なズレ（オフセット）を計算します。テンプレートマッチングと特徴点マッチング（ORB）を併用するハイブリッド方式です。
        2.  **グローバル最適化:** 全てのズレ情報を元に、`scipy.sparse.linalg.lsqr` を用いて、全体の歪みが最小になるような各画像の最終座標を一括で計算します。これにより、誤差の蓄積（ドリフト現象）を防ぎます。
        3.  **レンダリング:** `numpy.memmap` を使ってディスク上に巨大な仮想キャンバスを作成します。これにより、PCの搭載RAM容量を大幅に超えるような巨大な画像でも、メモリ不足に陥ることなく最終的な一枚絵を生成できます。


### 使い方
同梱の `manual.html` をご覧ください。
または、Python環境を構築し、以下で起動します。


pip install -r requirements.txt

python main_app.py


## 🙏 貢献のお願い (Call for Contributions)

### 🇯🇵 日本語 (Japanese)

**このプロジェクトは、皆さんの助けを必要としています。**

前述の通り、このツールはAI（ChatGPT）との対話を通じて生まれました。私自身はプログラミングの専門家ではないため、生成されたコードの詳細なレビューや改善が難しい状況です。

しかし、このツールのアイデアと機能性には大きな可能性があると信じています。もしあなたがプログラミングの知識をお持ちで、このプロジェクトに少しでも興味を持っていただけたなら、ぜひ力を貸していただけないでしょうか。

どのような小さな貢献でも、心から歓迎します。

#### どんな助けが必要ですか？

*   **コードのリファクタリング:**
    AIが生成したコードには、冗長な部分や非効率的な箇所があるかもしれません。よりクリーンで、読みやすく、効率的なコードに改善する手助けをお願いします。

*   **バグの発見と修正:**
    ツールを使ってみて、おかしな挙動やエラーを見つけたら、ぜひIssueで報告してください。もし修正方法がわかるなら、プルリクエストを送っていただけると大変助かります。

*   **機能のアイデアと実装:**
    「こんな機能があったらもっと便利になる」というアイデアはありませんか？Issueで提案していただくだけでも貴重な貢献です。

*   **ドキュメントの改善:**
    `README`や使い方マニュアル（`manual.html`）の誤字脱字の修正、より分かりやすい表現への変更など、文章の改善も歓迎します。

*   **テストの追加:**
    予期せぬ不具合を防ぐため、ユニットテストや結合テストを追加する手助けをお願いします。

このプロジェクトは、AIと人間の協業がどのような可能性を秘めているかを探る実験的な試みでもあります。あなたのスキルと知識が、このツールをより良いものへと成長させる鍵となります。

### License
MIT License



### Caution!
The copyright of the map belongs to the mapmaker. Please use completely free maps or maps in accordance with the map's terms of use.
Maps issued by public institutions may be usable.
Maps created by companies, such as Google Maps, may have usage restrictions. Please be careful.

###Overview

AutoMap is a tool that automatically scrolls and captures screenshots of web maps (or any large content) and stitches them into a single seamless panorama image using advanced alignment algorithms.

###⚠️ About Development (Important)

The code for this tool was entirely generated using ChatGPT (AI).
I have very little knowledge of programming. I provided the ideas and specifications to the AI, and assembled the generated code.
Therefore, code quality and maintainability might not be optimal.

Contributions are welcome!
I am looking for developers who can help with refactoring, bug fixing, and feature additions. Pull Requests are highly appreciated.

###Features

Auto Capture: Automatically scrolls and captures the specified region using simulated arrow key presses.

Advanced Stitching: Uses hybrid matching (Template Matching + ORB features) to align images precisely.

Large Scale: Designed to handle very large images without running out of memory (using memory mapping).

### 🇺🇸 English Version

This tool is built with the following key technologies and algorithms. We especially welcome refactoring and improvement suggestions from those familiar with these technologies!

| Category                    | Key Technologies & Libraries                                                     | Purpose                                                        |
| --------------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **GUI Frontend**            | `Tkinter` (Python Standard Library)                                              | To create a lightweight, cross-platform GUI.                   |
| **Image Processing & Opt.** | `OpenCV`, `NumPy`, `SciPy`                                                         | For advanced image processing and mathematical optimization.   |
| &nbsp;&nbsp;↳ **Matching**  | Hybrid Method (`Template Matching` + `ORB Features`)                               | To accurately determine the relative positions between images. |
| &nbsp;&nbsp;↳ **Optimization** | Global Optimization (`Sparse Least Squares`)                                     | To calculate the optimal layout that minimizes overall distortion (drift error). |
| &nbsp;&nbsp;↳ **Memory Mgmt.** | Memory-mapped Files (`np.memmap`)                                                | To enable rendering of huge images that exceed RAM capacity.   |
| **Automation**              | `PyAutoGUI`, `Keyboard`                                                            | For screen capturing, emulating keyboard inputs, and monitoring hotkeys. |
| **CI/CD & Testing**         | `GitHub Actions` (`Flake8`, `Bandit`)                                              | To automate code quality checks and security scanning.         |


#### 🇺🇸 English

This tool consists of two main, independent applications (a capturing app and a stitching app), each with a distinct role.

1.  **Capturing App (`main_app.py`)**
    *   **Role:** Provides the user interface and automates image collection by controlling the browser.
    *   **Launch:** Executed directly via `python main_app.py`.
    *   **GUI Construction:** Builds the main window (Capture tab, Stitch tab) using `Tkinter`. Window geometry and settings are saved to `config.json` (managed by `config_manager.py`).
    *   **Automated Capture Process:**
        1.  When the user clicks the "▶ Run" button, the automation logic starts in a separate thread (`threading`) to prevent the GUI from freezing.
        2.  The `pyautogui` library is used to emulate arrow key presses a configured number of times, scrolling the browser view.
        3.  A screenshot of the specified region is taken at each position and saved to the designated folder with the naming convention `Rxx_Cxx.png`.
        4.  On Windows, power-saving features are temporarily suppressed via `ctypes` to prevent the PC from sleeping during long captures.

2.  **Stitching App (`stitcher_app.py` → `advanced_stitcher.py`)**
    *   **Role:** Stitches the numerous captured images into a single, massive panoramic image.
    *   **Launch:** Opened as a modal window from the "Join" tab of the capturing app.
    *   **Process Separation:**
        1.  `stitcher_app.py` is the `Tkinter` GUI for configuring stitching options.
        2.  When "Start Stitching" is clicked, the computationally intensive image processing is executed in a completely separate process using `multiprocessing`, maintaining GUI responsiveness.
    *   **Core Engine (`advanced_stitcher.py`):**
        1.  **Pairwise Matching:** Utilizes `OpenCV` to calculate the relative offset between all adjacent image pairs using a hybrid approach of Template Matching and ORB feature detection.
        2.  **Global Optimization:** Based on all offset data, it calculates the final coordinates for every image that minimize overall distortion. This is done in a single step using `scipy.sparse.linalg.lsqr`, preventing the accumulation of errors (drift).
        3.  **Rendering:** Creates a large virtual canvas on disk using `numpy.memmap`. This allows the tool to render a final image that is significantly larger than the available RAM without causing memory errors.


###Usage

Please verify requirements.txt and run:

code
Bash
download
content_copy
expand_less
pip install -r requirements.txt
python main_app.py


**This project needs your help.**

As mentioned, this tool was born from a dialogue with an AI (ChatGPT). As I am not a programming expert myself, I find it difficult to conduct detailed reviews and improvements on the generated code.

However, I believe the idea and functionality of this tool have great potential. If you have programming knowledge and are even slightly interested in this project, I would be incredibly grateful for your contribution.

Any contribution, no matter how small, is sincerely welcome.

#### How can you help?

*   **Code Refactoring:**
    The AI-generated code may have redundant or inefficient parts. Please help improve it to be cleaner, more readable, and more efficient.

*   **Bug Discovery and Fixes:**
    If you find any strange behavior or errors while using the tool, please report them via an Issue. If you know how to fix it, a Pull Request would be greatly appreciated.

*   **Feature Ideas and Implementation:**
    Do you have an idea for a feature that would make this tool even more useful? Proposing it in an Issue is a valuable contribution in itself.

*   **Documentation Improvements:**
    Corrections to typos and grammatical errors in the `README` or user manual (`manual.html`), or suggestions for clearer wording, are also welcome.

*   **Adding Tests:**
    To prevent unexpected issues, please help add unit tests and integration tests.

This project is also an experiment to explore the potential of collaboration between AI and humans. Your skills and knowledge are the key to evolving this tool into something better.


### License
MIT License
