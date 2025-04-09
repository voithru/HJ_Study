import json
import os
import sys

class SettingsManager:
    def __init__(self, settings_file):
        self.settings_file = self.get_settings_file_path(settings_file)
        self.settings = self.load_settings()

    def get_settings_file_path(self, settings_file):
        if getattr(sys, 'frozen', False):
            # PyInstallerでビルドされた実行ファイルの場合
            application_path = os.path.dirname(sys.executable)
        else:
            # スクリプトとして実行される場合
            application_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(application_path, settings_file)

    def load_settings(self):
        default_languages = {
            lang: True for lang in ['KOR', 'ENG', 'JPN', 'CHN', 'SPA', 'VIE', 'IND', 'THA']}
        default_settings = {
            "errors": [
                {"name": "行ごとの文字数", "type": "Error", "languages": default_languages.copy()},
                {"name": "行数", "type": "Warning", "languages": default_languages.copy()},
                {"name": "@@@有無", "type": "Error", "languages": default_languages.copy()},
                {"name": "中間省略記号", "type": "Warning", "languages": {
                    "KOR": True,
                    "ENG": False,
                    "JPN": False,
                    "CHN": False,
                    "SPA": False,
                    "VIE": False,
                    "IND": False,
                    "THA": False}},
                {"name": "ピリオド省略記号", "type": "Warning", "languages": {
                    "KOR": False,
                    "ENG": True,
                    "JPN": True,
                    "CHN": True,
                    "SPA": True,
                    "VIE": True,
                    "IND": True,
                    "THA": True}},
                {"name": "ピリオド2,4個", "type": "Error", "languages": default_languages.copy()},
                {"name": "行末ピリオド", "type": "Warning", "languages": {
                    "KOR": True,
                    "ENG": True,
                    "JPN": True,
                    "CHN": True,
                    "SPA": False,
                    "VIE": True,
                    "IND": False,
                    "THA": True}},
                {"name": "行末ピリオド欠落", "type": "Error", "languages": {
                    "KOR": True,
                    "ENG": True,
                    "JPN": True,
                    "CHN": True,
                    "SPA": True,
                    "VIE": True,
                    "IND": True,
                    "THA": True}},
                {"name": "ハイフン後スペースあり", "type": "Warning", "languages": {
                    "KOR": False,
                    "ENG": True,
                    "JPN": False,
                    "CHN": False,
                    "SPA": False,
                    "VIE": False,
                    "IND": True,
                    "THA": False}},
                {"name": "ハイフン後スペースなし", "type": "Error", "languages": {
                    "KOR": True,
                    "ENG": False,
                    "JPN": True,
                    "CHN": True,
                    "SPA": True,
                    "VIE": True,
                    "IND": False,
                    "THA": True}},
                {"name": "不要なスペース", "type": "Warning", "languages": default_languages.copy()},
                {"name": "通常波線", "type": "Warning", "languages": {
                    "KOR": False,
                    "ENG": False,
                    "JPN": True,
                    "CHN": False,
                    "SPA": False,
                    "VIE": False,
                    "IND": False,
                    "THA": False}},
                {"name": "音符記号", "type": "Warning", "languages": default_languages.copy()},
                {"name": "ぼかし記号", "type": "Warning", "languages": default_languages.copy()},
                {"name": "全角数字", "type": "Warning", "languages": default_languages.copy()},
                {"name": "画面字幕位置", "type": "Error", "languages": default_languages.copy()},
                {"name": "中国語引用符使用", "type": "Warning", "languages": {
                    "KOR": False,
                    "ENG": False,
                    "JPN": False,
                    "CHN": True,
                    "SPA": False,
                    "VIE": False,
                    "IND": False,
                    "THA": False}},
                {"name": "括弧使用", "type": "Warning", "languages": {
                    "KOR": False,
                    "ENG": False,
                    "JPN": True,
                    "CHN": True,
                    "SPA": False,
                    "VIE": False,
                    "IND": False,
                    "THA": False}},
                {"name": "疑問符/感嘆符使用", "type": "Warning", "languages": {
                    "KOR": False,
                    "ENG": False,
                    "JPN": True,
                    "CHN": True,
                    "SPA": False,
                    "VIE": False,
                    "IND": False,
                    "THA": False}},
                {"name": "KOR使用", "type": "Error", "languages": default_languages.copy()},
                {"name": "特殊アスキー文字", "type": "Warning", "languages": default_languages.copy()},
                {"name": "ハイフン1個", "type": "Warning", "languages": default_languages.copy()},
                {"name": "大括弧内容エラー", "type": "Error", "languages": default_languages.copy()},
                {"name": "最後の行カンマ", "type": "Warning", "languages": default_languages.copy()},
                {"name": "日本語句読点", "type": "Warning", "languages": {
                    "KOR": False,
                    "ENG": False,
                    "JPN": True,
                    "CHN": False,
                    "SPA": False,
                    "VIE": False,
                    "IND": False,
                    "THA": False}},
                {"name": "持続時間エラー", "type": "Error", "languages": default_languages.copy()},
                {"name": "エンコードエラー", "type": "Error", "languages": default_languages.copy()},
                {"name": "文末ハイフン/アンダーバー", "type": "Warning", "languages": default_languages.copy()}
            ]
        }
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                return loaded_settings
            except json.JSONDecodeError:
                return default_settings
        else:
            return default_settings

    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"設定保存中にエラーが発生しました: {str(e)}")
            raise

    def get_settings(self):
        return self.settings

    def update_settings(self, new_settings):
        self.settings = new_settings
        self.save_settings()
