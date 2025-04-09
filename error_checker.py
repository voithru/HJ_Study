import unicodedata
import re


def count_cjk_characters(text):
    count = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ["F", "W"]:
            count += 1
        elif unicodedata.east_asian_width(char) in ["Na", "H"] or char.isspace():
            count += 0.5
        else:
            count += 1
    return count


def check_errors(srt_file, lang_code, file_name, settings):
    errors = []
    
    # 모든 설정된 에러 검사 매핑
    error_check_functions = {
        "行ごとの文字数": check_line_length,
        "行数": check_line_count,
        "@@@有無": check_at_marks,
        "中間省略記号": check_ellipsis,
        "ピリオド省略記号": check_dot_ellipsis,
        "ピリオド2,4個": check_double_dot,
        "行末ピリオド": check_end_punctuation,
        "ハイフン後スペースあり": lambda srt_file, lang_code, file_name: check_hyphen_space(srt_file, lang_code, file_name, True),
        "ハイフン後スペースなし": lambda srt_file, lang_code, file_name: check_hyphen_space(srt_file, lang_code, file_name, False),
        "不要なスペース": check_space_errors,
        "通常波線": check_normal_tilde,
        "音符記号": check_music_note,
        "ぼかし記号": check_blur_symbol,
        "全角数字": check_fullwidth_numbers,
        "画面字幕位置": check_bracket_text_position,
        "中国語引用符使用": check_chinese_quotes,
        "括弧使用": check_bracket_usage,
        "疑問符/感嘆符使用": check_question_exclamation_usage,
        "KOR使用": check_korean_language,
        "特殊アスキー文字": check_special_ascii_characters,
        "ハイフン1個": check_single_hyphen,
        "大括弧内容エラー": check_bracket_content,
        "行末ピリオド欠落": check_missing_end_punctuation,
        "最後の行カンマ": check_last_line_comma,
        "日本語句読点": check_japanese_punctuation,
        "持続時間エラー": check_duration,
        "エンコードエラー": check_encoding_issues,
        "文末ハイフン/アンダーバー": check_ending_hyphen_underscore,
    }
    
    # 사용자 설정에서 적용된 검사만 실행
    for error in settings["errors"]:
        error_name = error["name"]
        if error_name in error_check_functions and error["languages"].get(lang_code, False):
            error_func = error_check_functions[error_name]
            try:
                result = error_func(srt_file, lang_code, file_name)
                if result:
                    errors.extend(result)
            except Exception as e:
                # 에러 발생 시 추적 정보 추가
                errors.append({
                    "File": file_name,
                    "StartTC": "",
                    "ErrorType": "FUNCTION_ERROR",
                    "ErrorContent": f"Error in {error_name}: {str(e)}",
                    "SubtitleText": ""
                })
    
    return errors


def check_line_length(srt_file, lang_code, file_name):
    errors = []
    max_lengths = {
        "KOR": 20,
        "ENG": 42,
        "JPN": 16,
        "CHN": 20,
        "SPA": 42,
        "VIE": 42,
        "IND": 55,
        "THA": 42,
    }
    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            if lang_code in ["JPN", "CHN"]:
                length = count_cjk_characters(line)
            else:
                length = len(line)
            if length > max_lengths[lang_code]:
                error = {
                    "File": file_name,
                    "StartTC": str(sub.start),
                    "ErrorType": "行ごとの文字数",
                    "ErrorContent": f"{line_num}番目の行, {length:.1f} 文字 (最大: {max_lengths[lang_code]})",
                    "SubtitleText": sub.text,
                }
                errors.append(error)
    return errors


def check_line_count(srt_file, lang_code, file_name):
    errors = []
    max_lines = 3

    for sub in srt_file:
        lines = sub.text.split("\n")
        if len(lines) > max_lines:
            error = {
                "File": file_name,
                "StartTC": str(sub.start),
                "ErrorType": "行数",
                "ErrorContent": f"{len(lines)}行 (最大: {max_lines}行)",
                "SubtitleText": sub.text,
            }
            errors.append(error)
    return errors


