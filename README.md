# AutoMap 🗺️

**Web Map Auto-Scroller & Panorama Stitcher / Web地図自動スクロール撮影＆パノラマ結合ツール**

<!-- Badges -->
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

 ![](https://github.com/lemles/Map-Screenshot-Stitcher/blob/main/sample.gif)

---

## 🇯🇵 日本語 (Japanese)

### 概要
ブラウザ上の地図や巨大なコンテンツを自動でジグザグ移動しながらスクリーンショット撮影し、独自のアルゴリズムで継ぎ目のない一枚の巨大な画像に結合するツールです。

### 主な機能
*   **🖱️ 自動撮影**: 範囲を指定し、矢印キー操作をエミュレートして地図などを自動スクロール撮影。
*   **✨ 高度な結合**: テンプレートマッチングと特徴点マッチング(ORB)を併用し、ズレを自動補正。
*   **💾 大規模対応**: ディスクキャッシュ(Memory-mapping)により、メモリ不足を防ぎ、巨大な画像の生成が可能。

### 使い方
1.  Python環境を構築します。
2.  以下のコマンドを実行して、必要なライブラリをインストールします。
    ```bash
    pip install -r requirements.txt
    ```
3.  以下のコマンドでアプリケーションを起動します。
    ```bash
    python main_app.py
    ```
より詳細な使い方は、同梱の `manual.html` をご覧ください。

---

### 🙏 貢献のお願い

**このプロジェクトは、皆さんの様々な形での助けを必要としています。**

#### ⚠️ 開発の背景
このツールはAIとの対話を通じて生まれました。私自身はプログラミングの専門家ではないため、コードの改善にはコミュニティの力が必要です。このプロジェクトは、AIと人間の協業がどのような可能性を秘めているかを探る実験的な試みでもあります。

#### ❤️ ツールを広める・応援する
プログラミングの知識がない方でも、以下の形でプロジェクトに貢献できます。

*   **口コミでの紹介とクレジット表記のお願い:**
    もし"Map Screenshot Stitcher"が便利だと感じたら、ぜひ **X や社内のチャット、ブログなどで「こんな便利なツールがあったよ！」と紹介**していただけると、開発の大きな励みになります。

    また、作成した画像を公開する際には、**もし可能であれば**、画像の隅やキャプション、引用元などに、以下のようなクレジット表記を加えていただけると、プロジェクトの知名度向上に繋がり、大変嬉しく思います。これは**義務ではありません**が、コミュニティの成長のための素晴らしいご協力となります。

    > **クレジット表記の例:**
    > *   `地図画像: "Map Screenshot Stitcher" を使用して作成 (https://github.com/lemles/Map-Screenshot-Stitcher/)`
    > *   `Image created with "Map Screenshot Stitcher" (https://github.com/lemles/Map-Screenshot-Stitcher/)`

#### 💻 コードで貢献する
もちろん、開発者からの貢献はいつでも大歓迎です。どんな小さな貢献でも、心から歓迎します。

*   **コードのリファクタリング:** AIが生成したコードを、よりクリーンで効率的なものに改善する手助けをお願いします。
*   **バグの発見と修正:** 不具合を見つけたら、Issueでの報告や、プルリクエストを送っていただけると大変助かります。
*   **機能のアイデアと実装:** 「こんな機能があったらもっと便利になる」というアイデアを、ぜひIssueで提案してください。
*   **ドキュメントの改善:** `README`や使い方マニュアルの誤字脱字の修正など、文章の改善も歓迎します。
*   **テストの追加:** 予期せぬ不具合を防ぐため、ユニットテストや結合テストを追加する手助けをお願いします。

---

### 🛠️ 技術仕様
このツールは、以下の主要な技術とアルゴリズムで構築されています。詳細については、`docs/`フォルダ内のアーキテクチャドキュメントをご覧ください。

| カテゴリ                  | 主要技術・ライブラリ                                      | 目的                                                           |
| ------------------------- | --------------------------------------------------------- | -------------------------------------------------------------- |
| **GUIフロントエンド**     | `Tkinter`                                                 | クロスプラットフォームで動作する軽量なGUIの実現                    |
| **画像処理・最適化**      | `OpenCV`, `NumPy`, `SciPy`                                | 高度な画像処理と数学的最適化の実行                             |
| &nbsp;&nbsp;↳ **マッチング** | ハイブリッド方式 (`テンプレートマッチング` + `ORB特徴点`) | 画像間の正確な相対位置の特定                                   |
| &nbsp;&nbsp;↳ **最適化**  | グローバル最適化 (`疎行列最小二乗法`)                     | 全体的な歪み（ドリフト誤差）を最小化する最適な配置の計算         |
| **自動操作**              | `PyAutoGUI`, `Keyboard`                                   | スクリーンショット撮影、キーボード操作のエミュレート、ホットキー監視 |
| **CI/CD・テスト**         | `GitHub Actions` (`Flake8`, `Bandit`)                     | コード品質の自動チェックとセキュリティスキャンの実行             |

---

### 📜 ライセンス (License)

このプロジェクトは **AGPLv3** ライセンスの下で公開されています。
このライセンスは**ソースコードの利用**に関するものであり、**本ソフトウェアを使用して生成された成果物（画像ファイルなど）の利用を制限するものではありません。**

#### 【簡単なまとめ】
*   ✅ **ソフトウェアの利用:** このソフトウェア自体は、個人・商用を問わず**完全に無料**で利用できます。
*   ✅ **成果物の利用:** 本ソフトウェアを使って作成した画像（結合後の地図など）は、**自由に利用できます（商用利用も可）。**
*   ❌ **ソースコードの商用組み込み:** このソフトウェアのソースコード（またはその一部）を、**あなたが開発した別のソフトウェアに組み込んで配布・販売する場合**は、あなたのソフトウェア全体のソースコードもAGPLv3で公開する必要があります。

もし、AGPLのソースコードに関する制約を受けずに、あなたのクローズドソースな商用製品でAutoMapの技術を利用したい場合は、別途**商用ライセンス**をご用意しています。ご希望の場合は、作者までお問い合わせください。

#### ❗ 地図の著作権に関する注意
地図の著作権は各地図の制作者にあります。本ソフトウェアを使用する際は、対象となる地図の利用規約を必ず確認し、それに従ってください。Googleマップ等、企業の地図は利用が制限されている場合があります。

<br>

---
---

<br>



### Overview
"Map Screenshot Stitcher" is a tool that automatically scrolls and captures screenshots of web maps (or any large content) in a zigzag pattern and stitches them into a single seamless panoramic image using advanced alignment algorithms.

### Key Features
*   **🖱️ Auto Capture**: Automatically scrolls and captures a specified region by emulating arrow key presses.
*   **✨ Advanced Stitching**: Precisely aligns images using a hybrid method of Template Matching and ORB features.
*   **💾 Large Scale Support**: Designed to handle very large images without running out of memory by using memory-mapping.

### Usage
1.  Set up a Python environment.
2.  Install the required libraries by running the following command:
    ```bash
    pip install -r requirements.txt
    ```
3.  Launch the application with the following command:
    ```bash
    python main_app.py
    ```
For more detailed instructions, please refer to the `manual.html` file included in this repository.

---

### 🙏 Call for Contributions

**This project needs your help in many ways.**

#### ⚠️ Background
This tool was created through a dialogue with an AI . As I am not a programming expert, the power of the community is essential for improving the code. This project is also an experiment to explore the potential of collaboration between AI and humans.

#### ❤️ Spread the Word & Support Us
Even if you don't have programming knowledge, you can contribute to the project in the following ways:

*   **Share it with others & Credit Recommendation:**
    If you find AutoMap useful, **please consider sharing it on social media like X , in your company's chat, or on your blog.** Simply mentioning "I found this useful tool!" would be a great encouragement for us.

    Furthermore, when you publish images created with this tool, **if it is possible**, we would be very grateful if you could add a credit notation. This is **not a requirement**, but it is a wonderful contribution to our community's growth.

    > **Credit Examples:**
    > *   `Map image created using "Map Screenshot Stitcher" (https://github.com/lemles/Map-Screenshot-Stitcher/)`
    > *   `Image created with "Map Screenshot Stitcher" (https://github.com/lemles/Map-Screenshot-Stitcher/)`

#### 💻 Contribute with Code
Of course, contributions from developers are always welcome. Any contribution, no matter how small, is sincerely appreciated.

*   **Code Refactoring:** Help us improve the AI-generated code to be cleaner and more efficient.
*   **Bug Discovery and Fixes:** If you find a bug, reporting it via an Issue or sending a Pull Request would be a great help.
*   **Feature Ideas and Implementation:** If you have an idea for a new feature, please propose it in an Issue.
*   **Documentation Improvements:** Corrections to typos and grammatical errors in the `README` or user manual are also welcome.
*   **Adding Tests:** To prevent unexpected issues, please help add unit tests and integration tests.

---

### 🛠️ Technical Specifications
This tool is built with the following key technologies. For more details, please see the architecture documents in the `docs/` folder.

| Category                    | Key Technologies & Libraries                               | Purpose                                                        |
| --------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------- |
| **GUI Frontend**            | `Tkinter`                                                  | To create a lightweight, cross-platform GUI.                   |
| **Image Processing & Opt.** | `OpenCV`, `NumPy`, `SciPy`                                 | For advanced image processing and mathematical optimization.   |
| &nbsp;&nbsp;↳ **Matching**  | Hybrid Method (`Template Matching` + `ORB Features`)       | To accurately determine the relative positions between images. |
| &nbsp;&nbsp;↳ **Optimization** | Global Optimization (`Sparse Least Squares`)               | To calculate the optimal layout that minimizes overall distortion (drift error). |
| **Automation**              | `PyAutoGUI`, `Keyboard`                                    | For screen capturing, emulating keyboard inputs, and monitoring hotkeys. |
| **CI/CD & Testing**         | `GitHub Actions` (`Flake8`, `Bandit`)                      | To automate code quality checks and security scanning.         |

---

### 📜 License

This project is licensed under the **AGPLv3**.
This license applies to the **use of the source code** and does **not restrict the use of the output (e.g., image files) generated by this software.**

#### 【Simple Summary】
*   ✅ **Using the Software:** You are completely **free to use this software for any purpose, including personal and commercial use.**
*   ✅ **Using the Output:** You are **free to use the images created by this software for any purpose (including commercial use).**
*   ❌ **Commercial embedding of the Source Code:** If you **incorporate the source code (or any part of it) into another software product that you distribute or sell**, you must also release the entire source code of your product under the AGPLv3.

A **Commercial License** is available for businesses and developers who wish to use this technology in a proprietary commercial product without being subject to the terms of the AGPL. Please contact the author for more information.

#### ❗ A Note on Map Copyrights
The copyright of any map belongs to its respective creator. When using this software, you must check and comply with the terms of use for the map you are capturing. Maps from commercial entities like Google Maps may have usage restrictions.
