# advanced_stitcher.py

import cv2
import numpy as np
import os
import re
import gc
import math
import tempfile
from tqdm import tqdm
from scipy.sparse import lil_matrix, vstack
from scipy.sparse.linalg import lsqr
import psutil
from collections import OrderedDict
import json

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except Exception:
    HAS_MATPLOTLIB = False

# --- 【変更点】ここから日本語パス対応のためのヘルパー関数を追加 ---
def imread_safe(filename, flags=cv2.IMREAD_UNCHANGED):
    """日本語(マルチバイト文字)を含むパスの画像を正しく読み込むためのラッパー関数"""
    try:
        n = np.fromfile(filename, dtype=np.uint8)
        img = cv2.imdecode(n, flags)
        return img
    except Exception as e:
        print(f"ERROR: imread_safe でファイルの読み込みに失敗しました: {filename}, error: {e}")
        return None

def imwrite_safe(filename, img, params=None):
    """日本語(マルチバイト文字)を含むパスへ画像を正しく書き込むためのラッパー関数"""
    try:
        ext = os.path.splitext(filename)[1]
        result, buf = cv2.imencode(ext, img, params)
        if result:
            with open(filename, mode='w+b') as f:
                buf.tofile(f)
            return True
        else:
            return False
    except Exception as e:
        print(f"ERROR: imwrite_safe でファイルの書き込みに失敗しました: {filename}, error: {e}")
        return False
# --- 【変更点】ここまでヘルパー関数の追加 ---


