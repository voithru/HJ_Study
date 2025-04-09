import tkinter as tk
from tkinter import ttk, messagebox
import platform
import ttkbootstrap as tb  # ttkbootstrap 追加


class ErrorSettingsWindow(tb.Toplevel):  # tb.Toplevelに変更
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.parent = parent
        self.settings = settings
        self.title("エラー設定")
        self.geometry("1200x600")  # ウィンドウサイズを広げて説明を表示するスペースを確保
        self.create_widgets()
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.scroll_speed = 2  # スクロール速度調整定数

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 固定ヘッダーフレーム作成
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X)

        # カラムタイトル追加
        ttk.Label(header_frame, text="エラー項目", font=("TkDefaultFont", 14, "bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ttk.Label(header_frame, text="説明と例", font=("TkDefaultFont", 14, "bold")).grid(row=0, column=1, padx=10, pady=5, sticky="w")
        ttk.Label(header_frame, text="特記事項", font=("TkDefaultFont", 14, "bold")).grid(row=0, column=2, padx=10, pady=5, sticky="w")

        # カラム幅設定
        header_frame.columnconfigure(0, weight=1, minsize=180)
        header_frame.columnconfigure(1, weight=1, minsize=300)
        header_frame.columnconfigure(2, weight=1, minsize=200)

        # スクロール可能領域作成
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(content_frame, highlightthickness=0)
        scrollbar = tb.Scrollbar(
            content_frame, orient="vertical", command=self.canvas.yview, bootstyle="round"
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # マウスホイールイベントバインディング
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", self._on_mousewheel)
        self.bind_all("<Button-5>", self._on_mousewheel)

        self.lang_vars = {}

        error_descriptions = {
            "行ごとの文字数": ("各行が最大文字数を超えているかチェックします。", "これはとても長い長い長い長い長い長い長い長い文章です。"),
            "行数": ("各字幕が許容された最大行数を超えているかチェックします。", "一行目\n二行目\n三行目\n四行目"),
            "@@@有無": ("各行に '@@@' または '＠＠＠'が含まれているかチェックします。", "これは @@@ 不明確な発話表記です。"),
            "中間省略記号": ("各行に '⋯'があるかチェックします。", "これは⋯ 中間省略記号です。"),
            "ピリオド省略記号": ("各行に '...'があるかチェックします。", "これは... ピリオド省略記号です。"),
            "ピリオド2,4個": ("各行に '..' または '....'があるかチェックします。", "これは.. ピリオド2,4個 です...."),
            "行末ピリオド": ("各行の末尾に'.'があるかチェックします。", "これはピリオドです。"),
            "ハイフン後スペースあり": ("各行にハイフンの後にスペースがあるかチェックします。", "- これはスペースありです。"),
            "ハイフン後スペースなし": ("各行にハイフンの後にスペースがないかチェックします。", "-これはスペースなしです。"),
            "不要なスペース": ("各行の二重スペース: '  '\n各行の先頭、末尾: ' '\n小括弧、中括弧、大括弧内側のスペース: '[{( ' または ' )}]'", "[ これはスペースです。 )"),
            "通常波線": ("各行に '~'があるかチェックします。", "これは ~ 波線です。"),
            "音符記号": ("各行に '♪'がある場合、2つあるかチェックします。\n音符の内側にスペースがあるかチェックします。", "♪これは音符です♪"),
            "ぼかし記号": ("各行に '○'があるかチェックします。", "これは ○です。"),
            "全角数字": ("各行に全角数字があるかチェックします。", "これは １２３ 全角数字です。"),
            "画面字幕位置": ("各字幕に大括弧内のテキストが一般テキストより下にあるかチェックします。\n各字幕に大括弧がペアで存在するかチェックします。", "[画面字幕]\nこれはテストです。"),
            "中国語引用符使用": ("各行の中国語引用符使用をチェックします。", "\"これは二重引用符です。\"\n'これは単一引用符です。'"),
            "括弧使用": ("各行の小括弧と大括弧が正しく全角/半角で使用されているかチェックします。", "() : 半角小括弧、（） : 全角小括弧\n[] : 半角大括弧、［］ : 全角大括弧"),
            "疑問符/感嘆符使用": ("各行の疑問符と感嘆符が\n単独使用時全角\n重複使用時半角かチェックします。", "単独使用半角疑問符?\n二重使用全角記号！？"),
            "KOR使用": ("各行にKOR言語が使用されているかチェックします。", "This is a 韓国語 テキスト"),
            "特殊アスキー文字": ("各行に<0x08>と<0xa0>アスキーコード記号が使用されているかチェックします。", "これは<0x08>記号です。\nこれは<0xa0>記号です。"),
            "ハイフン1個": ("各字幕にハイフン(-)が一つだけあるかチェックします。", "- これはハイフンです\nこれは一般文です。"),
            "大括弧内容エラー": ("各行の大括弧内に数字や特殊記号だけがあるかチェックします。", "[?]\n[これは画面字幕です]"),
            "行末ピリオド欠落": ("各字幕の最後の行に文末記号がないかチェックします。", "これはピリオドがない文\nこれはピリオドがある文。"),
            "最後の行カンマ": ("各字幕の最後の行がコンマで終わるかチェックします。", "一行目\n二行目,"),
            "日本語句読点": ("日本語字幕でのピリオド(.)とコンマ(,)の使用をチェックします。", "これは間違った例です. (X)\nこれは正しい例です。(O)"),
            "持続時間エラー": ("各字幕の持続時間が最小1秒、最大8秒を超えるかチェックします。", "1秒未満または8秒超過字幕"),
            "エンコードエラー": ("字幕テキストでエンコーディングが崩れた痕跡があるかチェックします。", "これは â€™â€ エンコーディングが崩れたテキストです。"),
            "文末ハイフン/アンダーバー": ("各行の末尾に短い半角ハイフン(-)やアンダーバー(_)があるかチェックします。", "これは不完全な文です-\nこれは不完全な文です_"),
        }

        error_notes = {
            "行ごとの文字数": "KOR: 20, ENG: 42, JPN: 16, CHN: 20\nSPA: 42, VIE: 42, IND: 55, THA: 42\n\nJPN、CHNの場合、英数字とスペースは0.5文字扱い",
            "行数": "3行まで正常、4行以上エラー",
            "@@@有無": "聞き取りにくい部分の特殊記号検索",
            "中間省略記号": "ピリオドではない特殊文字",
            "ピリオド省略記号": "ピリオド(.)正確に3つ",
            "ピリオド2,4個": "ピリオド(.)正確に2つまたは4つ",
            "行末ピリオド": "JPN、CHN：'。'と'.'両方含む",
            "ハイフン後スペースあり": "ハイフンの後にスペースがあってはならない言語対象",
            "ハイフン後スペースなし": "ハイフンの後にスペースがあるべき言語対象",
            "不要なスペース": "",
            "通常波線": "通常波線の代わりにチルダ(～)を使用する言語対象（日本語）",
            "音符記号": "",
            "ぼかし記号": "エラーチェック目的ではなく、ぼかし記号確認",
            "全角数字": "",
            "画面字幕位置": "大括弧表記テキストが一般テキストより下にあるべき作業対象",
            "中国語引用符使用": "",
            "括弧使用": "JPN：小括弧全角、大括弧半角\nCHN：小括弧半角、大括弧半角\nそれ以外の言語は動作しません",
            "疑問符/感嘆符使用": "小括弧、大括弧との併用は検査しません。\n疑問符と感嘆符の重複使用のみチェックします。",
            "KOR使用": "韓国語を除く言語対象",
            "特殊アスキー文字": "アスキーコード<0x08>、<0xa0>使用の有無",
            "ハイフン1個": "ハイフンが2つ以上ある場合、エラー出力しません。",
            "大括弧内容エラー": "",
            "行末ピリオド欠落": "JPN、CHN：'。'と'.'両方含む\n大括弧テキスト、音符間テキスト、ハイフン台詞は除外",
            "最後の行カンマ": "字幕の最後の行はコンマで終わってはいけません",
            "日本語句読点": "日本語ではピリオド(.)の代わりに。を、コンマ(,)の代わりに、を使用する必要があります",
            "持続時間エラー": "最小持続時間：1秒\n最大持続時間：8秒",
            "エンコードエラー": "UTF-8がCP949や他のエンコーディングで誤って解釈された場合など\n特殊文字の崩れ、異常なユニコード文字などを検出します",
            "文末ハイフン/アンダーバー": "文がハイフンやアンダーバーで終わる場合、文が不完全または接続が間違っている可能性があります",
        }

        for i, error in enumerate(self.settings["errors"]):
            error_frame = ttk.Frame(self.scrollable_frame)
            error_frame.grid(row=i*2, column=0, sticky="ew", padx=10, pady=(10, 0), ipadx=5, ipady=5)

            error_label = ttk.Label(
                error_frame, text=error["name"], font=("TkDefaultFont", 15, "bold")
            )
            error_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

            all_var = tk.BooleanVar(value=all(error["languages"].values()))
            ttk.Checkbutton(
                error_frame,
                text="全て選択/解除",
                variable=all_var,
                command=lambda e=error["name"], v=all_var: self.toggle_all(e, v),
            ).grid(row=0, column=1, sticky=tk.E)

            lang_frame = ttk.Frame(error_frame)
            lang_frame.grid(row=1, column=0, columnspan=2, pady=5)

            self.lang_vars[error["name"]] = {}
            for j, lang in enumerate(
                ["KOR", "ENG", "JPN", "CHN", "SPA", "VIE", "IND", "THA"]
            ):
                var = tk.BooleanVar(value=error["languages"].get(lang, False))
                ttk.Checkbutton(lang_frame, text=lang, variable=var).grid(
                    row=j // 4, column=j % 4, sticky=tk.W, padx=5, pady=2
                )
                self.lang_vars[error["name"]][lang] = var

            # エラー説明追加
            description, example = error_descriptions.get(error["name"], ("", ""))
            desc_label = ttk.Label(
                self.scrollable_frame, text=f"説明:\n{description}\n\n検索テキスト例:\n{example}", anchor="w", justify="left"
            )
            desc_label.grid(row=i*2, column=1, sticky="w", padx=20, pady=5)

            # 特記事項追加
            note = error_notes.get(error["name"], "")
            note_label = ttk.Label(
                self.scrollable_frame, text=f"{note}", anchor="w", justify="left"
            )
            note_label.grid(row=i*2, column=2, sticky="w", padx=20, pady=5)

            # エラー項目と説明の間に区切り線追加
            ttk.Separator(self.scrollable_frame, orient="horizontal").grid(
                row=i*2+1, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 0)
            )

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10, padx=20, fill=tk.X)

        tb.Button(button_frame, text="キャンセル", command=self.destroy, bootstyle="danger-outline").pack(side=tk.RIGHT)
        tb.Button(button_frame, text="保存", command=self.save_settings, bootstyle="success-outline").pack(
            side=tk.RIGHT, padx=10
        )

    def _on_mousewheel(self, event):
        if not self.winfo_exists():
            return

        try:
            # 現在のスクロール位置と全体サイズ確認
            current_position = self.canvas.yview()

            # スクロール方向決定（方向のみ使用、大きさは無視）
            if platform.system() == "Windows":
                direction = -1 if event.delta > 0 else 1
            elif platform.system() == "Darwin":  # macOS
                direction = -1 if event.delta < 0 else 1
            else:  # Linux
                if event.num == 4:
                    direction = -1
                elif event.num == 5:
                    direction = 1
                else:
                    return

            # 固定スクロール量適用
            delta = direction * self.scroll_speed

            # スクロール適用
            if (delta > 0 and current_position[1] < 1.0) or \
                (delta < 0 and current_position[0] > 0.0):
                self.canvas.yview_scroll(int(delta), "units")
        except tk.TclError:
            # ウィンドウが既に閉じられているか、キャンバスが存在しない場合
            self.unbind_all("<MouseWheel>")
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")

    def toggle_all(self, error_name, all_var):
        state = all_var.get()
        for lang_var in self.lang_vars[error_name].values():
            lang_var.set(state)

    def save_settings(self):
        at_least_one_selected = False
        for error in self.settings["errors"]:
            error_name = error["name"]
            for lang, var in self.lang_vars[error_name].items():
                error["languages"][lang] = var.get()
                if var.get():
                    at_least_one_selected = True

        if not at_least_one_selected:
            messagebox.showwarning(
                "警告", "少なくとも一つの言語が選択されている必要があります。"
            )
            return
        self.parent.settings = self.settings
        self.parent.save_settings()
        self.destroy()
        messagebox.showinfo("通知", "設定が保存されました。")

    def on_closing(self):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")
        self.destroy()