def check_at_marks(srt_file, lang_code, file_name):
    errors = []
    at_marks = ['@@@', '＠＠＠']  # ゴバエリスト

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            if any(at_mark in line for at_mark in at_marks):
                error = {
                    "File": file_name,
                    "StartTC": str(sub.start),
                    "ErrorType": "@@@有無",
                    "ErrorContent": f"{line_num}番 行",
                    "SubtitleText": sub.text,
                }
                errors.append(error)
    return errors


def check_ellipsis(srt_file, lang_code, file_name):
    errors = []
    ellipsis_pattern = re.compile(r"⋯")

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            if ellipsis_pattern.search(line):
                error = {
                    "File": file_name,
                    "StartTC": str(sub.start),
                    "ErrorType": "中間省略記号",
                    "ErrorContent": f"{line_num}番目の行",
                    "SubtitleText": sub.text,
                }
                errors.append(error)
    return errors


def check_dot_ellipsis(srt_file, lang_code, file_name):
    errors = []
    ellipsis_pattern = re.compile(r"(?<!\.)\.\.\.(?!\.)")

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            if ellipsis_pattern.search(line):
                error = {
                    "File": file_name,
                    "StartTC": str(sub.start),
                    "ErrorType": "ピリオド省略記号",
                    "ErrorContent": f"{line_num}番目の行",
                    "SubtitleText": sub.text,
                }
                errors.append(error)
    return errors


def check_double_dot(srt_file, lang_code, file_name):
    errors = []
    dot_pattern = re.compile(r"(?<![.])[.]{2}(?![.])|(?<![.])[.]{4}(?![.])")

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            matches = dot_pattern.finditer(line)
            for match in matches:
                error_type = "ピリオド2個" if len(match.group()) == 2 else "ピリオド4個"
                error = {
                    "File": file_name,
                    "StartTC": str(sub.start),
                    "ErrorType": error_type,
                    "ErrorContent": f"{line_num}番目の行, 位置: {match.start()}",
                    "SubtitleText": sub.text,
                }
                errors.append(error)
    return errors


def check_end_punctuation(srt_file, lang_code, file_name):
    errors = []

    end_puncts = ["."] if lang_code not in ["JPN", "CHN"] else ["。", "."]

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if (
                line
                and any(line.endswith(punct) for punct in end_puncts)
                and not line.endswith("...")
            ):
                error = {
                    "File": file_name,
                    "StartTC": str(sub.start),
                    "ErrorType": "行末ピリオド",
                    "ErrorContent": f"{line_num}番目の行",
                    "SubtitleText": sub.text,
                }
                errors.append(error)
    return errors


def check_hyphen_space(srt_file, lang_code, file_name, space_expected):
    errors = []
    error_type = "ハイフン後スペースあり" if space_expected else "ハイフン後スペースなし"

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith("-"):
                if space_expected:
                    if line.strip().startswith("- "):
                        error = {
                            "File": file_name,
                            "StartTC": str(sub.start),
                            "ErrorType": error_type,
                            "ErrorContent": f"{line_num}番目の行",
                            "SubtitleText": sub.text,
                        }
                        errors.append(error)
                else:
                    if not line.strip().startswith("- "):
                        error = {
                            "File": file_name,
                            "StartTC": str(sub.start),
                            "ErrorType": error_type,
                            "ErrorContent": f"{line_num}番目の行",
                            "SubtitleText": sub.text,
                        }
                        errors.append(error)
    return errors


