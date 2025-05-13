from lxml import etree
from typing import Dict, Optional
import time

def parse_xml(xml_string: str) -> Optional[Dict]:
    """
    解析微信XML消息为字典
    :param xml_string: XML字符串
    :return: 解析后的字典
    """
    try:
        # print(f"开始解析XML: {xml_string}")
        root = etree.fromstring(xml_string.encode('utf-8'))
        result = {}
        for child in root:
            result[child.tag] = child.text
        # print(f"解析XML结果: {result}")
        return result
    except Exception as e:
        print(f"XML解析失败: {e}")
        return None

def dict_to_xml(data: Dict) -> str:
    """
    将字典转换为微信XML消息
    :param data: 消息字典
    :return: XML字符串
    """
    print(f"开始生成XML, 数据: {data}")
    xml = ["<xml>"]
    for key, value in data.items():
        if value is not None:
            if isinstance(value, (int, float)):
                xml.append(f"<{key}>{value}</{key}>")
            else:
                xml.append(f"<{key}><![CDATA[{value}]]></{key}>")
    xml.append("</xml>")
    result = "\n".join(xml)
    print(f"生成的XML: {result}")
    return result

def create_text_reply(to_user: str, from_user: str, content: str) -> str:
    """
    创建文本回复消息
    :param to_user: 接收方帐号（收到的OpenID）
    :param from_user: 开发者微信号
    :param content: 回复的消息内容
    :return: 回复消息的XML字符串
    """
    print(f"创建文本回复: to={to_user}, from={from_user}, content={content}")
    timestamp = int(time.time())
    reply_dict = {
        "ToUserName": to_user,
        "FromUserName": from_user,
        "CreateTime": timestamp,
        "MsgType": "text",
        "Content": content
    }
    xml = dict_to_xml(reply_dict)
    print(f"文本回复XML: {xml}")
    return xml

def create_image_reply(to_user: str, from_user: str, media_id: str) -> str:
    """
    创建图片回复消息
    :param to_user: 接收方帐号（收到的OpenID）
    :param from_user: 开发者微信号
    :param media_id: 通过素材管理中的接口上传多媒体文件，得到的id
    :return: 回复消息的XML字符串
    """
    print(f"创建图片回复: to={to_user}, from={from_user}, media_id={media_id}")
    reply_dict = {
        "ToUserName": to_user,
        "FromUserName": from_user,
        "CreateTime": int(time.time()),
        "MsgType": "image",
        "Image": {
            "MediaId": media_id
        }
    }
    return dict_to_xml(reply_dict)

def create_news_reply(to_user: str, from_user: str, articles: list) -> str:
    """
    创建图文回复消息
    :param to_user: 接收方帐号（收到的OpenID）
    :param from_user: 开发者微信号
    :param articles: 图文消息列表，每个元素需包含title,description,picurl,url字段
    :return: 回复消息的XML字符串
    """
    print(f"创建图文回复: to={to_user}, from={from_user}, articles={articles}")
    items = []
    for article in articles:
        item = "<item>\n"
        item += f"<Title><![CDATA[{article.get('title', '')}]]></Title>\n"
        item += f"<Description><![CDATA[{article.get('description', '')}]]></Description>\n"
        item += f"<PicUrl><![CDATA[{article.get('picurl', '')}]]></PicUrl>\n"
        item += f"<Url><![CDATA[{article.get('url', '')}]]></Url>\n"
        item += "</item>\n"
        items.append(item)
        
    reply_xml = f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[news]]></MsgType>
<ArticleCount>{len(articles)}</ArticleCount>
<Articles>
{''.join(items)}
</Articles>
</xml>"""
    
    print(f"图文回复XML: {reply_xml}")
    return reply_xml 