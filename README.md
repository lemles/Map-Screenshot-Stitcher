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
**このツールのコードは、ChatGPT (AI) を使用して生成されました。**
私はプログラミングの知識がほとんどありません。アイデアと仕様をAIに伝え、生成されたコードを組み合わせて作成しました。
そのため、コードの品質や保守性には問題がある可能性があります。

**開発を手伝ってくれる方を募集しています！**
リファクタリング、バグ修正、機能追加など、プルリクエスト(Pull Request)を歓迎します。

### 機能
1.  **自動撮影**: 範囲を指定し、矢印キー操作で地図を自動スクロール撮影。
2.  **高度な結合**: テンプレートマッチングと特徴点マッチング(ORB)を併用し、ズレを自動補正。
3.  **大規模対応**: メモリ不足を防ぐ設計で、巨大な画像の生成が可能。

### 使い方
同梱の `manual.html` をご覧ください。
または、Python環境を構築し、以下で起動します。


pip install -r requirements.txt
python main_app.py

###License
MIT License



##🇺🇸 English

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

###Usage

Please verify requirements.txt and run:

code
Bash
download
content_copy
expand_less
pip install -r requirements.txt
python main_app.py

###License
MIT License