def check_space_errors(srt_file, lang_code, file_name):
    errors = []
    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            if line.strip() != line:
                errors.append(
                    {
                        "File": file_name,
                        "StartTC": str(sub.start),
                        "ErrorType": "不要なスペース",
                        "ErrorContent": f"{line_num}番目の行: 行開始/終了スペース",
                        "SubtitleText": sub.text,
                    }
                )
            if "  " in line:
                errors.append(
                    {
                        "File": file_name,
                        "StartTC": str(sub.start),
                        "ErrorType": "不要なスペース",
                        "ErrorContent": f"{line_num}番目の行: 二重スペース",
                        "SubtitleText": sub.text,
                    }
                )
            if re.search(r"[\(\[\{]\s|\s[\)\]\}]", line):
                errors.append(
                    {
                        "File": file_name,
                        "StartTC": str(sub.start),
                        "ErrorType": "不要なスペース",
                        "ErrorContent": f"{line_num}番目の行: 括弧内スペース",
                        "SubtitleText": sub.text,
                    }
                )

    return errors


def check_normal_tilde(srt_file, lang_code, file_name):
    errors = []
    normal_tildes = ["~", "〜"]  # 通常波線と日本語波線

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            for tilde in normal_tildes:
                if tilde in line:
                    positions = [i for i, char in enumerate(line) if char == tilde]
                    for pos in positions:
                        error = {
                            "File": file_name,
                            "StartTC": str(sub.start),
                            "ErrorType": "通常波線",
                            "ErrorContent": f"{line_num}番目の行, 位置: {pos}, 文字: {tilde}",
                            "SubtitleText": sub.text,
                        }
                        errors.append(error)
    return errors


def check_music_note(srt_file, lang_code, file_name):
    errors = []
    music_note = "♪"
    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            if music_note in line:
                note_count = line.count(music_note)
                if note_count != 2:
                    errors.append(
                        {
                            "File": file_name,
                            "StartTC": str(sub.start),
                            "ErrorType": "音符記号個数",
                            "ErrorContent": f"{line_num}番目の行: \
                                一行に音符記号が2個ではありません (現在 {note_count}個)",
                            "SubtitleText": sub.text,
                        }
                    )
                else:
                    first_note_index = line.index(music_note)
                    second_note_index = line.rindex(music_note)
                    if (
                        first_note_index + 1 < len(line)
                        and line[first_note_index + 1] != " "
                    ):
                        errors.append(
                            {
                                "File": file_name,
                                "StartTC": str(sub.start),
                                "ErrorType": "音符記号スペース",
                                "ErrorContent": f"{line_num}番目の行: 最初の音符記号の後にスペースがありません",
                                "SubtitleText": sub.text,
                            }
                        )

                    if second_note_index > 0 and line[second_note_index - 1] != " ":
                        errors.append(
                            {
                                "File": file_name,
                                "StartTC": str(sub.start),
                                "ErrorType": "音符記号スペース",
                                "ErrorContent": f"{line_num}番目の行: 2番目の音符記号の前にスペースがありません",
                                "SubtitleText": sub.text,
                            }
                        )
    return errors


def check_blur_symbol(srt_file, lang_code, file_name):
    errors = []
    blur_symbol = "○"

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            if blur_symbol in line:
                positions = [i for i, char in enumerate(line) if char == blur_symbol]
                for pos in positions:
                    error = {
                        "File": file_name,
                        "StartTC": str(sub.start),
                        "ErrorType": "ぼかし記号",
                        "ErrorContent": f"{line_num}番目の行, 位置: {pos}",
                        "SubtitleText": sub.text,
                    }
                    errors.append(error)
    return errors


def check_fullwidth_numbers(srt_file, lang_code, file_name):
    errors = []
    fullwidth_numbers = "０１２３４５６７８９"  # 全角数字

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            for i, char in enumerate(line):
                if char in fullwidth_numbers:
                    error = {
                        "File": file_name,
                        "StartTC": str(sub.start),
                        "ErrorType": "全角数字",
                        "ErrorContent": f"{line_num}番目の行, 位置: {i}, 文字: {char}",
                        "SubtitleText": sub.text,
                    }
                    errors.append(error)
    return errors


