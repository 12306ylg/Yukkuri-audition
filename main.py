import os
import re
import uuid
import time
import chardet
import streamlit as st
import concurrent.futures
from yklConverter import phase_one, phase_two

def show_options():
    opt2 = st.selectbox("选项", ['全角片假', '平假名'], key="opt2")
    opt3 = st.selectbox("声线", [
        'AT1-F1', 'AT1-F2', 'AT1-M1', 'AT1-M2', 'AT1-DVD', 'AT1-IMD1', 'AT1-JGR', 'AT1-R1',
        'AT2-RM', 'AT2-HUSKEY', 'AT2-M4B', 'AT2-MF1', 'AT2-RB2', 'AT2-RB3', 'AT2-ROBO',
        'AT2-YUKKURI', 'AT2-F4', 'AT2-M5', 'AT2-MF2', 'AT2-RM3'
    ], key="opt3")
    option2_dict = {'全角片假': 'zenkaku', '平假名': 'hirigana'}
    return [
        option2_dict[opt2],
        opt3.split('-')[1].lower(),
        opt3.split('-')[0]
    ]

def synthesize_audio(args):
    idx, seq, jp, file_path, user_options, aud_path = args
    unique_id = uuid.uuid4().hex
    aud_file_path = os.path.join(file_path, aud_path, f'YukAud_{seq}.mp3')
    aud_file_path = aud_file_path.replace("\\", "/")
    os.makedirs(os.path.dirname(aud_file_path), exist_ok=True)
    p2_client = phase_two.yklRunner()  
    audio_bytes = p2_client.getAudio(jp, user_options[1], user_options[2])
    with open(aud_file_path, 'wb+') as mp3file:
        mp3file.write(audio_bytes)
    return idx, aud_file_path

def get_start_seq(dir_path):
    counter_file = os.path.join(dir_path, "counter.txt")
    if os.path.exists(counter_file):
        with open(counter_file, "r") as f:
            try:
                start_seq = int(f.read().strip())
            except Exception:
                start_seq = 1
    else:
        start_seq = 1
    return start_seq

def update_counter(dir_path, new_seq):
    counter_file = os.path.join(dir_path, "counter.txt")
    with open(counter_file, "w") as f:
        f.write(str(new_seq))

