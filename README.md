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
