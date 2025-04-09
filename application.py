import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from settings_manager import SettingsManager
from error_settings_window import ErrorSettingsWindow
from srt_processor import process_folder, fix_srt_format, check_srt_format
import subprocess
import platform
import pyperclip
import webbrowser
import ttkbootstrap as tb  # ttkbootstrap 追加

class Application(tb.Frame):  # tb.Frameに変更
    LANGUAGE_ORDER = ["KOR", "ENG", "JPN", "CHN", "SPA", "VIE", "IND", "THA"]

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("SRT Checker")
        self.pack(fill=tk.BOTH, expand=True)
        self.results = None
        self.folder_path = None

        self.settings_manager = SettingsManager("srt_checker_settings.json")
        self.settings = self.settings_manager.get_settings()

        self.create_widgets()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.create_button_frame()
        self.create_stats_frame()
        self.create_results_tree()

    def create_button_frame(self):
        button_frame = ttk.Frame(self)
        button_frame.grid(row=0, column=0, pady=(10, 5), padx=10, sticky="ew")

        buttons = [
            ("フォルダ選択", self.select_folder),
            ("エラー設定", self.open_settings),
            ("結果保存", self.save_results_to_file),
            ("フォルダ再検査", self.recheck_folder),
            ("形式修正", self.fix_format),
            ("srt形式チェック", self.check_srt_format),
        ]

        for text, command in buttons:
            button = tb.Button(button_frame, text=text, command=command, bootstyle="primary")
            button.pack(side=tk.LEFT, padx=(0, 5))

        self.save_results_button = button_frame.winfo_children()[-4]
        self.recheck_button = button_frame.winfo_children()[-3]
        self.fix_format_button = button_frame.winfo_children()[-2]
        self.check_format_button = button_frame.winfo_children()[-1]
        
        self.save_results_button.config(state=tk.DISABLED)
        self.recheck_button.config(state=tk.DISABLED)
        self.fix_format_button.config(state=tk.DISABLED)
        self.check_format_button.config(state=tk.DISABLED)

        # 画面説明書ボタン追加
        help_button = tb.Button(button_frame, text="画面説明書", command=self.open_help_url, bootstyle="info")
        help_button.pack(side=tk.RIGHT, padx=(5, 0))

    def open_help_url(self):
        webbrowser.open("https://www.figma.com/board/VLNNmvCkn7N7bbczbjnzPA/subtitle_cheker?node-id=0-1&t=ptPGO00fcSiR6XdR-1")  # 希望するURLに変更

    def create_stats_frame(self):
        self.stats_frame = ttk.Frame(self)
        self.stats_frame.grid(row=1, column=0, pady=(0, 5), padx=10, sticky="ew")

        self.stats_toggle = tb.Button(
            self.stats_frame, text="統計表示", command=self.toggle_stats, bootstyle="secondary"
        )
        self.stats_toggle.pack(side=tk.LEFT, padx=(0, 5))
        self.stats_toggle.config(state=tk.DISABLED)

        self.stats_content = ttk.Frame(self.stats_frame)
        self.stats_content.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.stats_content.pack_forget()

    def toggle_stats(self):
        if self.stats_content.winfo_manager():
            self.stats_content.pack_forget()
            self.stats_toggle.config(text="統計表示")
        else:
            self.stats_content.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.stats_toggle.config(text="統計非表示")
            self.update_stats()

    def update_stats(self):
        for widget in self.stats_content.winfo_children():
            widget.destroy()

        if not self.results:
            ttk.Label(self.stats_content, text="結果がありません。").pack()
            return

        # 全体エラー数を表示するフレーム
        total_frame = ttk.Frame(self.stats_content)
        total_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)

        ttk.Label(total_frame, text="Total", font=("TkDefaultFont", 12, "bold")).pack(
            anchor=tk.W
        )

        total_errors = sum(len(errors) for errors in self.results.values())
        ttk.Label(
            total_frame, text=str(total_errors), font=("TkDefaultFont", 24, "bold")
        ).pack(anchor=tk.W, pady=(5, 0))

        for lang in self.LANGUAGE_ORDER:
            if lang in self.results:
                errors = self.results[lang]
                lang_frame = ttk.LabelFrame(self.stats_content, text=lang)
                lang_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)

                error_counts = {}
                lang_total = 0
                for error in errors:
                    if isinstance(error, dict):
                        error_type = error["ErrorType"]
                        error_counts[error_type] = error_counts.get(error_type, 0) + 1
                        lang_total += 1
                    elif isinstance(error, tuple):
                        error_counts["PARSE_ERROR"] = (
                            error_counts.get("PARSE_ERROR", 0) + 1
                        )
                        lang_total += 1

                # 言語ごとの全体エラー数を大きく表示
                ttk.Label(
                    lang_frame, text=str(lang_total), font=("TkDefaultFont", 18, "bold")
                ).pack(anchor=tk.W, pady=(0, 5))

                for error_type, count in error_counts.items():
                    ttk.Label(lang_frame, text=f"{error_type}: {count}").pack(
                        anchor=tk.W
                    )

        # 統計をすぐに表示
        self.stats_content.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.stats_toggle.config(text="統計非表示")

    def create_results_tree(self):
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        columns = ("File", "StartTC", "ErrorType", "ErrorContent", "SubtitleText", "Severity")
        self.results_tree = ttk.Treeview(
            tree_frame, columns=columns, show="tree headings"
        )

        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150, anchor=tk.W)

        self.results_tree.grid(row=0, column=0, sticky="nsew")

        y_scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.results_tree.yview
        )
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        x_scrollbar = ttk.Scrollbar(
            tree_frame, orient="horizontal", command=self.results_tree.xview
        )
        x_scrollbar.grid(row=1, column=0, sticky="ew")

        self.results_tree.configure(
            yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set
        )
        self.results_tree.bind("<Double-1>", self.on_double_click)

    def save_settings(self):
        try:
            self.settings_manager.update_settings(self.settings)
        except Exception as e:
            messagebox.showerror("エラー", f"設定保存中にエラーが発生しました: {str(e)}")

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            self.process_folder()
            self.check_format_button.config(state=tk.NORMAL)

    def process_folder(self):
        if self.folder_path:
            self.results = process_folder(self.folder_path, self.settings)
            self.display_results(self.results)
            self.update_stats()
            self.save_results_button.config(state=tk.NORMAL)
            self.recheck_button.config(state=tk.NORMAL)
            self.fix_format_button.config(state=tk.NORMAL)
            self.stats_toggle.config(state=tk.NORMAL)
            self.stats_content.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.stats_toggle.config(text="統計非表示")

    def recheck_folder(self):
        if self.folder_path:
            self.process_folder()
        else:
            messagebox.showerror("エラー", "再検査するフォルダが選択されていません。")

    def open_settings(self):
        ErrorSettingsWindow(self, self.settings)

    def display_results(self, results):
        self.results_tree.delete(*self.results_tree.get_children())
        for lang in self.LANGUAGE_ORDER:
            if lang in results:
                lang_node = self.results_tree.insert("", "end", text=lang)
                for error in results[lang]:
                    self.insert_error(lang_node, error)

    def insert_error(self, parent, error):
        if isinstance(error, dict):
            values = (
                error["File"],
                error["StartTC"],
                error["ErrorType"],
                error["ErrorContent"],
                error["SubtitleText"].replace("\n", " "),
                error.get("Severity", "Error")  # Default to 'Error' if not specified
            )
            self.results_tree.insert(
                parent, "end", values=values, tags=(error["SubtitleText"],)
            )
        elif isinstance(error, tuple):
            self.results_tree.insert(
                parent, "end", values=(error[0], "", "PARSE_ERROR", error[1], "", "Error")
            )

    def on_double_click(self, event):
        item = self.results_tree.selection()[0]
        values = self.results_tree.item(item, "values")

        # 値がない場合（言語項目など）無視
        if not values:
            return

        column = self.results_tree.identify_column(event.x)

        actions = {
            "#1": lambda: self.open_file(values[0]),
            "#2": lambda: self.copy_start_tc_and_open_file(values[1], values[0]),
            "#5": lambda: self.show_full_text(self.results_tree.item(item, "tags")[0]),
        }

        action = actions.get(column)
        if action:
            action()

    def copy_start_tc_and_open_file(self, start_tc, file_name):
        pyperclip.copy(start_tc)
        self.open_file(file_name)

    def show_full_text(self, text):
        popup = tk.Toplevel(self)
        popup.title("字幕テキスト全体")
        popup.geometry("400x300")

        text_widget = tk.Text(popup, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget.config(yscrollcommand=scrollbar.set)
        text_widget.insert(tk.END, text)
        text_widget.config(state=tk.DISABLED)

    def open_file(self, file_name):
        if not self.folder_path:
            messagebox.showerror("エラー", f"ファイルが見つかりません: {full_path}")
            return

        full_path = os.path.join(self.folder_path, file_name)
        if not os.path.exists(full_path):
            messagebox.showerror("エラー", f"ファイルが見つかりません: {full_path}")
            return

        if platform.system() == "Darwin":
            subprocess.call(("open", full_path))
        elif platform.system() == "Windows":
            os.startfile(full_path)
        else:  # linux
            subprocess.call(("xdg-open", full_path))

    def save_results_to_file(self):
        if not self.results:
            messagebox.showinfo("通知", "保存する結果がありません。")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for lang in self.LANGUAGE_ORDER:
                    if lang in self.results:
                        f.write(f"Language: {lang}\n")
                        f.write("-" * 50 + "\n")
                        for error in self.results[lang]:
                            if isinstance(error, dict):
                                for key, value in error.items():
                                    f.write(f"{key}: {value}\n")
                            elif isinstance(error, tuple):
                                f.write(f"File: {error[0]}\n")
                                f.write(f"Error: PARSE_ERROR\n")
                                f.write(f"Details: {error[1]}\n")
                            f.write("-" * 50 + "\n")
            messagebox.showinfo("通知", f"結果が{file_path}に保存されました。")
        except Exception as e:
            messagebox.showerror("エラー", f"結果保存中にエラーが発生しました: {str(e)}")

    def on_closing(self):
        self.master.destroy()

    def fix_format(self):
        if not self.folder_path:
            messagebox.showerror("エラー", "フォルダが選択されていません。")
            return
        
        try:
            files_modified, tc_modified, text_space_modified, blank_lines_removed = fix_srt_format(self.folder_path)
            result_message = (
                f"合計{files_modified}個のファイルが修正されました。\n\n"
                f"- TC空白修正: {tc_modified}個\n"
                f"- テキスト前後の空白修正: {text_space_modified}行\n"
                f"- テキスト間の空行削除: {blank_lines_removed}行\n"
            )
            messagebox.showinfo("完了", result_message)
        except Exception as e:
            messagebox.showerror("エラー", f"形式修正中にエラーが発生しました: {str(e)}")

    def check_srt_format(self):
        if not self.folder_path:
            messagebox.showerror("エラー", "フォルダが選択されていません。")
            return
        
        try:
            format_errors = check_srt_format(self.folder_path)
            if format_errors:
                # 結果ツリービュー初期化
                self.results_tree.delete(*self.results_tree.get_children())
                
                # 'FORMAT'ノード作成
                format_node = self.results_tree.insert("", "end", text="FORMAT")
                
                # 各エラーをツリービューに追加
                for error in format_errors:
                    values = (
                        error["File"],
                        error["StartTC"],
                        error["ErrorType"],
                        error["ErrorContent"],
                        ""  # SubtitleTextは空欄
                    )
                    self.results_tree.insert(format_node, "end", values=values)
                
                messagebox.showinfo("完了", f"合計{len(format_errors)}個の形式エラーが見つかりました。")
            else:
                messagebox.showinfo("完了", "形式エラーが見つかりませんでした。一般エラーを検査します。")
                # 形式エラーがない場合、自動的にフォルダ再検査を実行
                self.process_folder()
                
        except Exception as e:
            messagebox.showerror("エラー", f"形式チェック中にエラーが発生しました: {str(e)}")