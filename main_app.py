# main_app.py

# --- 標準ライブラリ ---
import os
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import multiprocessing
import ctypes
import platform # OS判定用

# --- 外部ライブラリ ---
import cv2
cv2.ocl.setUseOpenCL(False)

import pyautogui
import keyboard

import gc
import numpy as np

# --- 自作モジュール ---
import config_manager
from utils import open_folder_in_explorer
from stitcher_app import StitcherApp

# --- 翻訳辞書 ---
TRANSLATIONS = {
    "ja": {
        "tab_main": " 撮影 ",
        "tab_stitch": " 結合 ",
        "step1": "1.準備",
        "save_path": "保存先:",
        "btn_select": "フォルダ選択",
        "btn_open": "開く",
        "browser_hint": "ブラウザ画面を右へ",
        "btn_region": "スクリーンショット範囲指定",
        "step2": "2.設定",
        "lbl_cols": "横枚数(列):",
        "lbl_rows": "縦枚数(行):",
        "lbl_right": "右移動(回):",
        "lbl_down": "下移動(回):",
        "lbl_delay": "間隔(秒):",
        "step3": "3.実行",
        "hint_start": "開始5秒内にブラウザをクリック",
        "btn_start": "▶ 開始",
        "status_wait": "待機中",
        "btn_stop": "■ 停止(ESC)",
        "accordion_show": "▼手動メニュー",
        "accordion_hide": "▲隠す",
        "btn_shot": "撮影 (z)",
        "btn_next": "次の行へ (x)",
        "btn_prev": "前の行へ (c)",
        "btn_reset": "リセット",
        "stitch_desc": "画像結合\nツール",
        "btn_stitch_open": "ツールを開く",
        "msg_reset": "リセットしますか？",
        "msg_reset_done": "リセット済",
        "msg_done": "完了",
        "msg_err": "エラー",
        "status_start": "開始 ",
        "status_check": "動作チェック...",
        "status_move": "行移動...",
    },
    "en": {
        "tab_main": " Shot ",
        "tab_stitch": " Join ",
        "step1": "1.Setup",
        "save_path": "SaveTo:",
        "btn_select": "Folder Sel",
        "btn_open": "Open",
        "browser_hint": "Map on Right!",
        "btn_region": "SS Region",
        "step2": "2.Config",
        "lbl_cols": "Cols(X):",
        "lbl_rows": "Rows(Y):",
        "lbl_right": "Right(→):",
        "lbl_down": "Down(↓):",
        "lbl_delay": "Delay(s):",
        "step3": "3.Run",
        "hint_start": "Click Map in 5s",
        "btn_start": "▶ Run",
        "status_wait": "Ready",
        "btn_stop": "■ Stop(ESC)",
        "accordion_show": "▼Manual",
        "accordion_hide": "▲Hide",
        "btn_shot": "📷 Shot (z)",
        "btn_next": "↓ Next (x)",
        "btn_prev": "↑ Prev (c)",
        "btn_reset": "Reset",
        "stitch_desc": "Stitcher\nTool",
        "btn_stitch_open": "Open Tool",
        "msg_reset": "Reset counters?",
        "msg_reset_done": "Reset Done",
        "msg_done": "Done",
        "msg_err": "Error",
        "status_start": "Start ",
        "status_check": "Chk...",
        "status_move": "NextRow...",
    }
}