def check_bracket_text_position(srt_file, lang_code, file_name):
    errors = []

    for sub in srt_file:
        lines = sub.text.split("\n")
        bracket_lines = []
        normal_lines = []
        is_bracket_open = False
        opening_brackets = 0
        closing_brackets = 0

        for i, line in enumerate(lines):
            if "[" in line:
                is_bracket_open = True
                opening_brackets += line.count("[")
            if "]" in line:
                closing_brackets += line.count("]")
                if opening_brackets == closing_brackets:
                    is_bracket_open = False

            if is_bracket_open or "[" in line or "]" in line:
                bracket_lines.append(i)
            elif line.strip():
                normal_lines.append(i)

        if opening_brackets != closing_brackets:
            errors.append(
                {
                    "File": file_name,
                    "StartTC": str(sub.start),
                    "ErrorType": "画面字幕括弧エラー",
                    "ErrorContent": f"括弧対が一致しません。(開き括弧: {opening_brackets}, 閉じ括弧: {closing_brackets})",
                    "SubtitleText": sub.text,
                }
            )

        if bracket_lines and normal_lines:
            if max(normal_lines) > min(bracket_lines):
                errors.append(
                    {
                        "File": file_name,
                        "StartTC": str(sub.start),
                        "ErrorType": "画面字幕位置エラー",
                        "ErrorContent": "通常テキストが画面テキストより下にあります。",
                        "SubtitleText": sub.text,
                    }
                )

    return errors

def check_chinese_quotes(srt_file, lang_code, file_name):
    errors = []
    chinese_quotes = ['"', '"', "'", "'"]  # 中国語大ダツオツと小ダツオツ

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            for quote in chinese_quotes:
                if quote in line:
                    error = {
                        "File": file_name,
                        "StartTC": str(sub.start),
                        "ErrorType": "中国語引用符使用",
                        "ErrorContent": f"{line_num}番目の行, 位置: {line.index(quote)}, 文字: {quote}",
                        "SubtitleText": sub.text,
                    }
                    errors.append(error)
    return errors

def check_bracket_usage(srt_file, lang_code, file_name):
    errors = []
    
    # 言語別基準設定
    criteria = {
        "JPN": {
            "parentheses": "fullwidth",  # 括弧は全角でなければなりません
            "brackets": "halfwidth",     # 括弧は半角でなければなりません
        },
        "CHN": {
            "parentheses": "halfwidth",  # 括弧は半角でなければなりません
            "brackets": "halfwidth",     # 括弧は半角でなければなりません
        },
        # 他言語に対する基準をここに追加
    }
    
    # 半角および全角記号定義
    halfwidth_parentheses = "()"
    fullwidth_parentheses = "（）"
    halfwidth_brackets = "[]"
    fullwidth_brackets = "［］"
    
    # 現在の言語の基準取得
    if lang_code not in criteria:
        return errors  # 基準がない言語は検査しません
    
    current_criteria = criteria[lang_code]
    
    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            for i, char in enumerate(line):
                if char in halfwidth_parentheses + fullwidth_parentheses:
                    expected = current_criteria["parentheses"]
                    if (char in halfwidth_parentheses and expected == "fullwidth") or \
                       (char in fullwidth_parentheses and expected == "halfwidth"):
                        error = {
                            "File": file_name,
                            "StartTC": str(sub.start),
                            "ErrorType": "括弧使用エラー",
                            "ErrorContent": f"{line_num}番目の行, 位置: {i}, 文字: {char}",
                            "SubtitleText": sub.text,
                        }
                        errors.append(error)
                elif char in halfwidth_brackets + fullwidth_brackets:
                    expected = current_criteria["brackets"]
                    if (char in halfwidth_brackets and expected == "fullwidth") or \
                       (char in fullwidth_brackets and expected == "halfwidth"):
                        error = {
                            "File": file_name,
                            "StartTC": str(sub.start),
                            "ErrorType": "括弧使用エラー",
                            "ErrorContent": f"{line_num}番目の行, 位置: {i}, 文字: {char}",
                            "SubtitleText": sub.text,
                        }
                        errors.append(error)
    return errors


