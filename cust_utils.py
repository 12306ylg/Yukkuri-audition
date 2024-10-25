from yklConverter import phaseOne
from yklConverter import phaseTwo
import PySimpleGUI as sg

import os
import re

def transform_request(text_path, aud_path, phase1op1, phase1op2, phase2op1):
    p1requestClient = phaseOne.ConverterClient()
    p1resolveClient = phaseOne.ConverterResolve()
    p2client = phaseTwo.yklRunner()

    filename = "Yukkuri_aud"
    file_path = os.path.join(aud_path, filename)
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




    with open(text_path, "r", encoding="utf-8") as chinese_file_fd:
        chinese_texts_raw = chinese_file_fd.readlines()

    ch_text = []
    for i in range(0, len(chinese_texts_raw)):
        ch_text = ch_text + [chinese_texts_raw[i].strip()]
        print(ch_text[i])

    #here is phase 1
    ch_text_modified: list[str] = []
    for i in ch_text:
        ch_text_modified.append( p1resolveClient.resolve(p1requestClient.post_request(i, phase1op1, phase1op2)) )

    #phase 1 complete
    for i in ch_text_modified:
        print(i)
    ch_text = None

    #phase 2 start
    


    for i in ch_text_modified:

        aud_file_path = os.path.join(file_path, f'YukAud{max_i}.mp3')
        aud_file_path = aud_file_path.replace("\\", "/")
        print(aud_file_path)
        max_i += 1
        with open(aud_file_path, 'wb') as mp3file:
            mp3file.write(p2client.getAudio(i, phase2op1))

    #ok









