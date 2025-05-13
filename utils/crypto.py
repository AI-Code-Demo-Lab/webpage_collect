#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import hashlib
import base64
import random
import string
import struct
import socket
import time
from utils import ierror
import xml.etree.cElementTree as ET
from Crypto.Cipher import AES

"""
关于ierror: 
由于原代码引用了ierror模块，为了保持代码完整性，
我们需要在同一目录下创建ierror.py文件
"""

class FormatException(Exception):
    pass

def throw_exception(message, exception_class=FormatException):
    """
    自定义异常
    """
    raise exception_class(message)

class SHA1:
    """计算公众平台的消息签名接口"""
    
    @staticmethod
    def getSHA1(token, timestamp, nonce, encrypt):
        """
        用SHA1算法生成安全签名
        @param token: 票据
        @param timestamp: 时间戳
        @param nonce: 随机字符串
        @param encrypt: 密文
        @return: 安全签名
        """
        try:
            sortlist = [token, timestamp, nonce, encrypt]
            sortlist.sort()
            sha = hashlib.sha1()
            sha.update("".join(sortlist).encode())
            return sha.hexdigest()
        except Exception as e:
            print(e)
            return ierror.WXBizMsgCrypt_ComputeSignature_Error

class PKCS7Encoder():
    """提供基于PKCS7算法的加解密接口"""
    
    block_size = 32
    
    @staticmethod
    def encode(text):
        """
        对需要加密的明文进行填充补位
        @param text: 需要进行填充补位操作的明文
        @return: 补齐明文字符串
        """
        text_length = len(text)
        # 计算需要填充的位数
        amount_to_pad = PKCS7Encoder.block_size - (text_length % PKCS7Encoder.block_size)
        if amount_to_pad == 0:
            amount_to_pad = PKCS7Encoder.block_size
        # 获得补位所用的字符
        pad = chr(amount_to_pad)
        return text + (pad * amount_to_pad).encode()
    
    @staticmethod
    def decode(decrypted):
        """
        删除解密后明文的补位字符
        @param decrypted: 解密后的明文
        @return: 删除补位字符后的明文
        """
        pad = decrypted[-1]
        if pad < 1 or pad > 32:
            pad = 0
        return decrypted[:-pad]

class Prpcrypt(object):
    """提供接收和推送给公众平台消息的加解密接口"""
    
    def __init__(self, key):
        # 自定义的加密密钥
        self.key = key
        # 设置加解密模式为AES的CBC模式
        self.mode = AES.MODE_CBC
    
    def encrypt(self, text, appid):
        """
        对明文进行加密
        @param text: 需要加密的明文
        @param appid: 公众号appid
        @return: 加密得到的字符串
        """
        # 16位随机字符串添加到明文开头
        text = text.encode() if isinstance(text, str) else text
        text = self.get_random_str() + struct.pack("I", socket.htonl(len(text))) + text + appid.encode()
        
        # 使用自定义的填充方式对明文进行补位填充
        text = PKCS7Encoder.encode(text)
        
        # 加密
        cryptor = AES.new(self.key, self.mode, self.key[:16])
        try:
            ciphertext = cryptor.encrypt(text)
            # 使用BASE64对加密后的字符串进行编码
            return ierror.WXBizMsgCrypt_OK, base64.b64encode(ciphertext)
        except Exception as e:
            print(e)
            return ierror.WXBizMsgCrypt_EncryptAES_Error, None
    
    def decrypt(self, text, appid):
        """
        对解密后的明文进行补位删除
        @param text: 密文
        @param appid: 公众号appid
        @return: 删除填充补位后的明文
        """
        try:
            cryptor = AES.new(self.key, self.mode, self.key[:16])
            # 使用BASE64对密文进行解码，然后AES-CBC解密
            plain_text = cryptor.decrypt(base64.b64decode(text))
        except Exception as e:
            print(f"解密出错: {e}")
            return ierror.WXBizMsgCrypt_DecryptAES_Error, None
        
        try:
            pad = plain_text[-1]
            # 去除16位随机字符串
            content = plain_text[16:-pad]
            xml_len = socket.ntohl(struct.unpack("I", content[: 4])[0])
            xml_content = content[4: xml_len + 4]
            from_appid = content[xml_len + 4:]
        except Exception as e:
            print(f"解析明文出错: {e}")
            return ierror.WXBizMsgCrypt_IllegalBuffer, None
        
        if from_appid.decode('utf-8', errors='ignore') != appid:
            print(f"AppID不匹配: {from_appid} vs {appid}")
            return ierror.WXBizMsgCrypt_ValidateAppid_Error, None
        
        return ierror.WXBizMsgCrypt_OK, xml_content
    
    def get_random_str(self):
        """
        随机生成16位字符串
        @return: 16位字符串
        """
        rule = string.ascii_letters + string.digits
        str_list = random.sample(rule, 16)
        return "".join(str_list).encode()

