import requests
from typing import List, Dict, Any
import config


class FeishuTable:
    """
    飞书多维表格操作类
    """
    def __init__(self, app_token: str, table_id: str, app_id: str = None, app_secret: str = None):
        """
        初始化飞书多维表格操作类
        :param app_id: 飞书应用ID，如果为None则使用config中的配置
        :param app_secret: 飞书应用密钥，如果为None则使用config中的配置
        """
        self.app_id = app_id or config.FEISHU_APP_ID
        self.app_secret = app_secret or config.FEISHU_APP_SECRET
        self.base_url = "https://open.feishu.cn/open-apis"
        self._tenant_access_token = None
        self.app_token = app_token
        self.table_id = table_id

    def get_tenant_access_token(self) -> str:
        """
        获取租户访问令牌
        :return: 租户访问令牌
        """
        if self._tenant_access_token:
            return self._tenant_access_token

        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        response = requests.post(url, json=payload)
        result = response.json()

        if result.get("code") == 0:
            self._tenant_access_token = result.get("tenant_access_token")
            return self._tenant_access_token
        else:
            raise Exception(f"获取租户访问令牌失败: {result}")

    def get_headers(self) -> Dict[str, str]:
        """
        获取请求头
        :return: 请求头字典
        """
        return {
            "Authorization": f"Bearer {self.get_tenant_access_token()}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, url: str, data: Dict = None, params: Dict = None) -> Dict:
        payload = {
            'method': method.upper(),
            'url': url,
            'json': data,
            'params': params,
        }

        response = requests.request(**payload, headers=self.get_headers())
        result = response.json()
        if result.get("code") == 0:
            return result

        self._tenant_access_token = None
        response = requests.request(**payload, headers=self.get_headers())
        return response.json()

    def get_app_info(self) -> Dict:
        """
        获取多维表格应用信息
        :return: 应用信息
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}"
        result = self._request('get', url)

        if result.get("code") == 0:
            return result.get("data", {})
        else:
            raise Exception(f"获取多维表格应用信息失败: {result}")

    def get_table_meta(self) -> Dict:
        """
        获取数据表元数据
        :param app_token: 多维表格应用token
        :param table_id: 数据表ID
        :return: 数据表元数据
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}"
        result = self._request('get', url)

        if result.get("code") == 0:
            return result.get("data", {})
        else:
            raise Exception(f"获取数据表元数据失败: {result}")

    def get_fields(self, app_token: str, table_id: str) -> List[Dict]:
        """
        获取数据表字段列表
        :param app_token: 多维表格应用token
        :param table_id: 数据表ID
        :return: 字段列表
        """
        url = f"{self.base_url}/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
        result = self._request('get', url)

        if result.get("code") == 0:
            return result.get("data", {}).get("items", [])
        else:
            raise Exception(f"获取字段列表失败: {result}")

    def create_field(self, field_name: str, field_type: str,
                     field_property: Dict = None) -> Dict:
        """
        创建字段
        :param field_name: 字段名称
        :param field_type: 字段类型（如 text, number, select, multiSelect 等）
        :param field_property: 字段属性
        :return: 创建的字段信息
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        payload = {
            "field_name": field_name,
            "type": field_type
        }

        if field_property:
            payload["property"] = field_property

        result = self._request('post', url, payload)
        if result.get("code") == 0:
            return result.get("data", {})
        else:
            raise Exception(f"创建字段失败: {result}")

    def update_field(self, field_id: str, field_name: str, field_type: int,
                     field_property: Dict = None) -> Dict:
        """
        更新字段
        https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/update
        :param field_id: 字段ID
        :param field_name: 字段名称
        :param field_type: 字段类型
        :param field_property: 字段属性
        :return: 更新后的字段信息
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields/{field_id}"
        payload = {
            "field_name": field_name,
            "type": field_type
        }

        if field_property:
            payload["property"] = field_property

        result = self._request('put', url, payload)
        if result.get("code") == 0:
            return result.get("data", {})
        else:
            raise Exception(f"更新字段失败: {result}")

    def add_option_values(self, view_id, field_id: str, field_name: str, option_values: List[str]) -> Dict:
        """
        为选择类型字段添加选项
        :param view_id: 视图ID
        :param field_id: 字段ID
        :param field_name: 字段名称
        :param option_values: 要添加的选项值列表
        :return: 更新后的字段信息
        """
        # 获取字段信息
        fields = self.list_fields(view_id)
        field = next((f for f in fields["items"] if f["field_id"] == field_id), None)

        if not field:
            raise Exception(f"字段 {field_id} 不存在")

        # 获取现有选项
        current_options = field.get("property", {}).get("options", [])
        current_options.extend([{'name': v} for v in option_values])

        # 更新字段属性
        return self.update_field(
            field_id, field_name, field['type'],
            field_property={"options": current_options}
        )

    def get_records(self, view_id: str = None, page_size: int = 100,
                    page_token: str = None) -> Dict:
        """
        获取记录列表
        :param view_id: 视图ID，可选
        :param page_size: 每页记录数，最大为 100
        :param page_token: 分页标记，首次调用不填
        :return: 记录列表信息
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        params = {"page_size": page_size}

        if view_id:
            params["view_id"] = view_id

        if page_token:
            params["page_token"] = page_token

        result = self._request('get', url, params=params)
        if result.get("code") == 0:
            return result.get("data", {})
        else:
            raise Exception(f"获取记录列表失败: {result}")

    def create_record(self, fields: Dict[str, Any]) -> Dict:
        """
        创建记录
        :param fields: 字段值，key为字段名或ID，value为字段值
        :return: 创建的记录信息
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        payload = {
            "fields": fields
        }

        result = self._request('post', url, payload)
        if result.get("code") == 0:
            return result.get("data", {})
        else:
            raise Exception(f"创建记录失败: {result}")

    def batch_create_records(self, records: List[Dict[str, Any]]) -> Dict:
        """
        批量创建记录
        :param records: 记录列表，每个记录是一个字典，key为字段名或ID，value为字段值
        :return: 创建的记录信息
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/batch_create"
        records_data = [{"fields": record} for record in records]
        payload = {
            "records": records_data
        }

        result = self._request('post', url, payload)
        if result.get("code") == 0:
            return result.get("data", {})
        else:
            raise Exception(f"批量创建记录失败: {result}")

    def update_record(self, record_id: str, fields: Dict[str, Any]) -> Dict:
        """
        更新记录
        :param record_id: 记录ID
        :param fields: 字段值，key为字段名或ID，value为字段值
        :return: 更新后的记录信息
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}"
        payload = {
            "fields": fields
        }

        result = self._request('put', url, payload)
        if result.get("code") == 0:
            return result.get("data", {})
        else:
            raise Exception(f"更新记录失败: {result}")

    def delete_record(self, record_id: str) -> bool:
        """
        删除记录
        :param record_id: 记录ID
        :return: 是否成功
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}"
        result = self._request('delete', url)
        if result.get("code") == 0:
            return True
        else:
            raise Exception(f"删除记录失败: {result}")

    def get_field(self, view_id: str, field_name) -> Dict:
        fields = self.list_fields(view_id)
        return next((f for f in fields["items"] if f["field_name"] == field_name), {})

    def list_fields(self, view_id: str = None,  page_size: int = 200,
                    page_token: str = None) -> Dict:
        """
        获取数据表字段列表，支持分页和视图筛选
        :param view_id: 视图ID，可选
        :param page_size: 每页字段数，默认100，最大值100
        :param page_token: 分页标记，首次调用不填
        :return: 包含字段列表和分页信息的字典
        """
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/fields"
        params = {"page_size": page_size}

        if view_id:
            params["view_id"] = view_id

        if page_token:
            params["page_token"] = page_token

        result = self._request('get', url, params=params)
        if result.get("code") == 0:
            return result.get("data", {})
        else:
            raise Exception(f"获取字段列表失败: {result}")

# 使用示例
if __name__ == "__main__":
    # 初始化飞书表格操作类
    feishu = FeishuTable('G1rDbcKyNaL1bAso3l8cImdYntX', 'tblpA7YT2FsTls21')

    # 示例：添加多选选项
    # try:
    #     # 首先需要获取字段ID
    #     fields = feishu.get_fields(
    #         app_token="bascnQMVnnn4t67IMnl8upRCxpg",
    #         table_id="tblUX3FwPfTxnWcJ"
    #     )
    #     
    #     # 找到字段ID
    #     field_id = None
    #     for field in fields:
    #         if field.get("field_name") == "状态":
    #             field_id = field.get("field_id")
    #             break
    #     
    #     if field_id:
    #         feishu.add_option_values(
    #             app_token="bascnQMVnnn4t67IMnl8upRCxpg",
    #             table_id="tblUX3FwPfTxnWcJ",
    #             field_id=field_id,
    #             option_values=["进行中", "已完成", "已取消"]
    #         )
    #         print("添加选项成功")
    #     else:
    #         print("未找到字段")
    # except Exception as e:
    #     print(f"添加选项失败: {e}")

    field = feishu.get_field('vewNTuIRsZ', '分类')
    print(field)
    # feishu.add_option_values('vewNTuIRsZ', 'fld0K2fHiH', '分类', ['分类3'])

    # feishu.update_field('G1rDbcKyNaL1bAso3l8cImdYntX', 'tblpA7YT2FsTls21','fld0K2fHiH','状态', 4, {
    #     "options": [
    #         # 之前有的需要带上原来的id，否则表中的数据会被重置
    #         {'color': 0, 'id': 'optjS6N5CE', 'name': '进行中'},
    #         {'color': 1, 'id': 'optiF3pYw1', 'name': '已完成'},
    #         {'color': 2, 'name': 'test'},
    #     ]
    # })

    # # 示例：添加单条记录
    # try:
    #     feishu.create_record(
    #         app_token="bascnQMVnnn4t67IMnl8upRCxpg",
    #         table_id="tblUX3FwPfTxnWcJ",
    #         fields={
    #             "标题": "测试任务",
    #             "状态": ["进行中", "已完成"],  # 多选值
    #             "负责人": "张三",
    #             "截止日期": "2024-03-20"
    #         }
    #     )
    #     print("添加记录成功")
    # except Exception as e:
    #     import traceback
    #     traceback.print_exc()
    #     print(f"添加记录失败: {e}")

    # # 示例：批量添加记录
    # try:
    #     feishu.batch_create_records(
    #         app_token="bascnQMVnnn4t67IMnl8upRCxpg",
    #         table_id="tblUX3FwPfTxnWcJ",
    #         records=[
    #             {
    #                 "标题": "任务1",
    #                 "状态": ["进行中"],
    #                 "负责人": "张三",
    #                 "截止日期": "2024-03-20"
    #             },
    #             {
    #                 "标题": "任务2",
    #                 "状态": ["已完成"],
    #                 "负责人": "李四",
    #                 "截止日期": "2024-03-21"
    #             }
    #         ]
    #     )
    #     print("批量添加记录成功")
    # except Exception as e:
    #     print(f"批量添加记录失败: {e}")
