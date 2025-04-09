import os
import pysrt
from error_checker import check_errors


def process_folder(folder_path, settings):
    results = {}

    for file in os.listdir(folder_path):
        if file.lower().endswith(".srt"):
            file_path = os.path.join(folder_path, file)
            lang_code = file.split("_")[-1].split(".")[0].upper()

            srt_file = pysrt.open(file_path)
            errors = check_errors(srt_file, lang_code, file, settings)
            if errors:
                if lang_code not in results:
                    results[lang_code] = []
                results[lang_code].extend(errors)

    return results


def fix_srt_format(folder_path):
    files_modified = 0
    total_tc_modified = 0
    total_text_space_modified = 0
    total_blank_lines_removed = 0
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.srt'):
                file_path = os.path.join(root, file)
                tc_modified = 0
                text_space_modified = 0
                blank_lines_removed = 0
                modified_lines = []
                
                try:
                    with open(file_path, 'r', encoding='utf-8-sig') as f:
                        lines = f.readlines()
                    
                    i = 0
                    while i < len(lines):
                        current_line = lines[i]  # rstrip() 削除
                        
                        # 現在の行が数字で次の行がタイムコードの場合、インデックスと判断
                        if (current_line.strip().isdigit() and 
                            i + 1 < len(lines) and 
                            ' --> ' in lines[i + 1]):
                            modified_lines.append(current_line.strip() + '\n')
                            i += 1
                            continue
                            
                        # TC行処理
                        if ' --> ' in current_line:
                            # TC行末の空白削除
                            cleaned_tc = current_line.rstrip()
                            if cleaned_tc != current_line.rstrip('\n'):
                                tc_modified += 1
                            modified_lines.append(cleaned_tc + '\n')
                            
                            # 字幕テキスト領域処理
                            i += 1
                            text_lines = []
                            consecutive_blank_lines = 0
                            while i < len(lines):
                                line = lines[i]  # 原本ライン維持
                                if not line.strip():  # 空行に出会ったら
                                    consecutive_blank_lines += 1
                                    i += 1
                                    # 次の行が数字でその次の行がタイムコードなら現在の字幕ブロック終了
                                    if (i < len(lines) - 1 and 
                                        lines[i].strip().isdigit() and 
                                        ' --> ' in lines[i + 1]):
                                        if consecutive_blank_lines > 1:
                                            blank_lines_removed += (consecutive_blank_lines - 1)
                                        break
                                    continue
                                
                                # テキストライン間の不要な空行カウント
                                if consecutive_blank_lines > 0:
                                    blank_lines_removed += consecutive_blank_lines
                                consecutive_blank_lines = 0
                                
                                # テキストラインの前後空白削除（全角/半角両方）
                                original_line = line.rstrip('\n')  # 改行だけ削除した原本
                                cleaned_text = original_line.strip(' 　')  # 半角/全角スペース両方削除
                                if cleaned_text != original_line:  # 原本と比較
                                    text_space_modified += 1
                                text_lines.append(cleaned_text + '\n')
                                i += 1
                            
                            # テキストライン追加
                            modified_lines.extend(text_lines)
                            modified_lines.append('\n')  # 字幕ブロック区分用空行
                            continue
                        
                        i += 1
                    
                    # ファイル末の不要な空白ライン削除
                    while modified_lines and modified_lines[-1].strip() == '':
                        modified_lines.pop()
                    
                    # 無条件でファイル保存
                    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                        f.writelines(modified_lines)
                    
                    # 実際に修正が発生した場合だけfiles_modified増加
                    if tc_modified > 0 or text_space_modified > 0 or blank_lines_removed > 0:
                        files_modified += 1
                    total_tc_modified += tc_modified
                    total_text_space_modified += text_space_modified
                    total_blank_lines_removed += blank_lines_removed
                
                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")
                    continue
    
    return files_modified, total_tc_modified, total_text_space_modified, total_blank_lines_removed


def check_srt_format(folder_path):
    format_errors = []
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.srt'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    first_tc_found = False
                    i = 0
                    while i < len(lines):
                        # タイムコードライン検索
                        if ' --> ' in lines[i]:
                            # 最初のタイムコードではない場合のみチェック
                            if first_tc_found:
                                # タイムコードの直上行が数字でないか
                                # その上の行が空行でない場合エラー
                                if (i < 1 or not lines[i-1].strip().isdigit() or 
                                    i < 2 or lines[i-2].strip() != ''):
                                    format_errors.append({
                                        'File': file,
                                        'Line': i + 1,
                                        'ErrorType': 'INDEX_BLANK_LINE',
                                        'ErrorContent': 'タイムコードの上の行がインデックスではないか、インデックスの上の行に空行がありません。',
                                        'StartTC': lines[i].strip()
                                    })
                            else:
                                # 最初のタイムコードは上の行がインデックスかだけチェック
                                if i < 1 or not lines[i-1].strip().isdigit():
                                    format_errors.append({
                                        'File': file,
                                        'Line': i + 1,
                                        'ErrorType': 'INDEX_LINE',
                                        'ErrorContent': 'タイムコードの上の行がインデックスではありません。',
                                        'StartTC': lines[i].strip()
                                    })
                                first_tc_found = True
                        
                        i += 1
                        
                except Exception as e:
                    format_errors.append({
                        'File': file,
                        'Line': 0,
                        'ErrorType': 'FILE_ERROR',
                        'ErrorContent': f'ファイル処理中にエラーが発生しました: {str(e)}',
                        'StartTC': ''
                    })
    
    return format_errors