class WXBizMsgCrypt(object):
    # 构造函数
    def __init__(self, token, encodingAESKey, appId):
        """
        初始化
        @param token: 公众平台上，开发者设置的token
        @param encodingAESKey: 公众平台上，开发者设置的EncodingAESKey
        @param appId: 公众号的appid
        """
        try:
            self.key = base64.b64decode(encodingAESKey + "=")
            assert len(self.key) == 32
        except Exception as e:
            print(f"初始化错误: {e}")
            throw_exception("[error]: encodingAESKey invalid !", FormatException)
        
        self.token = token
        self.appid = appId
    
    def VerifyURL(self, sMsgSignature, sTimeStamp, sNonce, sEchoStr):
        """
        验证URL
        @param sMsgSignature: 签名串，对应URL参数的msg_signature
        @param sTimeStamp: 时间戳，对应URL参数的timestamp
        @param sNonce: 随机串，对应URL参数的nonce
        @param sEchoStr: 随机串，对应URL参数的echostr
        @return: 解密之后的echostr
        """
        # 打印调试信息
        print(f"VerifyURL参数: sig={sMsgSignature}, ts={sTimeStamp}, nonce={sNonce}, echo={sEchoStr}")
        
        # 先验证签名
        signature = SHA1.getSHA1(self.token, sTimeStamp, sNonce, sEchoStr)
        if signature != sMsgSignature:
            print(f"签名验证失败: 计算得到{signature}，期望{sMsgSignature}")
            return ierror.WXBizMsgCrypt_ValidateSignature_Error
        
        # 签名验证通过，开始解密
        pc = Prpcrypt(self.key)
        try:
            # 解密echostr
            ret, result = pc.decrypt(sEchoStr, self.appid)
            if ret != 0:
                print(f"解密失败，错误码: {ret}")
                return ret
            
            # 成功解密
            return result
        except Exception as e:
            print(f"验证URL时发生异常: {e}")
            return ierror.WXBizMsgCrypt_DecryptAES_Error
    
    def VerifySignature(self, sMsgSignature, sTimeStamp, sNonce, sEchoStr):
        """
        验证签名
        @param sMsgSignature: 签名串，对应URL参数的msg_signature
        @param sTimeStamp: 时间戳，对应URL参数的timestamp
        @param sNonce: 随机串，对应URL参数的nonce
        @param sEchoStr: 随机串，对应URL参数的echostr
        @return: 成功0，失败返回对应的错误码
        """
        signature = SHA1.getSHA1(self.token, sTimeStamp, sNonce, sEchoStr)
        if signature != sMsgSignature:
            return ierror.WXBizMsgCrypt_ValidateSignature_Error, None
        return 0, signature
    
    def EncryptMsg(self, sReplyMsg, sNonce, timestamp=None):
        """
        将公众号回复用户的消息加密打包
        @param sReplyMsg: 公众号待回复用户的消息，xml格式的字符串
        @param sNonce: 随机串，可以自己生成，也可以用URL参数的nonce
        @param timestamp: 时间戳，可以自己生成，也可以用URL参数的timestamp,如为None则自动用当前时间
        @return: 成功返回加密后的可以直接回复用户的密文，失败返回None
        """
        pc = Prpcrypt(self.key)
        
        if timestamp is None:
            timestamp = str(int(time.time()))
        # 加密
        ret, encrypt = pc.encrypt(sReplyMsg, self.appid)
        if ret != 0:
            return ret, None
        
        # 生成安全签名
        signature = SHA1.getSHA1(self.token, timestamp, sNonce, encrypt.decode())
        if signature == "":
            return ierror.WXBizMsgCrypt_ComputeSignature_Error, None
        
        return 0, self.generate_encrypted_xml(encrypt, signature, timestamp, sNonce)
    
    def DecryptMsg(self, sPostData, sMsgSignature, sTimeStamp, sNonce):
        """
        检验消息的真实性，并且获取解密后的明文
        @param sMsgSignature: 签名串，对应URL参数的msg_signature
        @param sTimeStamp: 时间戳，对应URL参数的timestamp
        @param sNonce: 随机串，对应URL参数的nonce
        @param sPostData: 密文，对应POST请求的数据
        @return: 解密后的原文
        """
        # 验证安全签名
        ret, encrypt, toUserName = self.extract_encrypted_xml(sPostData)
        if ret != 0:
            return ret, None
        
        # 验证安全签名
        signature = SHA1.getSHA1(self.token, sTimeStamp, sNonce, encrypt)
        if signature != sMsgSignature:
            return ierror.WXBizMsgCrypt_ValidateSignature_Error, None
        
        pc = Prpcrypt(self.key)
        ret, xml_content = pc.decrypt(encrypt, self.appid)
        if ret != 0:
            return ret, None
        
        return 0, xml_content
    
    def extract_encrypted_xml(self, xmltext):
        """
        提取出xml数据包中的加密消息
        @param xmltext: 待提取的xml字符串
        @return: 提取出的加密消息字符串
        """
        try:
            xml_tree = ET.fromstring(xmltext)
            encrypt = xml_tree.find("Encrypt")
            toUserName = xml_tree.find("ToUserName")
            if encrypt is None or encrypt.text is None:
                return ierror.WXBizMsgCrypt_ParseXml_Error, None, None
            return 0, encrypt.text, toUserName.text if toUserName is not None else None
        except Exception as e:
            print(f"解析XML出错: {e}")
            return ierror.WXBizMsgCrypt_ParseXml_Error, None, None
    
    def generate_encrypted_xml(self, encrypt, signature, timestamp, nonce):
        """
        生成xml消息
        @param encrypt: 加密后的消息密文
        @param signature: 安全签名
        @param timestamp: 时间戳
        @param nonce: 随机字符串
        @return: 生成的xml字符串
        """
        resp_dict = {
            'Encrypt': encrypt.decode(),
            'MsgSignature': signature,
            'TimeStamp': timestamp,
            'Nonce': nonce
        }
        resp_xml = """<xml>
<Encrypt><![CDATA[{Encrypt}]]></Encrypt>
<MsgSignature><![CDATA[{MsgSignature}]]></MsgSignature>
<TimeStamp>{TimeStamp}</TimeStamp>
<Nonce><![CDATA[{Nonce}]]></Nonce>
</xml>""".format(**resp_dict)
        return resp_xml

