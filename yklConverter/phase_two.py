import requests
import urllib.parse



class yklRunner:
    '''pass the formated japaness to yukumo website, and handle the response audio file.
    Design in client mode, init a client, and use it to make call'''
    url:str
    user_proxies:dict
    user_headers:dict

    def __init__(self) -> None:
        self.url = "https://www.yukumo.net/api/v2/","/koe.mp3"
        self.user_proxies = {
            "http":None,
            "https":None
        }
        self.user_headers = {
            'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
        }
        
    
    def getAudio(self, fmt_jpn:str, sound_option:str="f1",sound_type:str="AT1") -> bytes:
        '''return the binary audio file, fmt_jpn is the japanese to be read, sound_option is the sound type, by the website.
        sound_option type: In the original website(https://www.yukumo.net/#/), 声種 has servel options. 
        From the first "AT1-F1" to "AT2-RM3"(AT2 last), sound_option just the suffix of the name of 声種.

        Such as: fill in f1 will choose AT1-F1. fill in jgr will choose AT1-JGR. fill in yukkuri will choose AT2-YUKKURI.

        Noticed that all AT10 is not supported yet, since they have more complex payload in GET. this will be supported in the further evolution.
        '''

        #sound_type index
        api_index = {
            "AT1":"aqtk1",
            "AT2":"aqtk2",
            "AT10":"aqtk10",
        }
        if sound_type not in api_index.keys():
            raise ValueError(f"sound_type {sound_type} is not supported yet, please choose from {api_index.keys()}")
        if sound_option not in ["f1", "f2", "m1", "m2", "dvd", "imd1", "jgr", "r1", "rm", "huskey", "m4b", "mf1", "rb2", "rb3", "robo", "yukkuri", "f4", "m5", "mf2","rm3"]:
            raise ValueError(f"sound_option {sound_option} is not supported yet, please choose from ['f1', 'f2', 'm1', 'm2', 'dvd', 'imd1', 'jgr', 'r1', 'rm', 'huskey', 'm4b', 'mf1', 'rb2', 'rb3', 'robo', 'yukkuri', 'f4', 'm5', 'mf2','rm3']")
        #get url concatenation
        encoded_japanese = urllib.parse.quote(fmt_jpn)
        concatenated_url = self.url[0] + api_index[sound_type] + self.url[1] + f"?type={sound_option}&kanji={encoded_japanese}"
        ykl_response = requests.get(url=concatenated_url, proxies=self.user_proxies, headers=self.user_headers)

        return ykl_response.content
        