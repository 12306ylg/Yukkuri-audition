from yklConverter import phase_one
from yklConverter import phase_two
import os
import re

def transform_request(text:str, output_dir:str, phase1_option:str, phase1_option_ext:str, phase2_voice:str, phase2_type:str):
    p1requestClient = phase_one.OnlineConverter.ConverterClient()
    p1resolveClient = phase_one.OnlineConverter.ConverterResolve()
    p2client = phase_two.yklRunner()

    filename = "Yukkuri_aud"
    file_path = os.path.join(output_dir, filename)
    file_path = file_path.replace("\\", "/")

    if not os.path.exists(file_path):
        os.makedirs(file_path)

    pattern = re.compile(r"YukAud(\d+)\.mp3")
    max_i = 0

    for file_name in os.listdir(file_path):
        match = pattern.match(file_name)
        if match:
            i = int(match.group(1))
            if i > max_i:
                max_i = i

    chinese_texts_raw = text.splitlines()

    ch_text = []
    for i, line in enumerate(chinese_texts_raw):
        ch_text = ch_text + [line]
        print(ch_text[i])

    # 处理细节收集
    details = []

    # phase 1
    ch_text_modified: list[str] = []
    for idx, raw in enumerate(ch_text):
        jp = p1resolveClient.resolve(p1requestClient.post_request(raw, phase1_option, phase1_option_ext))
        ch_text_modified.append(jp)
        details.append({
            "index": idx + 1,
            "原文": raw,
            "日文片假名": jp,
            "音频文件": None
        })

    # phase 2
    for idx, jp in enumerate(ch_text_modified):
        max_i += 1
        aud_file_path = os.path.join(file_path, f'YukAud{max_i}.mp3')
        aud_file_path = aud_file_path.replace("\\", "/")
        with open(aud_file_path, 'wb') as mp3file:
            mp3file.write(p2client.get(jp, phase2_voice, phase2_type))
        details[idx]["音频文件"] = aud_file_path

    return aud_file_path, max_i, details