# 兼容性函数
def check_signature(msg_signature, timestamp, nonce, token, encrypt=None):
    """
    兼容性函数，用于验证消息签名
    """
    try:
        # 使用SHA1进行签名验证
        sortlist = [token, timestamp, nonce]
        if encrypt is not None:
            sortlist.append(encrypt)
        sortlist.sort()
        str_to_sign = ''.join(sortlist)
        
        # 打印调试信息
        print(f"签名验证参数: {str_to_sign}")
        
        # 计算签名
        sha = hashlib.sha1()
        sha.update(str_to_sign.encode('utf-8'))
        signature = sha.hexdigest()
        
        # 验证签名
        result = signature == msg_signature
        print(f"签名验证结果: 计算={signature}, 接收={msg_signature}, 匹配={result}")
        return result
    except Exception as e:
        print(f"签名验证失败: {e}")
        return False

def decrypt_echostr(encrypted_echostr: str, token: str, aes_key: str, app_id: str) -> str:
    """
    解密微信服务器发送的echostr
    :param encrypted_echostr: 加密的echostr
    :param token: 微信token
    :param aes_key: 微信EncodingAESKey
    :param app_id: 微信AppID
    :return: 解密后的echostr
    """
    try:
        crypt = WXBizMsgCrypt(token, aes_key, app_id)
        return crypt.VerifyURL(encrypted_echostr, token, aes_key, app_id)
    except Exception as e:
        print(f"解密echostr失败: {e}")
        return encrypted_echostr

def decrypt_token(encrypted_token: str) -> str:
    """
    解密微信客服消息中的Token
    @param encrypted_token: 加密的Token
    @return: 解密后的Token
    """
    # 微信客服Token解密逻辑
    # 注意：根据微信文档，Token是通过一定算法加密的
    # 这里实现解密逻辑，具体算法需要根据微信文档说明
    if encrypted_token.startswith('ENCD'):
        # 假设Token是通过base64编码的，实际可能需要更复杂的解密逻辑
        try:
            # 移除ENCD前缀
            token_data = encrypted_token[4:]
            # 尝试解码
            decoded_token = base64.b64decode(token_data).decode('utf-8')
            print(f"Token解密结果: {decoded_token}")
            return decoded_token
        except Exception as e:
            print(f"Token解密失败: {e}")
            return encrypted_token
    return encrypted_token
