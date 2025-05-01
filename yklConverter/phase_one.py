import re
import jaconv
from pypinyin import Style, pinyin
import requests
import warnings
import urllib.parse
from lxml import html

class OnlineConverter:
    class ConverterClient:
        '''this class should be initilized as a client, then use req to translate chinese into japanese'''
        response_result:str
        target_url = "https://www.ltool.net/chinese_simplified_and_traditional_characters_pinyin_to_katakana_converter_in_simplified_chinese.php"
        user_proxies = {
            "http":None,
            "https":None
        }
        user_headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'cache-control': 'max-age=0',
        'connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Charset': 'utf-8',
        'content-length': '86',
        'content-type': 'application/x-www-form-urlencoded',
        'host': 'www.ltool.net',
        'origin': 'https://www.ltool.net',
        'referer': 'https://www.ltool.net/chinese_simplified_and_traditional_characters_pinyin_to_katakana_converter_in_simplified_chinese.php',
        'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
        }

        def __init__(self) -> None:
            pass

        def post_request(self, content="", option="1", option_ext="zenkaku"):
            '''content is the chinese raw, options stands for the 6 options in original website. options_ext stands for the 3 options.
            Noticed that filling options para with 5 or 6 could lead unexpected result. this is the issue of original website.
            '''
            payload = {
                'contents': content,
                'firstinput': 'OK',
                'option': option,
                'optionext': option_ext
            }
            
            try:
                response = requests.post(url=self.target_url, data=payload, proxies=self.user_proxies, headers=self.user_headers)
                response.raise_for_status()
                return response.content
            except Exception as err:
                return f"An error occurred: {err}"

        def __ascii_encode(self, content_raw_utf8:str):
            warnings.warn("py request can auto encode incoming string, this method is redundance")
            return urllib.parse.quote(content_raw_utf8)

    class ConverterResolve:
        '''Response Result clss, designed as client modol. First user should new a instance of this class as client.
        After use ConvertClient calling a request, use this client to resolve the result, to get the true response.'''
        html_parser = html.HTMLParser(recover=True)

        def __init__(self) -> None:
            pass

        def __html_resolve(self, html_content, xpath_expression='''//*[@id="result"]/div'''):
            '''resolve html_content using the parser in the class, useing xpath rule in para:xpath_expression, return resolved result'''
            try:
                tree = html.fromstring(html_content, parser=self.html_parser)
                element = tree.xpath(xpath_expression)
                return element[0].text_content()
            except html.etree.XMLSyntaxError as e:
                return f"html resolve error occurred: {e}"

        def __result_text_filter(self, result_raw:str):
            filtered_string = re.sub(r'\(.*?\)', '', result_raw)
            # Remove spaces
            filtered_string = filtered_string.replace(" ", "")
            return filtered_string

        def resolve(self, html_page:str) -> str:
            element_text = self.__html_resolve(html_content=html_page)
            result_readable = self.__result_text_filter(element_text)
            return str(result_readable)

        def snworks(self, content:bytes)-> str:
            '''this method is debug only, don't ever use it in actual product environment'''
            warnings.warn("this method is debug only, don't ever use it in actual product environment")
            content = content.decode()
            res:str = re.findall(r'finalresult.+?>(.+?)</div',content)[0].strip()[1:]
            res = res.replace("%","\\x")
            return res
class OfflineConverter:
 def chinese_to_kana(text: str, mode: str = 'zenkaku') -> str:
    # 1. 中文 → 拼音（无声调）
    py_list = pinyin(text.replace(" ","__space__"),
                     style=Style.NORMAL,      # 去掉声调
                     strict=False)            # 较宽松地处理 ü、拼音孤立字母等
    romaji_tokens = []
    for item in py_list:
        token = item[0]
        if not re.match(r'^[a-zü]+$', token, re.I):   # 不是拼音就直接收
            romaji_tokens.append(token)
        else:                                         # 处理拼音中的 ü → yu
            romaji_tokens.append(token.replace('ü', 'yu'))

    romaji = ' '.join(romaji_tokens)

    # 2. 拼音(罗马字) → 片假名（全角）
    kana = jaconv.alphabet2kana(romaji)
    kana = jaconv.hira2kata(kana)   

    if mode == 'hankaku':
        kana = jaconv.z2h(kana, kana=True, digit=False, ascii=False)
    elif mode == 'hirigana':
        kana = jaconv.kata2hira(kana)
    elif mode != 'zenkaku':
        raise ValueError("mode 参数必须是 'zenkaku', 'hankaku' 或 'hirigana'")
    return kana.replace(" ", "").replace("__ッパッエ__", " ")