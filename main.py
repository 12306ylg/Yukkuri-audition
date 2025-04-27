import os
import re
import uuid
import concurrent.futures
import streamlit as st
import chardet
from yklConverter import phaseOne, phaseTwo


def show_options():
    option1 = ['ウォ', 'ウォ3', '我(ウォ)', '我(ウォ3)']
    option2 = ['全角片假', '半角假名', '平假名']
    option3 = ['AT1-F1', 'AT1-F2', 'AT1-M1', 'AT1-M2', 'AT1-DVD', 'AT1-IMD1', 'AT1-JGR', 'AT1-R1', 'AT2-RM', 'AT2-HUSKEY', 'AT2-M4B', 'AT2-MF1', 'AT2-RB2', 'AT2-RB3', 'AT2-ROBO', 'AT2-YUKKURI', 'AT2-F4', 'AT2-M5', 'AT2-MF2', 'AT2-RM3']

    st.subheader("ltools翻译选项1")
    opt1 = st.selectbox("选项1", option1, key="opt1")
    st.subheader("ltools翻译选项2")
    opt2 = st.selectbox("选项2", option2, key="opt2")
    st.subheader("yukumo声线")
    opt3 = st.selectbox("声线", option3, key="opt3")

    option1_dict = {'ウォ': '1', 'ウォ3': '2', '我(ウォ)': '3', '我(ウォ3)': '4'}
    option2_dict = {'全角片假': 'zenkaku', '半角假名': 'hankaku', '平假名': 'hirigana'}

    user_select_list = [
        option1_dict[opt1],
        option2_dict[opt2],
        opt3.split('-')[1].lower(),
        opt3.split('-')[0]
    ]
    return user_select_list

def main():
    st.title("Yukkuri语音转换器")
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

            manual_encoding = st.select_slider("编码：", options=["utf-8", "gbk", "big5", "latin-1"], value=st.session_state.encoding)
            if manual_encoding and manual_encoding != st.session_state.encoding:
                st.session_state.encoding = manual_encoding
                text = text_content.decode(manual_encoding, errors='ignore')
        else:
            text = ""
            st.warning("请上传文本文件")
    else:
        text = st.text_area("请输入文本内容：", "附魔附魔")
    aud_path = st.text_input(f"请输入保存文件夹\n（如果是相对路径，音频会存在`{os.path.join(os.getcwd(),'Yukkuri_aud')}`）：", placeholder="不分类默认留空就好了") 
    with st.expander("选项"):
        user_select_list = show_options()
        thread_count = st.slider("线程数（1为单线程，推荐2-4）", min_value=1, max_value=32, value=4)
        if user_select_list:
            st.session_state.user_select_list = user_select_list
        st.session_state.thread_count = thread_count
    if 'user_select_list' in st.session_state:
        st.write("已选择的选项：", st.session_state.user_select_list)
        st.write("线程数：", st.session_state.thread_count)
    if st.button("开始转化", key="start_convert"):
        if not text.strip()  or 'user_select_list' not in st.session_state or len(st.session_state.user_select_list) < 4:
            st.warning("请填写所有输入并选择所有选项")
            return
        with st.spinner("少女祈祷中...\nNow Loading..."):
            
            p1requestClient = phaseOne.ConverterClient()
            p1resolveClient = phaseOne.ConverterResolve()
            p2client = phaseTwo.yklRunner()
            file_path = "Yukkuri_aud"
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
            ch_text = [line.strip() for line in chinese_texts_raw]
            details = []
            detail_placeholder = st.empty()
            ch_text_modified = []
            for idx, raw in enumerate(ch_text):
                detail_placeholder.markdown(f"正在处理第{idx+1}句：{raw}")
                jp = p1resolveClient.resolve(p1requestClient.post_request(raw, st.session_state.user_select_list[0], st.session_state.user_select_list[1]))
                ch_text_modified.append(jp)
                details.append({
                    "index": idx + 1,
                    "原文": raw,
                    "日文片假名": jp,
                    "音频文件": None
                })

            def synthesize_audio(args):
                idx, jp, file_path, user_select_list = args
                unique_id = uuid.uuid4().hex
                aud_file_path = os.path.join("Yukkuri_aud", file_path, f'YukAud_{unique_id}.mp3')
                aud_file_path = aud_file_path.replace("\\", "/")
                audio_bytes = p2client.getAudio(jp, user_select_list[2], user_select_list[3])
                with open(aud_file_path, 'wb') as mp3file:
                    mp3file.write(audio_bytes)
                return idx, aud_file_path

            thread_count = st.session_state.get("thread_count", 1)
            synth_args = []
            for idx, jp in enumerate(ch_text_modified):
                synth_args.append((idx, jp, file_path, st.session_state.user_select_list))

            if thread_count == 1:
                for idx, jp in enumerate(ch_text_modified):
                    detail_placeholder.markdown(f"正在合成第{idx+1}句音频：{jp}")
                    max_i += 1
                    # 取原文前10字，去除特殊字符
                    safe_text = re.sub(r'[\\/:*?"<>|]', '', ch_text[idx][:10])
                    base_name = f'YukAud{max_i}_{safe_text}'
                    aud_file_path = os.path.join(file_path, f'{base_name}.mp3')
                    aud_file_path = aud_file_path.replace("\\", "/")
                    # 检查是否重名，若有则加序号
                    count = 1
                    while os.path.exists(aud_file_path):
                        aud_file_path = os.path.join(file_path, f'{base_name}_{count}.mp3')
                        aud_file_path = aud_file_path.replace("\\", "/")
                        count += 1
                    with open(aud_file_path, 'wb') as mp3file:
                        audio_bytes = p2client.getAudio(jp, st.session_state.user_select_list[2], st.session_state.user_select_list[3])
                        #防止无效文件写入
                        if not ismp3(audio_bytes):
                            st.warning(f"第{idx+1}句音频无效，跳过。")
                            max_i -= 1
                            continue
                            
                        mp3file.write(audio_bytes)
                    details[idx]["音频文件"] = aud_file_path
            else:
                with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
                    futures = {executor.submit(synthesize_audio, arg): arg[0] for arg in synth_args}
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            idx, aud_file_path = future.result()
                            details[idx]["音频文件"] = aud_file_path
                            detail_placeholder.markdown(f"已完成第{details[idx]['index']}句音频：{ch_text_modified[idx]}")
                        except (concurrent.futures.TimeoutError, OSError) as e:
                            st.error(f"第{idx+1}句音频合成失败: {e}")

                max_i += len(ch_text_modified)

            detail_placeholder.empty()
        st.success("转化完成！哇多么好的音频啊！")
        st.info(f"音频文件保存在：{file_path}")
        st.balloons()
        with st.expander("处理细节"):
            for d in details:
                st.markdown(f"**第{d['index']}句**")
                st.text(f"原文: {d['原文']}")
                st.text(f"日文片假名: {d['日文片假名']}")
                st.text(f"音频文件: {d['音频文件']}")
                st.audio(d['音频文件'], format="audio/mp3")

def ismp3(data: bytes) -> bool:
    # MP3文件通常以ID3标签开头，或以帧同步头0xFFFB/0xFFF3/0xFFF2等开头
    if data.startswith(b'ID3'):
        return True
    if len(data) > 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return True
    return False

if __name__ == '__main__':
    main()