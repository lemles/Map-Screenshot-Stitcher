# stitcher_app.py 

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import queue
import multiprocessing
import os
import shutil
import tempfile
import sys
import platform # OS判定用

# AdvancedStitcherを動的にインポートする試み
try:
    from advanced_stitcher import AdvancedStitcher
except ImportError:
    try:
        from advanced_stitcher import AdvancedStitcher
    except ImportError:
        AdvancedStitcher = None # 実行時にエラーチェック

# --- 翻訳辞書 ---
TRANSLATIONS = {
    "ja": {
        "title": "画像結合ツール",
        "btn_close": "閉じる",
        "grp_input": "1. 入力フォルダ",
        "btn_select": "選択...",
        "grp_output": "2. 出力ファイル",
        "grp_options": "3. オプション",
        "chk_range": "部分結合を有効にする",
        "lbl_row": "行(R):",
        "lbl_col": "列(C):",
        "lbl_thresh": "信頼度閾値:",
        "lbl_weight": "格子維持の重み:",
        "lbl_over_h": "横の重なり(%):",
        "lbl_over_v": "縦の重なり(%):",
        "chk_preview": "低解像度プレビューを生成",
        "chk_heatmap": "オフセットヒートマップを生成",
        "lbl_dest_any": "  ← 出力先 (任意):",
        "btn_run": "結合開始",
        "grp_status": "進捗",
        "status_ready": "準備完了",
        "status_done": "完了",
        "status_err": "エラー",
        "msg_input_err": "有効な入力フォルダと出力を選択してください。",
        "msg_val_err": "オプションの数値が正しくありません。\n{}",
        "msg_mod_err": "AdvancedStitcherモジュールをインポートできませんでした。",
        "msg_grid_err": "グリッド検証エラー",
        "msg_disk_warn": "一時ファイルのために十分な空き容量がない可能性があります。\n推定必要容量: {} MB\n空き容量: {} MB\nそれでも続行しますか？",
        "msg_close_warn": "結合処理が実行中です。本当に終了しますか？",
        "msg_done_desc": "{}\n保存先: {}"
    },
    "en": {
        "title": "Image Stitcher",
        "btn_close": "Close",
        "grp_input": "1. Input Folder",
        "btn_select": "Select...",
        "grp_output": "2. Output File",
        "grp_options": "3. Options",
        "chk_range": "Enable Partial Stitching",
        "lbl_row": "Rows(R):",
        "lbl_col": "Cols(C):",
        "lbl_thresh": "Score Thresh:",
        "lbl_weight": "Grid Weight:",
        "lbl_over_h": "Overlap H(%):",
        "lbl_over_v": "Overlap V(%):",
        "chk_preview": "Generate Low-Res Preview",
        "chk_heatmap": "Generate Offset Heatmap",
        "lbl_dest_any": "  ← Dest (Opt):",
        "btn_run": "Start Stitching",
        "grp_status": "Progress",
        "status_ready": "Ready",
        "status_done": "Done",
        "status_err": "Error",
        "msg_input_err": "Select valid input folder and output file.",
        "msg_val_err": "Invalid option values.\n{}",
        "msg_mod_err": "Could not import AdvancedStitcher module.",
        "msg_grid_err": "Grid Verification Error",
        "msg_disk_warn": "Insufficient disk space for temp files likely.\nEst: {} MB\nFree: {} MB\nContinue anyway?",
        "msg_close_warn": "Stitching is running. Really exit?",
        "msg_done_desc": "{}\nSaved to: {}"
    }
}

def stitcher_worker_wrapper(input_dir, output_file, q, config):
    try:
        if AdvancedStitcher is None:
            raise ImportError("advanced_stitcher module not found.")
        stitcher = AdvancedStitcher(input_dir=input_dir, output_file=output_file, status_queue=q, config=config)
        stitcher.run()
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        q.put(("error", f"Error: {e}\n\nDetails:\n{error_details}"))