def check_question_exclamation_usage(srt_file, lang_code, file_name):
    errors = []
    halfwidth_symbols = "!?"
    fullwidth_symbols = "！？"
    question_exclamation = "!?！？"
    exception_mark = "…"

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            for i, char in enumerate(line):
                if char in question_exclamation:
                    prev_char = line[i-1] if i > 0 else None
                    next_char = line[i+1] if i < len(line) - 1 else None

                    if char in halfwidth_symbols:
                        if (prev_char in fullwidth_symbols if prev_char else False) or (next_char in fullwidth_symbols if next_char else False):
                            error = {
                                "File": file_name,
                                "StartTC": str(sub.start),
                                "ErrorType": "半角 ?! 周囲全角 ?!",
                                "ErrorContent": f"{line_num}番目の行, 位置: {i}, 文字: {char}",
                                "SubtitleText": sub.text,
                            }
                            errors.append(error)
                        elif (prev_char not in question_exclamation+exception_mark if prev_char else True) and (next_char not in question_exclamation+exception_mark if next_char else True):
                            error = {
                                "File": file_name,
                                "StartTC": str(sub.start),
                                "ErrorType": "半角 ?! 周囲符号なし",
                                "ErrorContent": f"{line_num}番目の行, 位置: {i}, 文字: {char}は全角でなければなりません。",
                                "SubtitleText": sub.text,
                            }
                            errors.append(error)
                    elif char in fullwidth_symbols:
                        if (prev_char in halfwidth_symbols if prev_char else False) or (next_char in halfwidth_symbols if next_char else False):
                            error = {
                                "File": file_name,
                                "StartTC": str(sub.start),
                                "ErrorType": "全角 ?! 周囲半角 ?!",
                                "ErrorContent": f"{line_num}番目の行, 位置: {i}, 文字: {char}",
                                "SubtitleText": sub.text,
                            }
                            errors.append(error)
                        elif (prev_char in fullwidth_symbols if prev_char else False) or (next_char in fullwidth_symbols if next_char else False):
                            error = {
                                "File": file_name,
                                "StartTC": str(sub.start),
                                "ErrorType": "全角 ?! 周囲全角 ?!",
                                "ErrorContent": f"{line_num}番目の行, 位置: {i}, 文字: {char}は半角でなければなりません。",
                                "SubtitleText": sub.text,
                            }
                            errors.append(error)

    return errors


def check_korean_language(srt_file, lang_code, file_name):
    errors = []
    if lang_code == "KOR":
        return errors  # 韓国語ファイルは検査しません

    korean_char_pattern = re.compile(r'[\u1100-\u11FF\u3130-\u318F\uAC00-\uD7AF]')

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            if korean_char_pattern.search(line):
                error = {
                    "File": file_name,
                    "StartTC": str(sub.start),
                    "ErrorType": "KOR使用",
                    "ErrorContent": f"{line_num}番目の行に韓国語が含まれています。",
                    "SubtitleText": sub.text,
                }
                errors.append(error)
    return errors

def check_special_ascii_characters(srt_file, lang_code, file_name):
    errors = []
    special_chars = {
        '\x08': "<0x08> 文字",
        '\xA0': "<0xA0> 文字"
    }

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            for char, error_type in special_chars.items():
                if char in line:
                    positions = [i for i, c in enumerate(line) if c == char]
                    for pos in positions:
                        error = {
                            "File": file_name,
                            "StartTC": str(sub.start),
                            "ErrorType": error_type,
                            "ErrorContent": f"{line_num}番目の行, 位置: {pos}",
                            "SubtitleText": sub.text,
                        }
                        errors.append(error)
    return errors

