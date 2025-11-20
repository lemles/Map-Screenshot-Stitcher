# utils.py
import os
import sys
import subprocess
from tkinter import messagebox

def open_folder_in_explorer(path):
    """指定されたパスをOSのファイルエクスプローラーで開く"""
    if not os.path.isdir(path):
        messagebox.showwarning("フォルダが見つかりません", f"パスが存在しません:\n{path}")
        return
    try:
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.call(['open', path])
        else:  # Linux
            subprocess.call(['xdg-open', path])
    except Exception as e:

        messagebox.showerror("エラー", f"フォルダを開けませんでした。\n{e}")



import subprocess
import pickle

def security_test_function(user_input):
    # Bandit should detect this as a high-risk issue (shell=True)
    subprocess.run(f"echo {user_input}", shell=True) 

    # Bandit should detect this as a medium-risk issue (insecure pickle usage)
    pickle.loads(b"\x80\x03}q\x00.")
