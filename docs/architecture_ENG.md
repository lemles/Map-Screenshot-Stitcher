# AutoMap - Architecture & Component Details

This document provides a deeper dive into the internal structure and logic of the AutoMap tool. It is intended for developers who wish to contribute to the project.

**Contributions Needed:** The code, being AI-generated, currently lacks inline comments. A highly valuable contribution would be to add comments to the code based on this document, or to improve this document itself.

## Table of Contents
1.  [File Structure](#1-file-structure)
2.  [Core Concepts](#2-core-concepts)
3.  [Component Breakdown](#3-component-breakdown)
    - [`main_app.py`](#main_apppy)
    - [`stitcher_app.py`](#stitcher_appy)
    - [`advanced_stitcher.py` (The Engine)](#advanced_stitcherpy-the-engine)
    - [`config_manager.py`](#config_managerpy)
    - [`utils.py`](#utilspy)

---

## 1. File Structure