def check_single_hyphen(srt_file, lang_code, file_name):
    errors = []
    hyphen = '-'

    for sub in srt_file:
        lines = sub.text.split("\n")
        hyphen_count = sum(line.count(hyphen) for line in lines)
        leading_hyphen_lines = [line_num for line_num, line in enumerate(lines, 1) if line.strip().startswith(hyphen)]

        if hyphen_count == 1:
            error_content = "中間ハイフン1個"
            if leading_hyphen_lines:
                error_content = f"先頭ハイフン: {', '.join(map(str, leading_hyphen_lines))}番目の行"
            
            error = {
                "File": file_name,
                "StartTC": str(sub.start),
                "ErrorType": "ハイフン個数エラー",
                "ErrorContent": error_content,
                "SubtitleText": sub.text,
            }
            errors.append(error)

    return errors

def check_bracket_content(srt_file, lang_code, file_name):
    errors = []
    bracket_pattern = re.compile(r'\[(.*?)\]')  # 括弧内の内容を見つける正規表現

    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            matches = bracket_pattern.finditer(line)
            for match in matches:
                content = match.group(1)
                # 特殊記号や数字だけで構成されているか確認
                if content and all(char.isdigit() or not char.isalnum() for char in content):
                    error = {
                        "File": file_name,
                        "StartTC": str(sub.start),
                        "ErrorType": "括弧内容エラー",
                        "ErrorContent": f"{line_num}番目の行, 括弧内に翻訳するテキストがありません: '{content}'",
                        "SubtitleText": sub.text,
                    }
                    errors.append(error)

    return errors

def check_duration(srt_file, lang_code, file_name):
    errors = []
    min_duration = 1.0  # 1秒
    max_duration = 8.0  # 8秒

    for sub in srt_file:
        # 開始時間を秒に変換
        start_total_seconds = (sub.start.hours * 3600 + 
                             sub.start.minutes * 60 + 
                             sub.start.seconds + 
                             sub.start.milliseconds / 1000)
        
        # 終了時間を秒に変換
        end_total_seconds = (sub.end.hours * 3600 + 
                           sub.end.minutes * 60 + 
                           sub.end.seconds + 
                           sub.end.milliseconds / 1000)
        
        duration = end_total_seconds - start_total_seconds

        if duration < min_duration:
            error = {
                "File": file_name,
                "StartTC": str(sub.start),
                "ErrorType": "持続時間エラー",
                "ErrorContent": f"字幕が短すぎます: {duration:.3f}秒 (最小: {min_duration}秒)",
                "SubtitleText": sub.text,
            }
            errors.append(error)
        elif duration > max_duration:
            error = {
                "File": file_name,
                "StartTC": str(sub.start),
                "ErrorType": "持続時間エラー",
                "ErrorContent": f"字幕が長すぎます: {duration:.3f}秒 (最大: {max_duration}秒)",
                "SubtitleText": sub.text,
            }
            errors.append(error)
    return errors

def check_missing_end_punctuation(srt_file, lang_code, file_name):
    errors = []
    # 言語別文末記号定義
    end_puncts = {
        "JPN": ["。", ".", "！", "？", "…"],  # 日本語
        "CHN": ["。", ".", "！", "？", "…"],  # 中国語
        "default": [".", "!", "?", "..."]     # 他言語
    }
    
    # 例外処理する特殊ケース (句点がなくてもよい場合)
    exceptions = [
        r"^\[.*\]$",  # 括弧で囲まれたテキスト
        r"^♪.*♪$"    # 音符間のテキスト
    ]
    
    puncts = end_puncts.get(lang_code, end_puncts["default"])
    
    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:  # 空行は無視
                continue
                
            # 例外ケース確認
            if any(re.match(pattern, line) for pattern in exceptions):
                continue
                
            # 最後の行でない場合はスキップ
            if line_num < len(lines) and lines[line_num].strip():
                continue
                
            # 文末記号確認
            if not any(line.endswith(punct) for punct in puncts):
                error = {
                    "File": file_name,
                    "StartTC": str(sub.start),
                    "ErrorType": "行末ピリオド欠落",
                    "ErrorContent": f"{line_num}番目の行",
                    "SubtitleText": sub.text,
                }
                errors.append(error)
    
    return errors