class StitcherApp(tk.Toplevel):
    def __init__(self, master=None, config=None):
        super().__init__(master)
        self.config = config if config else {}
        # 言語設定取得
        self.lang_code = self.config.get('language', 'ja')
        
        self.title(self.t('title'))
        # ウィンドウサイズを少し広げる（英語対応のため）
        self.geometry("600x750")
        self.transient(master); self.grab_set()
        
        self.status_queue = multiprocessing.Queue()
        self.stitching_process = None
        
        self.setup_styles()

        main_frame = ttk.Frame(self, padding=(12, 12))
        main_frame.pack(fill=tk.BOTH, expand=True)

        self._create_io_widgets(main_frame)
        self._create_options_widgets(main_frame)
        self._create_run_widgets(main_frame)
        self._create_status_widgets(main_frame)

        ttk.Button(main_frame, text=self.t('btn_close'), command=self.on_closing).pack(side="bottom", fill="x", pady=(10, 0))

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_output_paths()
        self.toggle_extra_options()

    def get_ui_font_family(self):
        sys_name = platform.system()
        if sys_name == "Windows": return "Segoe UI"
        elif sys_name == "Darwin": return "System"
        else: return "TkDefaultFont"

    def setup_styles(self):
        style = ttk.Style()
        font_family = self.get_ui_font_family()
        base_font = (font_family, 9)
        bold_font = (font_family, 9, "bold")
        
        self.option_add('*font', base_font)
        style.configure("Accent.TButton", font=(font_family, 11, "bold"))
        style.configure("TLabel", font=base_font)
        style.configure("TButton", font=base_font)

    def t(self, key):
        return TRANSLATIONS.get(self.lang_code, TRANSLATIONS["ja"]).get(key, key)

    def _create_io_widgets(self, parent):
        input_frame = ttk.LabelFrame(parent, text=self.t('grp_input'), padding=10)
        input_frame.pack(fill="x", pady=5)
        init_in = self.config.get('save_folder', os.getcwd())
        self.input_path = tk.StringVar(value=init_in)
        ttk.Entry(input_frame, textvariable=self.input_path, state="readonly").pack(fill="x", expand=True, side="left", padx=(0, 5))
        ttk.Button(input_frame, text=self.t('btn_select'), command=self.select_input_folder).pack(side="right")

        output_frame = ttk.LabelFrame(parent, text=self.t('grp_output'), padding=10)
        output_frame.pack(fill="x", pady=5)
        self.output_path = tk.StringVar()
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path, state="readonly")
        self.output_entry.pack(fill="x", expand=True, side="left", padx=(0, 5))
        ttk.Button(output_frame, text=self.t('btn_select'), command=self.select_output_file).pack(side="right")

    def _create_options_widgets(self, parent):
        option_frame = ttk.LabelFrame(parent, text=self.t('grp_options'), padding=10)
        option_frame.pack(fill="x", pady=10)

        # Partial Stitching
        self.use_range = tk.BooleanVar(value=False)
        ttk.Checkbutton(option_frame, text=self.t('chk_range'), variable=self.use_range, command=self.toggle_range_frame).pack(anchor="w")
        self.range_frame = ttk.Frame(option_frame)
        range_grid = ttk.Frame(self.range_frame); range_grid.pack(pady=5)
        
        ttk.Label(range_grid, text=self.t('lbl_row')).grid(row=0, column=0, sticky="w", padx=5)
        self.r_min_var = tk.StringVar(value="1"); ttk.Entry(range_grid, textvariable=self.r_min_var, width=6).grid(row=0, column=1)
        ttk.Label(range_grid, text="～").grid(row=0, column=2, padx=5)
        self.r_max_var = tk.StringVar(value="10"); ttk.Entry(range_grid, textvariable=self.r_max_var, width=6).grid(row=0, column=3)
        
        ttk.Label(range_grid, text=self.t('lbl_col')).grid(row=1, column=0, sticky="w", padx=5, pady=(5,0))
        self.c_min_var = tk.StringVar(value="1"); ttk.Entry(range_grid, textvariable=self.c_min_var, width=6).grid(row=1, column=1)
        ttk.Label(range_grid, text="～").grid(row=1, column=2, padx=5)
        self.c_max_var = tk.StringVar(value="10"); ttk.Entry(range_grid, textvariable=self.c_max_var, width=6).grid(row=1, column=3)

        # Settings Grid
        settings_frame = ttk.Frame(option_frame)
        settings_frame.pack(fill="x", pady=5)
        settings_frame.columnconfigure(1, weight=1); settings_frame.columnconfigure(3, weight=1)

        # Row 0
        ttk.Label(settings_frame, text=self.t('lbl_thresh')).grid(row=0, column=0, sticky="w")
        self.score_var = tk.StringVar(value=str(self.config.get("min_score_threshold", 0.75)))
        ttk.Entry(settings_frame, textvariable=self.score_var, width=8).grid(row=0, column=1, sticky="w", padx=(5, 10))

        ttk.Label(settings_frame, text=self.t('lbl_weight')).grid(row=0, column=2, sticky="w")
        self.pos_weight_var = tk.StringVar(value="0.01") 
        ttk.Entry(settings_frame, textvariable=self.pos_weight_var, width=8).grid(row=0, column=3, sticky="w", padx=(5, 0))

        # Row 1
        ttk.Label(settings_frame, text=self.t('lbl_over_h')).grid(row=1, column=0, sticky="w", pady=(5,0))
        self.overlap_h_var = tk.StringVar(value="60") 
        ttk.Entry(settings_frame, textvariable=self.overlap_h_var, width=8).grid(row=1, column=1, sticky="w", padx=(5, 10), pady=(5,0))

        ttk.Label(settings_frame, text=self.t('lbl_over_v')).grid(row=1, column=2, sticky="w", pady=(5,0))
        self.overlap_v_var = tk.StringVar(value="40") 
        ttk.Entry(settings_frame, textvariable=self.overlap_v_var, width=8).grid(row=1, column=3, sticky="w", padx=(5, 0), pady=(5,0))

        # Extra Outputs
        self.gen_preview = tk.BooleanVar(value=False); self.gen_heatmap = tk.BooleanVar(value=False)
        extras_frame = ttk.Frame(option_frame); extras_frame.pack(fill="x", pady=5)
        
        ttk.Checkbutton(extras_frame, text=self.t('chk_preview'), variable=self.gen_preview, command=self.toggle_extra_options).grid(row=0, column=0, sticky="w", columnspan=2)
        ttk.Checkbutton(extras_frame, text=self.t('chk_heatmap'), variable=self.gen_heatmap, command=self.toggle_extra_options).grid(row=1, column=0, sticky="w", columnspan=2)
        
        self.preview_path_label = ttk.Label(extras_frame, text=self.t('lbl_dest_any'))
        self.preview_path_label.grid(row=0, column=2, padx=(10, 2), sticky="e")
        self.preview_path_var = tk.StringVar()
        self.preview_path_entry = ttk.Entry(extras_frame, textvariable=self.preview_path_var, width=18)
        self.preview_path_entry.grid(row=0, column=3, sticky="ew")
        self.preview_path_button = ttk.Button(extras_frame, text="...", command=self.select_preview_path, width=3)
        self.preview_path_button.grid(row=0, column=4, padx=(2,0))

        self.heatmap_path_label = ttk.Label(extras_frame, text=self.t('lbl_dest_any'))
        self.heatmap_path_label.grid(row=1, column=2, padx=(10, 2), sticky="e")
        self.heatmap_path_var = tk.StringVar()
        self.heatmap_path_entry = ttk.Entry(extras_frame, textvariable=self.heatmap_path_var, width=18)
        self.heatmap_path_entry.grid(row=1, column=3, sticky="ew")
        self.heatmap_path_button = ttk.Button(extras_frame, text="...", command=self.select_heatmap_path, width=3)
        self.heatmap_path_button.grid(row=1, column=4, padx=(2,0))
    
    def _create_run_widgets(self, parent):
        run_frame = ttk.Frame(parent); run_frame.pack(fill="x", pady=(10, 5))
        self.run_button = ttk.Button(run_frame, text=self.t('btn_run'), command=self.start_stitching, style="Accent.TButton")
        self.run_button.pack(fill="x", ipady=6)
    
    def _create_status_widgets(self, parent):
        status_frame = ttk.LabelFrame(parent, text=self.t('grp_status'), padding=10)
        status_frame.pack(fill="both", expand=True, pady=5)
        self.status_label = ttk.Label(status_frame, text=self.t('status_ready'), anchor="w", wraplength=400)
        self.status_label.pack(fill="x")
        self.progress = ttk.Progressbar(status_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=6)
        self.pair_label = ttk.Label(status_frame, text="", anchor="w", foreground="blue")
        self.pair_label.pack(fill="x")

    def toggle_range_frame(self):
        if self.use_range.get(): self.range_frame.pack(anchor="w", pady=5)
        else: self.range_frame.pack_forget()

    def toggle_extra_options(self):
        state = "normal" if self.gen_preview.get() else "disabled"
        self.preview_path_label.config(state=state); self.preview_path_entry.config(state=state); self.preview_path_button.config(state=state)
        state = "normal" if self.gen_heatmap.get() else "disabled"
        self.heatmap_path_label.config(state=state); self.heatmap_path_entry.config(state=state); self.heatmap_path_button.config(state=state)

    def update_output_paths(self):
        input_dir = self.input_path.get()
        if not input_dir: return
        base_name = os.path.basename(os.path.normpath(input_dir))
        output_dir = os.path.dirname(input_dir)
        self.output_path.set(os.path.join(output_dir, f"{base_name}_stitched.png"))

    def select_input_folder(self):
        folder = filedialog.askdirectory(initialdir=self.input_path.get())
        if folder: self.input_path.set(folder); self.update_output_paths()

    def select_output_file(self):
        filename = filedialog.asksaveasfilename(initialdir=os.path.dirname(self.output_path.get()), initialfile=os.path.basename(self.output_path.get()), defaultextension=".png", filetypes=[("PNG", "*.png")])
        if filename: self.output_path.set(filename)

    def select_preview_path(self):
        p_name = os.path.splitext(os.path.basename(self.output_path.get()))[0] + "_preview.png"
        filename = filedialog.asksaveasfilename(initialfile=p_name, defaultextension=".png", filetypes=[("PNG", "*.png")])
        if filename: self.preview_path_var.set(filename)

    def select_heatmap_path(self):
        h_name = os.path.splitext(os.path.basename(self.output_path.get()))[0] + "_heatmap.png"
        filename = filedialog.asksaveasfilename(initialfile=h_name, defaultextension=".png", filetypes=[("PNG", "*.png")])
        if filename: self.heatmap_path_var.set(filename)

    def start_stitching(self):
        if self.stitching_process and self.stitching_process.is_alive(): return
        input_dir, output_file = self.input_path.get(), self.output_path.get()
        if not all([input_dir, output_file, os.path.isdir(input_dir)]):
            messagebox.showwarning(self.t('status_err'), self.t('msg_input_err'), parent=self)
            return
        
        stitcher_config = {}
        try:
            stitcher_config["min_score_threshold"] = float(self.score_var.get())
            stitcher_config["initial_pos_weight"] = float(self.pos_weight_var.get())
            
            overlap_h = int(self.overlap_h_var.get())
            overlap_v = int(self.overlap_v_var.get())
            if not (0 < overlap_h <= 100 and 0 < overlap_v <= 100):
                raise ValueError("Overlap must be 1-100")
            stitcher_config["overlap_h_pct"] = overlap_h
            stitcher_config["overlap_v_pct"] = overlap_v

            if self.use_range.get():
                stitcher_config["stitch_range"] = {k: int(v.get()) for k, v in [("r_min", self.r_min_var), ("r_max", self.r_max_var), ("c_min", self.c_min_var), ("c_max", self.c_max_var)]}
            
            stitcher_config["generate_preview"] = self.gen_preview.get()
            stitcher_config["generate_heatmap"] = self.gen_heatmap.get()
            stitcher_config["blend"] = False

            p_path = self.preview_path_var.get()
            if p_path: stitcher_config["preview_path"] = p_path
            h_path = self.heatmap_path_var.get()
            if h_path: stitcher_config["heatmap_path"] = h_path
        except ValueError as e:
            messagebox.showerror(self.t('status_err'), self.t('msg_val_err').format(e), parent=self)
            return

        if AdvancedStitcher is None:
            messagebox.showerror(self.t('status_err'), self.t('msg_mod_err'), parent=self)
            return
        
        try:
            temp_stitcher = AdvancedStitcher(input_dir, output_file, None, stitcher_config)
            temp_stitcher.verify_grid()
        except Exception as e:
            messagebox.showerror(self.t('msg_grid_err'), str(e), parent=self)
            return
        
        try:
            h, w, _ = temp_stitcher.base_image_shape
            est_bytes = temp_stitcher.grid_info['max_r'] * temp_stitcher.grid_info['max_c'] * h * w * 1.5
            _, _, free = shutil.disk_usage(tempfile.gettempdir())
            free_mb = free // 1024 // 1024
            est_mb = int(est_bytes // 1024 // 1024)
            if free < est_bytes:
                 if not messagebox.askyesno("Warning", self.t('msg_disk_warn').format(est_mb, free_mb), parent=self): return
        except Exception: pass
        
        self.run_button.config(state="disabled"); self.progress['value'] = 0; self.pair_label.config(text="")
        self.stitching_process = multiprocessing.Process(target=stitcher_worker_wrapper, args=(input_dir, output_file, self.status_queue, stitcher_config))
        self.stitching_process.start()
        self.check_status()

    def check_status(self):
        try:
            while True:
                message, value = self.status_queue.get_nowait()
                if message == "progress": self.progress['value'] = int(value)
                elif message == "status": self.status_label.config(text=str(value))
                elif message == "progress_pair": self.pair_label.config(text=f"{value}")
                elif message == "done":
                    self.progress['value'] = 100
                    self.status_label.config(text=str(value))
                    messagebox.showinfo(self.t('status_done'), self.t('msg_done_desc').format(value, self.output_path.get()), parent=self)
                    self._reset_ui_after_run()
                    return
                elif message == "error":
                    self.status_label.config(text=self.t('status_err'))
                    messagebox.showerror(self.t('status_err'), str(value), parent=self)
                    self._reset_ui_after_run()
                    return
        except queue.Empty:
            pass
        
        if self.stitching_process and self.stitching_process.is_alive():
            self.after(120, self.check_status)
        elif self.stitching_process:
            self._reset_ui_after_run()

    def _reset_ui_after_run(self):
        self.run_button.config(state="normal")
        self.stitching_process = None

    def on_closing(self):
        if self.stitching_process and self.stitching_process.is_alive():
            if messagebox.askyesno("Confirm", self.t('msg_close_warn'), parent=self):
                self.stitching_process.terminate()
                self.destroy()
        else:
            self.destroy()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk(); root.withdraw()
    app = StitcherApp(master=root, config={"save_folder": os.getcwd(), "language": "ja"})
    app.mainloop()