def main():
    st.title("Yukkuri语音转换器")
    conversion_mode = st.radio("选择中文转换模式", ["在线转换（慢，稳定）", "本地转换（快一点）"], index=0)
    st.session_state.conversion_mode = conversion_mode

    text_input_ways = ["从文件读取转换", "直接输入文本"]
    selected_input_method = st.selectbox("选择输入方式", text_input_ways)
    st.warning("注意一行一句")
    text = ""
    if selected_input_method == "从文件读取转换":
        text_file = st.file_uploader("选择文本文件", type=["txt"])
        if text_file is not None:
            text_content = text_file.read()
            detected_encoding = chardet.detect(text_content)['encoding'] or 'utf-8'
            if 'last_file_name' not in st.session_state or st.session_state.last_file_name != text_file.name:
                st.session_state.encoding = detected_encoding if detected_encoding in ["utf-8", "gbk", "big5", "latin-1"] else "utf-8"
                st.session_state.last_file_name = text_file.name
            text = text_content.decode(st.session_state.encoding, errors='ignore')
            st.text_area("文本预览（如无异议直接下一步，否则在下面手动选择编码）：", text[:100], height=300)
            manual_encoding = st.selectbox("编码：", options=["utf-8", "gbk", "big5", "latin-1", "shift-jis"], index=["utf-8", "gbk", "big5", "latin-1", "shift-jis"].index(st.session_state.encoding))
            if manual_encoding and manual_encoding != st.session_state.encoding:
                st.session_state.encoding = manual_encoding
                text = text_content.decode(manual_encoding, errors='ignore')
        else:
            text = ""
            st.warning("请上传文本文件")
    else:
        text = st.text_area("请输入文本内容：", "附魔附魔")
    aud_path = st.text_input(f"请输入保存文件夹\n（如果是相对路径，音频会存在`{os.path.join(os.getcwd(),'Yukkuri_aud')}`）：", placeholder="不分类默认留空就好了，建议每个工程都独立一个文件夹") 
    if aud_path and re.search(r'[<>:"/\\|?*]', aud_path):
        st.error("路径中包含非法字符，请重新输入。")
        return
    with st.expander("选项"):
        user_options = show_options()
        thread_count = st.slider("线程数（1为单线程，推荐2-4）", min_value=1, max_value=32, value=4)
        st.session_state.user_options = user_options
        st.session_state.thread_count = thread_count
    if 'user_options' in st.session_state:
        st.write("已选择的选项：", st.session_state.user_options)
        st.write("线程数：", st.session_state.thread_count)
    if st.button("开始转化", key="start_convert"):
        if not text:
            st.warning("请先输入文本")
            return
        with st.spinner("##### 少女祈祷中...\n\n###### Now Loading..."):
            
            file_path = "Yukkuri_aud"
            file_path = file_path.replace("\\", "/")
            if not os.path.exists(file_path):
                os.makedirs(file_path)
            # 读取持久化计数器获得起始序号
            start_seq = get_start_seq(file_path)
            lines = [line.strip() for line in text.splitlines()]
            details = []
            detail_placeholder = st.empty()
            jp_lines = []
            for idx, raw in enumerate(lines):
                detail_placeholder.markdown(f"正在处理第{idx+1}句：{raw}")
                if st.session_state.conversion_mode == "在线转换":
                    p1_request_client = phase_one.OnlineConverter.ConverterClient()
                    p1_resolve_client = phase_one.OnlineConverter.ConverterResolve()
                    jp = p1_resolve_client.resolve(
                        p1_request_client.post_request(
                            raw,
                            st.session_state.user_options[0]
                        )
                    )
                else:
                    jp = phase_one.OfflineConverter.chinese_to_kana(raw, mode=st.session_state.user_options[0])
                    print(jp)
                jp_lines.append(jp)
                details.append({
                    "index": idx + 1,
                    "原文": raw,
                    "日文片假名": jp,
                    "音频文件": None
                })
            thread_count = st.session_state.get("thread_count", 1)
            # 在生成每句的语音时，将序号作为 seq 传入任务中
            synth_args = [(idx, start_seq + idx, jp, file_path, st.session_state.user_options, aud_path) for idx, jp in enumerate(jp_lines)]
            if thread_count == 1:
                p2_client = phase_two.yklRunner()
                for idx, jp in enumerate(jp_lines):
                    time.sleep(0.01)
                    seq = start_seq + idx
                    base_name = f'YukAud{seq}'
                    aud_file_path = os.path.join(file_path, f'{base_name}.mp3').replace("\\", "/")
                    count = 1
                    while os.path.exists(aud_file_path):
                        aud_file_path = os.path.join(file_path, f'{base_name}_{count}.mp3').replace("\\", "/")
                        count += 1
                    with open(aud_file_path, 'wb') as mp3file:
                        audio_bytes = p2_client.getAudio(jp, st.session_state.user_options[1], st.session_state.user_options[2])
                        if not ismp3(audio_bytes):
                            st.warning(f"第{idx+1}句音频无效，跳过。")
                            continue
                        mp3file.write(audio_bytes)
                    details[idx]["音频文件"] = aud_file_path
                    time.sleep(0.01)
            else:
                with concurrent.futures.ProcessPoolExecutor(max_workers=thread_count) as executor:
                    futures = {executor.submit(synthesize_audio, arg): arg[0] for arg in synth_args}
                    for future in concurrent.futures.as_completed(futures):
                        idx = futures[future]
                        try:
                            idx_result, aud_file_path = future.result()
                            details[idx_result]["音频文件"] = aud_file_path
                        except (concurrent.futures.TimeoutError, OSError) as e:
                            st.error(f"第{str(details[idx])}句音频合成失败: {str(e)}")
                        time.sleep(0.05)
            # 更新计数器，新计数器为起始序号加上本次生成音频的行数
            update_counter(file_path, start_seq + len(jp_lines))
            st.success("转化完成！哇多么好的音频啊！")
            st.info(f"音频文件保存在：{file_path}")
            with st.expander("处理细节"):
                for d in details:
                    st.markdown(f"**第{d['index']}句**")
                    st.text(f"原文: {d['原文']}")
                    st.text(f"日文片假名: {d['日文片假名']}")
                    st.text(f"音频文件: {d['音频文件']}")
                    st.audio(d['音频文件'], format="audio/mp3")

def ismp3(data: bytes) -> bool:
    """MP3文件通常以ID3标签开头，或以帧同步头0xFFFB/0xFFF3/0xFFF2等开头"""
    if data.startswith(b'ID3'):
        return True
    if len(data) > 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return True
    return False

if __name__ == '__main__':
    main()