def check_last_line_comma(srt_file, lang_code, file_name):
    errors = []
    
    for sub in srt_file:
        lines = sub.text.split("\n")
        # 空行削除
        lines = [line for line in lines if line.strip()]
        
        if lines:  # 行が1つ以上ある場合
            last_line = lines[-1].strip()
            if last_line.endswith(","):
                error = {
                    "File": file_name,
                    "StartTC": str(sub.start),
                    "ErrorType": "最後の行カンマ",
                    "ErrorContent": f"最後の行がカンマで終わります",
                    "SubtitleText": sub.text,
                }
                errors.append(error)
    
    return errors

def check_japanese_punctuation(srt_file, lang_code, file_name):
    errors = []
    western_punctuation = ['.', ',']
        
    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            for punct in western_punctuation:
                if punct in line:
                    error = {
                        "File": file_name,
                        "StartTC": str(sub.start),
                        "ErrorType": "日本語句読点",
                        "ErrorContent": f"{line_num}番目の行: '{punct}' 使用",
                        "SubtitleText": sub.text,
                    }
                    errors.append(error)
    
    return errors

def check_encoding_issues(srt_file, lang_code, file_name):
    errors = []
    
    # エンコード破損現象が起こるときよく見られるパターン
    # 1. 特殊文字列パターン (UTF-8をCP949として誤解した場合など)
    suspicious_patterns = [
        r'â€™', r'â€"', r'â€œ', r'â€', r'Â', r'ï»¿',  # UTF-8 BOMと特殊文字破損
        r'í[\u0080-\u00FF][\u0080-\u00FF]',  # 韓国語破損パターン (UTF-8 -> EUC-KR/CP949誤解)
        r'ã[\u0080-\u00FF][\u0080-\u00FF]',  # 日本語破損パターン
        r'æ[\u0080-\u00FF][\u0080-\u00FF]',  # 中国語破損パターン
    ]
    
    combined_pattern = re.compile('|'.join(suspicious_patterns))
    
    # 2. 無効なUnicode文字シーケンス確認
    for sub in srt_file:
        # パターンマッチ検査
        if combined_pattern.search(sub.text):
            error = {
                "File": file_name,
                "StartTC": str(sub.start),
                "ErrorType": "エンコードエラー",
                "ErrorContent": "テキストにエンコード破損パターンが検出されました",
                "SubtitleText": sub.text,
            }
            errors.append(error)
            continue
            
        # 異常なUnicode文字比率検査
        unusual_chars = 0
        total_chars = len(sub.text.replace("\n", "").replace(" ", ""))
        
        if total_chars == 0:
            continue
            
        for char in sub.text:
            # 制御文字または通常でないUnicode範囲確認
            cp = ord(char)
            if (0x80 <= cp <= 0x9F) or cp == 0xFFFD:  # 制御文字または置換文字
                unusual_chars += 1
                
        # 異常文字比率が高い場合
        if total_chars > 0 and unusual_chars / total_chars > 0.1:  # 10%以上が異常文字なら疑わしい
            error = {
                "File": file_name,
                "StartTC": str(sub.start),
                "ErrorType": "エンコードエラー",
                "ErrorContent": f"異常文字比率: {unusual_chars}/{total_chars}",
                "SubtitleText": sub.text,
            }
            errors.append(error)
    
    return errors

def check_ending_hyphen_underscore(srt_file, lang_code, file_name):
    errors = []
    end_symbols = ['-', '_']  # 検査する記号
    
    for sub in srt_file:
        lines = sub.text.split("\n")
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and any(line.endswith(symbol) for symbol in end_symbols):
                ending_symbol = '-' if line.endswith('-') else '_'
                error = {
                    "File": file_name,
                    "StartTC": str(sub.start),
                    "ErrorType": "文末ハイフン/アンダーバー",
                    "ErrorContent": f"{line_num}番目の行が '{ending_symbol}'で終わります",
                    "SubtitleText": sub.text,
                }
                errors.append(error)
    
    return errors