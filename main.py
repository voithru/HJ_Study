import tkinter as tk
import sys
from pathlib import Path
from application import Application
import ttkbootstrap as tb  # ttkbootstrap 追加

def setup_environment():
    if getattr(sys, "frozen", False):
        # PyInstallerでビルドされた実行ファイルの場合
        application_path = Path(sys._MEIPASS)
    else:
        # スクリプトとして実行される場合
        application_path = Path(__file__).parent

    # アプリケーションパスをシステムパスに追加
    sys.path.append(str(application_path))

def main():
    setup_environment()

    # デフォルトテーマを設定
    theme = "litera"
    root = tb.Window(themename=theme)  # ttkbootstrap テーマ適用
    app = Application(master=root)
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()