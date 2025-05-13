import uvicorn
import requests
import urllib.parse
from openai import OpenAI
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import PlainTextResponse

import config
from utils.crypto import WXBizMsgCrypt
from utils.xml_parser import parse_xml
from utils.feishu_table import FeishuTable

access_token = ''
next_cursor = ''
feishu_table = FeishuTable('G1rDbcKyNaL1bAso3l8cImdYntX', 'tblpA7YT2FsTls21')

app = FastAPI(title="微信客服回调简化版",
              description="仅包含验证和消息解码功能")


@app.get("/", response_class=PlainTextResponse)
async def root():
    """
    根路径，返回简单的说明
    """
    return "微信客服回调接口已成功部署，请在微信客服管理后台配置 /wechat 作为回调地址"


@app.get("/wechat", response_class=PlainTextResponse)
async def wechat_get(
        msg_signature: str,
        timestamp: str,
        nonce: str,
        echostr: str
):
    """
    处理微信服务器的验证请求
    """
    try:
        # 使用WXBizMsgCrypt处理验证请求
        wxcpt = WXBizMsgCrypt(
            config.WECHAT_TOKEN,
            config.WECHAT_ENCODING_AES_KEY,
            config.WECHAT_APP_ID
        )

        # URL解码
        echostr_decoded = urllib.parse.unquote(echostr)

        # 直接使用验证方法
        result = wxcpt.VerifyURL(msg_signature, timestamp, nonce,
                                 echostr_decoded)

        # 根据返回类型判断结果
        if isinstance(result, bytes):
            return result.decode('utf-8')
        elif isinstance(result, int) and result < 0:
            print(f"验证URL失败，错误码: {result}")
            raise HTTPException(status_code=403,
                                detail=f"验证失败，错误码: {result}")
        else:
            print(f"未知的返回结果: {result}")
            raise HTTPException(status_code=500, detail="处理验证请求失败")

    except Exception as e:
        print(f"处理验证请求异常: {e}")
        raise HTTPException(status_code=500, detail=f"处理请求异常: {str(e)}")


def get_access_token(force=False):
    global access_token

    if not access_token or force:
        res = requests.get(
            f'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
            f'?corpid={config.WECHAT_APP_ID}&corpsecret={config.WECHAT_SECRET}'
        )
        access_token = res.json().get('access_token')

    return access_token


def _request(url, data):
    _access_token = get_access_token()
    res = requests.post(url + _access_token, json=data)
    if res.json()['errcode'] == 0:
        return res.json()

    print('error request: ', res.json())
    _access_token = get_access_token(force=True)
    res = requests.post(url + _access_token, json=data)
    return res.json()


def get_message(params, next_cursor):
    url = 'https://qyapi.weixin.qq.com/cgi-bin/kf/sync_msg?access_token='

    data = {
        "token": params['Token'],
        "open_kfid": params['OpenKfId'],
    }
    if next_cursor:
        data['cursor'] = next_cursor

    return _request(url, data)