class RegionSelector(tk.Toplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.attributes("-fullscreen", True)
        self.attributes("-alpha", 0.3)
        self.attributes("-topmost", True)
        self.overrideredirect(True)

        self.canvas = tk.Canvas(self, cursor="cross", bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.rect: self.canvas.delete(self.rect)

    def on_mouse_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        if self.rect: self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y, outline='red', width=5)

    def on_button_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        x, y = min(self.start_x, end_x), min(self.start_y, end_y)
        w, h = abs(end_x - self.start_x), abs(end_y - self.start_y)
        if w > 10 and h > 10:
            self.config['region'] = [int(x), int(y), int(w), int(h)]
        self.destroy()

class Application(ttk.Frame):
    def __init__(self, master, config):
        super().__init__(master)
        self.master = master
        self.config = config
        
        # --- 言語設定の読み込み (デフォルトはja) ---
        self.lang_code = self.config.get('language', 'ja')
        
        self.shot_col_count = 1
        self.automation_running = False
        self.is_manual_open = False

        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        self.setup_hotkeys()
        self.update_labels()

    def get_ui_font_family(self):
        """OSに応じた標準UIフォント名を返す"""
        sys_name = platform.system()
        if sys_name == "Windows":
            return "Segoe UI"
        elif sys_name == "Darwin": # macOS
            return "System" # または ".AppleSystemUIFont"
        elif sys_name == "Linux":
            return "DejaVu Sans" # 環境によるが一般的
        else:
            return "TkDefaultFont"

    def t(self, key):
        """現在の言語設定に基づいて翻訳テキストを返す"""
        return TRANSLATIONS.get(self.lang_code, TRANSLATIONS["ja"]).get(key, key)

    def toggle_language(self):
        """言語を切り替えてUIを再描画"""
        self.lang_code = 'en' if self.lang_code == 'ja' else 'ja'
        self.config['language'] = self.lang_code
        
        # ウィジェットをすべて破棄して作り直す
        for widget in self.winfo_children():
            widget.destroy()
            
        self.setup_styles() # フォント再適用のため念のため
        self.create_widgets()
        self.update_labels()

    def setup_window(self):
        self.master.title("AutoMap")
        geometry = self.config.get('window_geometry', "205x800+0+0")
        self.master.geometry(geometry)
        self.master.attributes("-topmost", True)

        # ★★★ 追加: 横幅(width)を固定、縦幅(height)は変更可能にする ★★★
        # これにより、横に引き伸ばすスナップ機能が無効化されます
        self.master.resizable(width=False, height=False)

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.pack(padx=0, pady=0, fill=tk.BOTH, expand=True)
    
    def setup_styles(self):
        style = ttk.Style()
        
        # OS標準フォントを取得
        ui_font_family = self.get_ui_font_family()
        
        base_font = (ui_font_family, 9)
        bold_font = (ui_font_family, 9, "bold")
        small_font = (ui_font_family, 8)
        tiny_font = (ui_font_family, 7)

        # 全体のデフォルトフォント設定
        self.master.option_add('*font', base_font)

        style.configure("TNotebook", tabposition='n')
        style.configure("TNotebook.Tab", font=base_font, padding=[5, 2])
        style.map("TNotebook.Tab",
            foreground=[("selected", "blue"), ("!selected", "black")]
        )

        style.configure("Highlight.TButton", font=bold_font, background="#cceeff")
        style.configure("Step.TLabelframe", relief="groove", borderwidth=1)
        style.configure("Step.TLabelframe.Label", font=bold_font, foreground="#333333")
        style.configure("Accordion.TButton", font=small_font, foreground="#555555")
        
        # 各種ウィジェットのフォント適用
        style.configure("TLabel", font=base_font)
        style.configure("TButton", font=base_font)
        style.configure("TEntry", font=base_font)
        
        # 小さいラベル用のスタイル定義
        style.configure("Tiny.TLabel", font=tiny_font)
        style.configure("Small.TLabel", font=small_font)

    def create_widgets(self):
        # --- 言語切替ボタン (最上部) ---
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", pady=(2, 0), padx=2)
        lang_text = "English" if self.lang_code == 'ja' else "日本語"
        ttk.Button(top_frame, text=f"🌐 {lang_text}", command=self.toggle_language, style="Accordion.TButton").pack(anchor="e")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        self.create_main_tab()
        self.create_stitcher_tab()

    def create_main_tab(self):
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text=self.t('tab_main'))

        # --- スクロール設定 ---
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        def _on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)
        
        canvas.bind("<Configure>", _on_canvas_configure)
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # === コンテンツ配置 ===
        
        # --- Step 1 ---
        step1_frame = ttk.LabelFrame(scrollable_frame, text=self.t('step1'), style="Step.TLabelframe", padding=2)
        step1_frame.pack(fill="x", pady=2, padx=2)

        ttk.Label(step1_frame, text=self.t('save_path')).pack(anchor="w")
        btn_f = ttk.Frame(step1_frame)
        btn_f.pack(fill="x")
        ttk.Button(btn_f, text=self.t('btn_select'), command=self.select_save_folder).pack(side="left", fill="x", expand=True)
        ttk.Button(btn_f, text=self.t('btn_open'), width=5, command=self.open_save_folder).pack(side="right", padx=(2,0))
        
        self.path_label = ttk.Label(step1_frame, text="", foreground="gray", style="Tiny.TLabel", wraplength=130)
        self.path_label.pack(anchor="w", pady=(0, 2))
        
        ttk.Separator(step1_frame, orient="horizontal").pack(fill="x", pady=2)
        ttk.Label(step1_frame, text=self.t('browser_hint'), foreground="#555555", style="Small.TLabel").pack(anchor="w")
        ttk.Button(step1_frame, text=self.t('btn_region'), command=self.open_region_selector).pack(fill="x", pady=2)
        self.region_label = ttk.Label(step1_frame, text="", foreground="blue", style="Tiny.TLabel", wraplength=130)
        self.region_label.pack(anchor="w")

        # --- Step 2 ---
        step2_frame = ttk.LabelFrame(scrollable_frame, text=self.t('step2'), style="Step.TLabelframe", padding=2)
        step2_frame.pack(fill="x", pady=2, padx=2)

        def add_mini_input(parent, txt, var):
            f = ttk.Frame(parent)
            f.pack(fill="x", pady=1)
            ttk.Label(f, text=txt, style="Small.TLabel").pack(anchor="w")
            ttk.Entry(f, textvariable=var).pack(fill="x")

        self.auto_cols_var = tk.StringVar(value=self.config.get('auto_cols', 10))
        add_mini_input(step2_frame, self.t('lbl_cols'), self.auto_cols_var)

        self.auto_rows_var = tk.StringVar(value=self.config.get('auto_rows', 10))
        add_mini_input(step2_frame, self.t('lbl_rows'), self.auto_rows_var)

        ttk.Separator(step2_frame, orient="horizontal").pack(fill="x", pady=3)

        self.key_right_var = tk.StringVar(value=self.config.get('key_right_presses', 5))
        add_mini_input(step2_frame, self.t('lbl_right'), self.key_right_var)

        self.key_down_var = tk.StringVar(value=self.config.get('key_down_presses', 5))
        add_mini_input(step2_frame, self.t('lbl_down'), self.key_down_var)

        self.auto_delay_var = tk.StringVar(value=self.config.get('auto_delay', 1.5))
        add_mini_input(step2_frame, self.t('lbl_delay'), self.auto_delay_var)

        # --- Step 3 ---
        step3_frame = ttk.LabelFrame(scrollable_frame, text=self.t('step3'), style="Step.TLabelframe", padding=2)
        step3_frame.pack(fill="x", pady=2, padx=2)

        ttk.Label(step3_frame, text=self.t('hint_start'), foreground="red", style="Tiny.TLabel", wraplength=130).pack(pady=(0, 2))
        
        self.auto_run_button = ttk.Button(step3_frame, text=self.t('btn_start'), command=self.start_automation, style="Highlight.TButton")
        self.auto_run_button.pack(fill="x", ipady=5)

        self.auto_status_label = ttk.Label(step3_frame, text=self.t('status_wait'), font=("", 9, "bold"), foreground="blue", wraplength=130)
        self.auto_status_label.pack(pady=2)

        self.auto_stop_button = ttk.Button(step3_frame, text=self.t('btn_stop'), command=self.stop_automation, state="disabled")
        self.auto_stop_button.pack(fill="x")

        # --- アコーディオン ---
        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=5)
        
        self.toggle_btn = ttk.Button(scrollable_frame, text=self.t('accordion_show'), style="Accordion.TButton", command=self.toggle_manual_controls)
        self.toggle_btn.pack(fill="x")

        self.manual_frame = ttk.Frame(scrollable_frame, padding=2, relief="sunken", borderwidth=1)
        
        ttk.Button(self.manual_frame, text=self.t('btn_shot'), command=self.take_screenshot).pack(fill="x", pady=1)
        ttk.Button(self.manual_frame, text=self.t('btn_next'), command=self.go_to_next_row).pack(fill="x", pady=1)
        ttk.Button(self.manual_frame, text=self.t('btn_prev'), command=self.go_to_previous_row).pack(fill="x", pady=1)
        ttk.Button(self.manual_frame, text=self.t('btn_reset'), command=self.reset_counters).pack(fill="x", pady=3)

    def create_stitcher_tab(self):
        stitcher_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(stitcher_frame, text=self.t('tab_stitch'))
        
        lbl = ttk.Label(stitcher_frame, text=self.t('stitch_desc'), justify="center")
        lbl.pack(pady=20)
        
        ttk.Button(stitcher_frame, text=self.t('btn_stitch_open'), command=self.open_stitcher_window, style="Highlight.TButton").pack(expand=True, fill="x", ipady=10, padx=5, anchor="n")

    def toggle_manual_controls(self):
        if self.is_manual_open:
            self.manual_frame.pack_forget()
            self.toggle_btn.config(text=self.t('accordion_show'))
            self.is_manual_open = False
        else:
            self.manual_frame.pack(fill="x", pady=2)
            self.toggle_btn.config(text=self.t('accordion_hide'))
            self.is_manual_open = True
            self.master.after(100, lambda: self.manual_frame.master.master.yview_moveto(1.0))

    def setup_hotkeys(self):
        try:
            keyboard.add_hotkey('esc', self.stop_automation)
        except: pass

    def update_labels(self):
        r = self.config['region']
        path = self.config['save_folder']
        short_path = "..." + path[-10:] if len(path) > 10 else path
        self.path_label.config(text=short_path)
        self.region_label.config(text=f"{r[2]}x{r[3]} (x{r[0]},y{r[1]})")

    def open_stitcher_window(self):
        StitcherApp(self, config=self.config)

    def open_save_folder(self):
        open_folder_in_explorer(self.config['save_folder'])

    def open_region_selector(self):
        self.master.withdraw()
        selector = RegionSelector(self, config=self.config)
        self.master.wait_window(selector)
        self.update_labels()
        self.master.deiconify()
        self.master.attributes("-topmost", True)

    def select_save_folder(self):
        folder = filedialog.askdirectory(initialdir=self.config['save_folder'])
        if folder:
            self.config['save_folder'] = folder
            self.update_labels()

    def go_to_next_row(self):
        self.config['current_row'] += 1
        self.shot_col_count = 1
        self.auto_status_label.config(text=f"Now: R{self.config['current_row']}")

    def go_to_previous_row(self):
        if self.config['current_row'] > 1:
            self.config['current_row'] -= 1
            self.shot_col_count = 1
            self.auto_status_label.config(text=f"Now: R{self.config['current_row']}")
            
    def reset_counters(self):
        if messagebox.askyesno("Confirm", self.t('msg_reset')):
            self.config['current_row'] = 1
            self.shot_col_count = 1
            self.auto_status_label.config(text=self.t('msg_reset_done'))

    def take_screenshot(self, is_auto=False, row=0, col=0):
        try:
            os.makedirs(self.config['save_folder'], exist_ok=True)
            r, c = (row, col) if is_auto else (self.config['current_row'], self.shot_col_count)
            filename = os.path.join(self.config['save_folder'], f"R{r:02d}_C{c:02d}.png")
            
            if not is_auto:
                self.master.withdraw()
                self.master.after(200, lambda: self.capture_and_show(filename, is_auto))
                return True
            else:
                return self.capture_and_show(filename, is_auto)
        except Exception as e:
            if not is_auto: messagebox.showerror(self.t('msg_err'), str(e))
            return False

    def capture_and_show(self, filename, is_auto, retry_count=0):
        try:
            screenshot = pyautogui.screenshot(region=tuple(self.config['region']))

            if is_auto:
                img_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                mean_color = cv2.mean(img_cv)[:3]
                if all(c > 250 for c in mean_color) or all(120 < c < 140 for c in mean_color):
                    if retry_count < 3:
                        print(f"Retry {retry_count}...")
                        time.sleep(2.0)
                        return self.capture_and_show(filename, is_auto, retry_count + 1)

            screenshot.save(filename, dpi=(self.config['dpi'], self.config['dpi']), compress_level=self.config['png_compress_level'])
            print(f"Saved: {os.path.basename(filename)}")
            if not is_auto:
                self.shot_col_count += 1
                messagebox.showinfo(self.t('msg_done'), "OK")
            return True 
        except Exception as e:
            print(f"Err: {e}")
            return False 
        finally:
            if not is_auto and self.master.state() == 'withdrawn':
                self.master.deiconify()

    def start_automation(self):
        if self.automation_running: return
        try:
            cols = int(self.auto_cols_var.get())
            rows = int(self.auto_rows_var.get())
            delay = float(self.auto_delay_var.get())
            key_right = int(self.key_right_var.get())
            key_down = int(self.key_down_var.get())
            if any(x < 0 for x in [cols, rows, delay, key_right, key_down]): raise ValueError
            self.config.update({'auto_cols': cols, 'auto_rows': rows, 'auto_delay': delay, 'key_right_presses': key_right, 'key_down_presses': key_down})
        except ValueError:
            messagebox.showerror("Err", "Value Error"); return
        
        self.automation_running = True
        self.auto_run_button.config(state="disabled")
        self.auto_stop_button.config(state="normal")
        threading.Thread(target=self.automation_thread, daemon=True).start()

    def stop_automation(self):
        if self.automation_running:
            self.automation_running = False
            self._update_status_label("Stopping...")

    def _update_status_label(self, text):
        self.master.after(0, lambda: self.auto_status_label.config(text=text))

    def automation_thread(self):
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        is_sleep_prevented = False
        final_status = self.t('status_wait')

        try:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
            is_sleep_prevented = True
            
            cfg = self.config
            cols, rows = cfg['auto_cols'], cfg['auto_rows']
            delay = cfg['auto_delay']
            key_right, key_down = cfg['key_right_presses'], cfg['key_down_presses']
            KEY_INTERVAL = 0.5
            
            for i in range(5, 0, -1):
                if not self.automation_running: raise InterruptedError
                self._update_status_label(f"{self.t('status_start')} {i}s...")
                time.sleep(1)

            self._update_status_label(self.t('status_check'))
            for key, presses in [('right', key_right), ('left', key_right)]:
                if not self.automation_running: raise InterruptedError
                pyautogui.press(key, presses=presses, interval=KEY_INTERVAL)
                time.sleep(0.5)
            time.sleep(1.0)

            total = rows * cols
            cur = 0
            
            for r in range(1, rows + 1):
                for c_step in range(cols):
                    if not self.automation_running: raise InterruptedError
                    time.sleep(0.3)
                    c = c_step + 1 if r % 2 == 1 else cols - c_step
                    cur += 1
                    self._update_status_label(f"R{r}-C{c} ({cur}/{total})")
                    
                    if not self.take_screenshot(is_auto=True, row=r, col=c):
                        raise RuntimeError("Shot Err")

                    time.sleep(delay)

                    if c_step < cols - 1:
                        k = 'right' if r % 2 == 1 else 'left'
                        pyautogui.press(k, presses=key_right, interval=KEY_INTERVAL)
                        time.sleep(0.5)

                if r < rows:
                    if not self.automation_running: raise InterruptedError
                    self._update_status_label(self.t('status_move'))
                    pyautogui.press('down', presses=key_down, interval=KEY_INTERVAL)
                    time.sleep(1.0)
                    if r % 5 == 0: gc.collect()
            
            final_status = self.t('msg_done')
            messagebox.showinfo(self.t('msg_done'), "OK")
        
        except InterruptedError:
            final_status = "Stop"
        except Exception as e:
            final_status = "Err"
            print(e)
        finally:
            if is_sleep_prevented:
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            self.automation_running = False
            self.master.after(0, self._finalize_automation_ui, final_status)

    def _finalize_automation_ui(self, status_text):
        self.auto_status_label.config(text=status_text)
        self.auto_run_button.config(state="normal")
        self.auto_stop_button.config(state="disabled")

    def on_closing(self):
        self.stop_automation()
        try: keyboard.unhook_all()
        except: pass
        try:
            x = y +
            self.config['window_geometry'] = self.master.geometry()
            config_manager.save_config(self.config)
        except: pass
        self.master.destroy()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    config = config_manager.load_config()
    root = tk.Tk()
    app = Application(master=root, config=config)

    app.mainloop()