class AdvancedStitcher:
    def __init__(self, input_dir, output_file, status_queue=None, config=None):
        self.input_dir = input_dir
        self.output_file = output_file
        self.status_queue = status_queue
        self.config = config if config else {}

        # thresholds and params
        self.min_score_threshold = self.config.get("min_score_threshold", 0.75)
        self.stitch_range = self.config.get("stitch_range", None)
        self.preview_scale = self.config.get("preview_scale", 0.25)
        self.cache_max_items = self.config.get("cache_max_items", 128)
        self.sentinel_color = tuple(self.config.get("sentinel_color", (1, 0, 255)))  # BGR sentinel for memmap
        
        #self.blend = self.config.get("blend", True)  # enable simple feather blending
        self.blend = False

        self.blend_width = self.config.get("blend_width", 64)  # px

        self.image_files = self._get_image_files()
        if not self.image_files:
            raise ValueError("指定されたフォルダに Rxx_Cxx.png 形式のファイルが見つかりません。")

        self.grid_info = self._get_grid_info()
        if self.grid_info is None:
            raise ValueError("画像ファイル名からグリッド情報を構築できませんでした。")

        self.positions = {}
        self.base_image_shape = self._get_base_image_shape()
        self.pairwise_matches = {}

        # ORB and matcher
        self.detector = cv2.ORB_create(nfeatures=self.config.get("nfeatures", 2000))
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

        # simple LRU cache for image reads (grayscale for matching, rgb for render cached separately)
        self._gray_cache = OrderedDict()
        self._rgb_cache = OrderedDict()

        # file map (lowercase keys)
        self._file_map = {os.path.basename(f).lower(): os.path.join(self.input_dir, f) for f in os.listdir(self.input_dir)}

    # ----------------------- utilities -----------------------
    def _update_status(self, message_type, value):
        if self.status_queue:
            self.status_queue.put((message_type, value))

    def _get_image_files(self):
        files = [f for f in os.listdir(self.input_dir) if re.match(r'R\d+_C\d+\.png', f, re.IGNORECASE)]
        return sorted(files, key=lambda f: [int(i) for i in re.findall(r'\d+', f)])

    def _get_image_path(self, r, c):
        target_filename = f"R{r:02d}_C{c:02d}.png".lower()
        return self._file_map.get(target_filename)

    def _get_grid_info(self):
        rows, cols = set(), set()
        for f in self.image_files:
            match = re.search(r'R(\d+)_C(\d+)', f, re.IGNORECASE)
            if match:
                rows.add(int(match.group(1)))
                cols.add(int(match.group(2)))
        if not rows or not cols:
            return None
        return {"min_r": min(rows), "max_r": max(rows), "min_c": min(cols), "max_c": max(cols), "rows": sorted(list(rows)), "cols": sorted(list(cols))}

    def _get_base_image_shape(self):
        first_image_path = os.path.join(self.input_dir, self.image_files[0])
        # 【変更点】cv2.imread を imread_safe に置き換え
        img = imread_safe(first_image_path)
        if img is None:
            raise ValueError(f"基準画像の読み込みに失敗しました: {first_image_path}")
        return img.shape

    # ----------------------- caching reads -----------------------
    def _cache_trim(self):
        # enforce cache sizes
        while len(self._gray_cache) > self.cache_max_items:
            self._gray_cache.popitem(last=False)
        while len(self._rgb_cache) > self.cache_max_items:
            self._rgb_cache.popitem(last=False)

    def read_gray(self, path, downscale=1):
        key = (path, downscale)
        if key in self._gray_cache:
            self._gray_cache.move_to_end(key)
            return self._gray_cache[key]
        # 【変更点】cv2.imread を imread_safe に置き換え
        img = imread_safe(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        if downscale != 1:
            img = cv2.resize(img, (int(img.shape[1]*downscale), int(img.shape[0]*downscale)), interpolation=cv2.INTER_AREA)
        self._gray_cache[key] = img
        self._cache_trim()
        return img

    def read_rgb(self, path):
        if path in self._rgb_cache:
            self._rgb_cache.move_to_end(path)
            return self._rgb_cache[path]
        # 【変更点】cv2.imread を imread_safe に置き換え
        img = imread_safe(path, cv2.IMREAD_COLOR)
        if img is None:
            return None
        self._rgb_cache[path] = img
        self._cache_trim()
        return img

    # ----------------------- verification -----------------------
    def verify_grid(self):
        self._update_status("status", "画像グリッドの完全性を検証中...")
        missing_files = []
        rows, cols = self.grid_info["rows"], self.grid_info["cols"]
        for r in rows:
            for c in cols:
                if self._get_image_path(r, c) is None:
                    missing_files.append(f"R{r:02d}_C{c:02d}.png")
        if missing_files:
            error_msg = (f"画像ファイルが{len(missing_files)}件見つかりません。\n"
                         "撮影が不完全であるか、入力フォルダが正しくありません。\n\n"
                         "見つからないファイル (最初の5件):\n" + "\n".join(missing_files[:5]))
            raise ValueError(error_msg)
        self._update_status("status", "グリッドは完全です。")
        return True

    # ----------------------- matching helpers -----------------------
# advanced_stitcher.py の _match_template メソッド

    def _match_template(self, base_img, target_img, direction):
        h, w = base_img.shape[:2]

        overlap_h_pct = self.config.get("overlap_h_pct", 60) / 100.0
        overlap_v_pct = self.config.get("overlap_v_pct", 40) / 100.0

        if direction.startswith('h'):
            overlap_ratio = overlap_h_pct
        else:
            overlap_ratio = overlap_v_pct

        edge_pct = min(overlap_ratio * 0.4, 0.4)
        search_pct = min(overlap_ratio * 1.2, 0.9)

        if direction.startswith('h'):
            template = base_img[:, int(w*(1-edge_pct)):]
            search_area = target_img[:, :int(w*search_pct)]
        else: # direction == 'v' の場合
            # テンプレートは上の画像の下端
            template = base_img[int(h*(1-edge_pct)):, :]
            
            # ★★★ ここが重要な修正 ★★★
            # 検索範囲を、下の画像の「上部」かつ「横幅すべて」に広げる
            # これにより、左右50pxのズレを完全に許容できる
            search_area = target_img[:int(h*search_pct), :] # X座標の指定を削除し、横幅全体を対象にする
            # ★★★ 修正ここまで ★★★

        if template.size == 0 or search_area.size == 0:
            return None, 0

        res = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        # TM_CCOEFF_NORMEDの場合、max_valが良いスコア
        # スコアの閾値を少し甘め(0.8など)に設定しても良いかもしれない
        if max_val > 0.8: 
            if direction.startswith('h'):
                # オフセット計算は、テンプレートの開始位置と、見つかった位置の差
                offset = (int(w*(1-edge_pct)) - max_loc[0], -max_loc[1])
            else:
                # 縦方向の場合も同様に計算
                offset = (-max_loc[0], int(h*(1-edge_pct)) - max_loc[1])
            return offset, max_val
        return None, max_val
    
    

    def _match_features(self, base_img, target_img):
        kp1, des1 = self.detector.detectAndCompute(base_img, None)
        kp2, des2 = self.detector.detectAndCompute(target_img, None)
        if des1 is None or des2 is None or len(des1) < 8 or len(des2) < 8:
            return None, 0, 0

        knn_matches = self.matcher.knnMatch(des1, des2, k=2)
        good_matches = []
        for pair in knn_matches:
            if len(pair) < 2:
                continue
            m, n = pair
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

        match_count = len(good_matches)
        if match_count < 8:
            return None, 0, match_count

        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        # try default RANSAC then relax if necessary
        for thr in (3.0, 6.0, 10.0):
            M, mask = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=thr)
            if M is not None and mask is not None and np.count_nonzero(mask) >= 6:
                offset_x, offset_y = M[0, 2], M[1, 2]
                score = np.count_nonzero(mask) / len(mask)
                return (-int(round(offset_x)), -int(round(offset_y))), float(score), match_count

        return None, 0, match_count

    # ----------------------- pairwise calculation -----------------------
    def calculate_all_pairwise_matches(self):
        self._update_status("status", "隣接ペアのリストを作成中...")
        rows, cols = self.grid_info["rows"], self.grid_info["cols"]
        jobs = []
        for r_idx, r in enumerate(rows):
            is_forward = (r_idx % 2 == 0)
            for c_idx, c in enumerate(cols):
                if c_idx + 1 < len(cols):
                    direction = "h_forward" if is_forward else "h_backward"
                    jobs.append(((r, c), (r, cols[c_idx+1]), direction))
                if r_idx + 1 < len(rows):
                    jobs.append(((r, c), (rows[r_idx+1], c), "v"))

        if self.stitch_range:
            sr = self.stitch_range
            filtered = []
            for a, b, d in jobs:
                if sr["r_min"] <= a[0] <= sr["r_max"] and sr["c_min"] <= a[1] <= sr["c_max"]:
                    filtered.append((a, b, d))
            jobs = filtered

        if not jobs:
            raise ValueError("マッチング対象の画像ペアが見つかりません。")

        self._update_status("status", f"ハイブリッドマッチングを逐次処理中 ({len(jobs)}ペア)...")
        pbar = tqdm(jobs, desc="Hybrid Matching")
        for i, job in enumerate(pbar):
            base_key, target_key, direction = job
            base_path = self._get_image_path(base_key[0], base_key[1])
            target_path = self._get_image_path(target_key[0], target_key[1])
            if not base_path or not target_path:
                continue

            # status: which pair
            self._update_status("status", f"Matching: {base_key} -> {target_key} ({direction})")
            self._update_status("progress_pair", (base_key, target_key))

            base_img_gray = self.read_gray(base_path)
            target_img_gray = self.read_gray(target_path)
            if base_img_gray is None or target_img_gray is None:
                continue

            offset, score = self._match_template(base_img_gray, target_img_gray, direction)
            match_count = 0
            template_val = score
            if offset is None:
                offset, score, match_count = self._match_features(base_img_gray, target_img_gray)

            # weight correction using match_count
            if offset and score > 0:
                effective_score = float(score) * (math.log(match_count + 1) if match_count > 0 else 1.0)
            else:
                effective_score = score

            if offset and effective_score > self.min_score_threshold:
                self.pairwise_matches[(base_key, target_key)] = (offset, float(score), direction, int(match_count), float(template_val))

            progress_percent = int(((i + 1) / len(jobs)) * 50)
            self._update_status("progress", progress_percent)

    # ----------------------- initial estimation -----------------------
    def estimate_initial_positions(self):
        self._update_status("status", "代表オフセットを計算中...")
        if not self.pairwise_matches:
            raise Exception("マッチングが1件も見つかりませんでした。信頼度閾値を下げて試してください。")

        h_offsets_x, h_offsets_y, v_offsets_x, v_offsets_y = [], [], [], []
        for (off, score, direction, match_count, template_val) in [(v[0], v[1], v[2], v[3], v[4]) for v in self.pairwise_matches.values()]:
            offset = off
            direction = direction
            if direction.startswith('h'):
                h_offsets_x.append(offset[0]); h_offsets_y.append(offset[1])
            else:
                v_offsets_x.append(offset[0]); v_offsets_y.append(offset[1])

        if not h_offsets_x or not v_offsets_x:
            raise Exception("水平または垂直方向のマッチングが見つかりませんでした。")

        median_h_offset = (int(np.median(h_offsets_x)), int(np.median(h_offsets_y)))
        median_v_offset = (int(np.median(v_offsets_x)), int(np.median(v_offsets_y)))

        self._update_status("status", f"代表 H-Offset: {median_h_offset}")
        self._update_status("status", f"代表 V-Offset: {median_v_offset}")
        self._update_status("status", "全画像の初期座標を計算中...")

        rows, cols = self.grid_info["rows"], self.grid_info["cols"]
        row_map = {r: i for i, r in enumerate(rows)}
        col_map = {c: i for i, c in enumerate(cols)}
        for r in rows:
            for c in cols:
                r_idx, c_idx = row_map[r], col_map[c]
                pos_x = c_idx * median_h_offset[0] + r_idx * median_v_offset[0]
                pos_y = c_idx * median_h_offset[1] + r_idx * median_v_offset[1]
                self.positions[(r, c)] = (pos_x, pos_y)

    # ----------------------- global optimization -----------------------
    def run_global_optimization(self):
        self._update_status("status", "グローバル最適化を実行中...")
        image_keys = sorted(self.positions.keys())
        key_to_idx = {key: i for i, key in enumerate(image_keys)}

        valid_matches = []
        for match_keys, match_data in self.pairwise_matches.items():
            k1, k2 = match_keys
            if key_to_idx.get(k1) is not None and key_to_idx.get(k2) is not None:
                valid_matches.append((k1, k2, match_data))

        if not valid_matches:
            return

        num_images = len(image_keys)
        num_matches = len(valid_matches)
        A = lil_matrix((num_matches * 2, num_images * 2), dtype=float)
        b = np.zeros(num_matches * 2)

        for i, (k1, k2, (offset, score, direction, match_count, tmpl_val)) in enumerate(valid_matches):
            idx1 = key_to_idx[k1]
            idx2 = key_to_idx[k2]

            base_weight = (score ** 2)
            # augment by match_count and template val
            base_weight *= (1.0 + math.log(match_count + 1) * 0.1)
            base_weight *= (1.0 + float(tmpl_val) * 0.1)

            #重み付けの調整
            weight = base_weight


            A[i*2, idx1*2] = -weight; A[i*2, idx2*2] = weight; b[i*2] = offset[0] * weight
            A[i*2 + 1, idx1*2 + 1] = -weight; A[i*2 + 1, idx2*2 + 1] = weight; b[i*2 + 1] = offset[1] * weight




        # --- ここからが新しい制約の追加 ---
        # 1. 各画像は、その理想的な初期位置から大きく離れてはいけない、という制約を追加する
        # この制約の強さを決める「重み」。値を大きくするほど、初期位置の格子形状を強く維持する。
        # まずは 0.01 や 0.1 などの小さな値から試すのが良い。
        #値が小さすぎる場合 (例: 0.001)
        #効果がほとんど現れず、以前と同じようにズレてしまう可能性があります。
        #制約が弱すぎて、ペアワイズマッチの誤差の蓄積に負けてしまう状態です。
        #値が大きすぎる場合 (例: 1.0)
        #画像が完全に理想的な格子状に並び、個々のズレが全く補正されなくなります。
        #これは estimate_initial_positions の結果をそのまま使っているのとほぼ同じ状態になり、細かい部分の重なりが不自然になる可能性があります。
        #制約が強すぎて、ペアワイズマッチの情報が無視されてしまう状態です。
        initial_pos_weight = self.config.get("initial_pos_weight", 0.01)

        # 既存のA行列とbベクトルを拡張するためのリストを準備
        A_extra_rows = []
        b_extra_rows = []

        # 全ての画像に対してループ
        for key, idx in key_to_idx.items():
            # この画像の理想的な初期位置を取得
            initial_pos_x, initial_pos_y = self.positions[key] # estimate_initial_positionsで計算済み

            # X座標に関する制約を追加
            # A_extra の idx*2 の位置に重みを設定
            row_x = lil_matrix((1, num_images * 2), dtype=float)
            row_x[0, idx * 2] = initial_pos_weight
            A_extra_rows.append(row_x)
            # b_extra にも対応する値を追加
            b_extra_rows.append(initial_pos_x * initial_pos_weight)

            # Y座標に関する制約を追加
            row_y = lil_matrix((1, num_images * 2), dtype=float)
            row_y[0, idx * 2 + 1] = initial_pos_weight
            A_extra_rows.append(row_y)
            b_extra_rows.append(initial_pos_y * initial_pos_weight)

        # リストを結合して、既存のAとbに連結する
        if A_extra_rows:
            A_extra_2 = vstack(A_extra_rows)
            b_extra_2 = np.array(b_extra_rows)
            A = vstack([A, A_extra_2])
            b = np.concatenate([b, b_extra_2])
        # --- 新しい制約の追加ここまで ---






        # add origin fixation constraint to remove translation ambiguity
        A_extra = lil_matrix((2, num_images * 2), dtype=float)
        A_extra[0, 0] = 1.0  # fix x of first image
        A_extra[1, 1] = 1.0  # fix y of first image
        b_extra = np.zeros(2)

        A = vstack([A, A_extra])
        b = np.concatenate([b, b_extra])

        initial_guess = np.array([self.positions[key] for key in image_keys]).flatten()
        # if initial guess length < solution, pad
        if initial_guess.shape[0] < A.shape[1]:
            initial_guess = np.pad(initial_guess, (0, A.shape[1] - initial_guess.shape[0]))

        result = lsqr(A, b, x0=initial_guess, iter_lim=self.config.get("lsqr_iter", 200))
        optimized_coords = result[0].reshape((num_images, 2))

        for key, idx in key_to_idx.items():
            opt_x, opt_y = optimized_coords[idx, 0], optimized_coords[idx, 1]
            self.positions[key] = (int(round(opt_x)), int(round(opt_y)))



    # ----------------------- rendering -----------------------
    def render_final_image(self):
        self._update_status("status", "最終画像のレンダリング準備中...")
        render_keys = [k for k in self.positions.keys() if not self.stitch_range or (self.stitch_range["r_min"] <= k[0] <= self.stitch_range["r_max"] and self.stitch_range["c_min"] <= k[1] <= self.stitch_range["c_max"])]
        if not render_keys:
            self._update_status("error", "指定範囲に描画対象画像がありません。"); return

        render_positions = {k: self.positions[k] for k in render_keys}
        min_x = min(pos[0] for pos in render_positions.values())
        min_y = min(pos[1] for pos in render_positions.values())
        max_x = max(pos[0] + self.base_image_shape[1] for pos in render_positions.values())
        max_y = max(pos[1] + self.base_image_shape[0] for pos in render_positions.values())
        canvas_width, canvas_height = max_x - min_x, max_y - min_y

        sane_max_width = int(len(self.grid_info["cols"]) * self.base_image_shape[1] * 1.5)
        sane_max_height = int(len(self.grid_info["rows"]) * self.base_image_shape[0] * 1.5)
        if canvas_width <= 0 or canvas_height <= 0 or canvas_width > sane_max_width or canvas_height > sane_max_height:
            self._update_status("error", f"計算された画像サイズ({canvas_width}x{canvas_height})が非現実的です。"); return

        # === 【ここからが新しい戦略の核心部分】 ===
        temp_dir = tempfile.gettempdir()
        
        # 1. カラー情報用の一時ファイル (BGR, 3チャンネル)
        canvas_filename = os.path.join(temp_dir, f"stitcher_canvas_{os.getpid()}.mmap")
        
        # 2. 形状記録用の一時ファイル (Grayscale, 1チャンネル)
        mask_filename = os.path.join(temp_dir, f"stitcher_mask_{os.getpid()}.mmap")

        for f in [canvas_filename, mask_filename]:
            if os.path.exists(f):
                try: os.remove(f)
                except Exception: pass

        try:
            self._update_status("status", "ディスク上に2種類の一時ファイルを作成中...")
            # カラー用キャンバスは黒(0,0,0)で初期化
            canvas = np.memmap(canvas_filename, dtype='uint8', mode='w+', shape=(canvas_height, canvas_width, 3))
            canvas[:] = 255
            
            # 形状記録用マスクは0(透明)で初期化
            canvas_mask = np.memmap(mask_filename, dtype='uint8', mode='w+', shape=(canvas_height, canvas_width))
            canvas_mask[:] = 0
        except Exception as e:
            self._update_status("error", f"一時ファイルの作成に失敗しました: {e}"); return
        
        # === 【ここまでが新しい戦略の核心部分】 ===

        self._update_status("status", "画像をレンダリング中...")
        total_render_images = len(render_keys)
        last_progress = -1

        for i, key in enumerate(tqdm(render_keys, desc="Rendering")):
            img_path = self._get_image_path(key[0], key[1])
            if not img_path: continue
            
            # 【変更点】cv2.imread を imread_safe に置き換え
            img = imread_safe(img_path, cv2.IMREAD_UNCHANGED)
            if img is None: continue

            has_alpha = img.shape[2] == 4
            img_rgb = img[:, :, :3] if has_alpha else img

            # --- 座標計算とクリッピング ---
            pos = self.positions[key]; h, w, _ = img_rgb.shape
            canvas_x_start, canvas_y_start = pos[0] - min_x, pos[1] - min_y
            img_x_start, img_y_start = 0, 0; copy_w, copy_h = w, h

            if canvas_x_start < 0: img_x_start = -canvas_x_start; copy_w -= img_x_start; canvas_x_start = 0
            if canvas_y_start < 0: img_y_start = -canvas_y_start; copy_h -= img_y_start; canvas_y_start = 0
            if canvas_x_start + copy_w > canvas_width: copy_w = canvas_width - canvas_x_start
            if canvas_y_start + copy_h > canvas_height: copy_h = canvas_height - canvas_y_start

            if copy_w <= 0 or copy_h <= 0: continue
            
            # --- 描画領域のビューを取得 ---
            img_rgb_view = img_rgb[img_y_start:img_y_start+copy_h, img_x_start:img_x_start+copy_w]
            dest_slice = canvas[canvas_y_start:canvas_y_start+copy_h, canvas_x_start:canvas_x_start+copy_w]
            mask_slice = canvas_mask[canvas_y_start:canvas_y_start+copy_h, canvas_x_start:canvas_x_start+copy_w]

            # --- 2つのキャンバスへの書き込み ---
            if has_alpha:
                alpha_view = img[img_y_start:img_y_start+copy_h, img_x_start:img_x_start+copy_w, 3]
                # 完全に透明でないピクセルをマスクとして使用
                visible_mask = alpha_view > 0
                dest_slice[visible_mask] = img_rgb_view[visible_mask]
                mask_slice[visible_mask] = 255
            else:
                # アルファがなければ全面上書き
                dest_slice[:] = img_rgb_view
                mask_slice[:] = 255

            # --- 進捗更新 ---
            progress_percent = int(50 + ((i + 1) / total_render_images) * 50)
            if progress_percent > last_progress:
                self._update_status("status", f"レンダリング中 ({i+1}/{total_render_images})"); self._update_status("progress", progress_percent)
                last_progress = progress_percent
        
        canvas.flush()
        canvas_mask.flush()





        # ############## 【ここからがメモリ効率の良い、新しいトリミング処理です】 ##############
        self._update_status("status", "形状マスクを基に、最適なトリミング領域を計算中...")

        # canvas_maskをチェックして、画像データが存在する行と列を探す
        # これにより、巨大な座標配列をメモリ上に作成するのを回避する
        rows_with_data = np.any(canvas_mask, axis=1)
        cols_with_data = np.any(canvas_mask, axis=0)
        
        # データが存在する最初の行と最後の行、最初の列と最後の列を見つける
        y_indices = np.where(rows_with_data)[0]
        x_indices = np.where(cols_with_data)[0]

        if y_indices.size == 0 or x_indices.size == 0:
            self._update_status("status", "有効な画像領域が見つかりませんでした。")
            final_canvas_view = np.zeros((1, 1, 3), dtype=np.uint8)
        else:
            y0, y1 = y_indices[0], y_indices[-1]
            x0, x1 = x_indices[0], x_indices[-1]

            self._update_status("status", "最終領域をメモリにコピー中...")
            # 計算した座標を使い、カラーキャンバスから最終画像を切り出す
            final_canvas_view = np.array(canvas[y0:y1+1, x0:x1+1])
        # ############## 【新しいトリミング処理ここまで】 ##############






        self._update_status("status", "最終画像をファイルに保存中...")
        # 【変更点】cv2.imwrite を imwrite_safe に置き換え
        imwrite_safe(self.output_file, final_canvas_view, [cv2.IMWRITE_PNG_COMPRESSION, 1])
        self._update_status("done", "画像結合が完了しました！")

        # 一時ファイルをクリーンアップ
        del final_canvas_view; del canvas; del canvas_mask; gc.collect()
        for f in [canvas_filename, mask_filename]:
            try:
                os.remove(f)
            except Exception as e:
                self._update_status("status", f"一時ファイル'{os.path.basename(f)}'の削除に失敗: {e}")




    # ----------------------- preview low-res stitch -----------------------
    def preview_stitch(self, out_preview_path=None):
        """Make a quick low-resolution stitch to visually validate offsets."""
        scale = float(self.preview_scale)
        # create temporary in-memory canvas using scaled positions
        self._update_status("status", "プレビュー用低解像度スティッチを実行中...")
        # compute scaled positions
        scaled_positions = {k: (int(v[0]*scale), int(v[1]*scale)) for k, v in self.positions.items()}
        # determine canvas size
        min_x = min(px for px, py in scaled_positions.values())
        min_y = min(py for px, py in scaled_positions.values())
        max_x = max(px + int(self.base_image_shape[1]*scale) for px, py in scaled_positions.values())
        max_y = max(py + int(self.base_image_shape[0]*scale) for px, py in scaled_positions.values())
        cw, ch = max_x - min_x, max_y - min_y
        canvas = np.full((ch, cw, 3), 255, dtype=np.uint8)

        for key, pos in scaled_positions.items():
            path = self._get_image_path(key[0], key[1])
            img = self.read_rgb(path)
            if img is None: continue
            img_s = cv2.resize(img, (int(img.shape[1]*scale), int(img.shape[0]*scale)), interpolation=cv2.INTER_AREA)
            x = pos[0] - min_x; y = pos[1] - min_y
            h, w, _ = img_s.shape
            canvas[y:y+h, x:x+w] = img_s
        if out_preview_path:
            # 【変更点】cv2.imwrite を imwrite_safe に置き換え
            imwrite_safe(out_preview_path, canvas)
            self._update_status("status", f"プレビュー画像を保存しました: {out_preview_path}")
        return canvas

    # ----------------------- heatmap of offsets -----------------------
    def save_offset_heatmap(self, out_path):
        if not HAS_MATPLOTLIB:
            self._update_status("status", "matplotlib が無いためヒートマップは生成できません。")
            return
        offsets = []
        for (k1, k2), (offset, score, direction, match_count, tmpl_val) in self.pairwise_matches.items():
            offsets.append((k1, k2, offset[0], offset[1]))
        if not offsets:
            self._update_status("status", "オフセットデータがないためヒートマップ生成をスキップします。")
            return
        dx = [o[2] for o in offsets]
        dy = [o[3] for o in offsets]
        plt.figure(figsize=(6,6))
        plt.scatter(dx, dy, c=np.hypot(dx, dy), cmap='jet')
        plt.colorbar(label='magnitude')
        plt.xlabel('dx'); plt.ylabel('dy'); plt.title('Pairwise offsets heatmap')
        plt.grid(True)
        plt.savefig(out_path)
        plt.close()
        self._update_status("status", f"オフセットのヒートマップを保存しました: {out_path}")

    # ----------------------- main run -----------------------
    def run(self):
        self.verify_grid()
        self.calculate_all_pairwise_matches()
        self.estimate_initial_positions()
        self.run_global_optimization()
        # optional preview
        if self.config.get('generate_preview'):
            preview_path = self.config.get('preview_path', os.path.splitext(self.output_file)[0] + '_preview.png')
            self.preview_stitch(preview_path)
        # optional heatmap
        if self.config.get('generate_heatmap'):
            hm_path = self.config.get('heatmap_path', os.path.splitext(self.output_file)[0] + '_heatmap.png')
            self.save_offset_heatmap(hm_path)
        self.render_final_image()