def send_text_message(openid, user_id, msgid, content):
    data = {
        "touser": user_id,
        "open_kfid": openid,
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    if msgid:
        data['msgid'] = msgid

    return _request(
        'https://qyapi.weixin.qq.com/cgi-bin/kf/send_msg?access_token=',
        data
    )


def gen_tags(url, tags):
    res = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
        }
    )

    soup = BeautifulSoup(res.text, 'html.parser')
    body = soup.find('body')

    prompt = '''
    # 角色
    你是一个高效的分类标签生成助手，能精准分析文本内容，为其生成合适的分类标签，方便在文章库中进行过滤。若文章介绍了某个软件或者工具，会将该软件/工具名称也作为一个标签。

    ## 技能
    ### 技能 1: 生成分类标签
    1. 仔细分析用户提供的文本内容。
    2. 根据内容主题、关键信息等，生成不超过4个分类标签，每个标签不超过4个字。
    3. 若文本介绍了软件或工具，将该软件/工具名称也作为一个标签。
    4. 用英文逗号分隔标签进行输出。

    ## 限制:
    - 只专注于生成文本分类标签相关内容，拒绝回答无关话题。
    - 输出的标签必须符合要求，不超过规定数量和字数。
    - 输出格式必须是英文逗号分隔的标签形式。
    - 只需输出标签，不要包含其他内容。
    - 如果在已有标签中有相近的，就使用已有标签。
    
    ## 已有标签:
    {}

    具体内容如下：\n\n
    {}
    '''.format('\n'.join(f'- {o}' for o in tags),
               body.text.replace('\n\n\n', '\n').strip())

    client = OpenAI(
        base_url=config.OPENAI_API_BASE,
        api_key=config.OPENAI_API_KEY
    )

    response = client.responses.create(
        model="gpt-4.1",
        input=prompt
    )
    return response.output_text.split(',')


@app.post("/wechat")
async def wechat_post(
        request: Request,
        msg_signature: str = None,
        timestamp: str = None,
        nonce: str = None
):
    """
    处理微信客服消息，仅进行解码
    """
    try:
        # 打印请求参数
        print(f"接收POST请求: sig={msg_signature}, ts={timestamp}, nonce={nonce}")

        # 获取请求体
        body = await request.body()
        xml_content = body.decode("utf-8")
        message_dict = parse_xml(xml_content)

        # 如果直接解析成功，并且有消息类型，则使用直接解析结果
        if message_dict and "MsgType" in message_dict:
            print("使用直接解析结果")
            print(f'解析结果: {message_dict}')
            return Response(content="success", media_type="text/plain")

        # 否则尝试解密处理
        # print("尝试解密处理消息")
        # 检查必要参数
        if not all([msg_signature, timestamp, nonce]):
            print("缺少必要的加密参数，无法解密")
            return Response(content="success", media_type="text/plain")

        # 初始化WXBizMsgCrypt
        wxcpt = WXBizMsgCrypt(
            config.WECHAT_TOKEN,
            config.WECHAT_ENCODING_AES_KEY,
            config.WECHAT_APP_ID
        )

        # 解密消息
        ret, decrypted_content = wxcpt.DecryptMsg(
            xml_content, msg_signature, timestamp, nonce)
        if ret != 0:
            print(f"消息解密失败，错误码: {ret}")
            return Response(content="success", media_type="text/plain")

        # 解析解密后的XML
        message_dict = parse_xml(decrypted_content.decode('utf-8'))
        # print(f"解密后解析结果: {message_dict}")

        global next_cursor
        messages = get_message(message_dict, next_cursor)
        next_cursor = messages.get('next_cursor', '')

        if not messages['msg_list']:
            return Response(content="success", media_type="text/plain")

        # print(f'原始消息：{messages}')
        message = messages['msg_list'][-1]
        if message['msgtype'] != 'link':
            send_text_message(
                message['open_kfid'],
                message['external_userid'],
                message['msgid'],
                '目前我只能处理链接消息'
            )
            # 返回success
            return Response(content="success", media_type="text/plain")

        send_text_message(
            message['open_kfid'],
            message['external_userid'],
            message['msgid'],
            '开始保存文章，请稍等...'
        )

        field = feishu_table.get_field('vewNTuIRsZ', '分类')
        options = [o["name"] for o in field["property"]["options"]]
        tags = gen_tags(message['link']['url'], options)
        feishu_table.create_record(
            {
                '标题': message['link']['title'],
                '分类': tags,
                '链接': {
                    'text': message['link']['url'],
                    'link': message['link']['url'],
                },
                '描述': message['link']['desc'],
                '图片链接': message['link']['pic_url'],
            }
        )
        send_text_message(message['open_kfid'], message['external_userid'], '', '文章保存成功！')

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"处理消息异常: {e}")
        return Response(content="success", media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
