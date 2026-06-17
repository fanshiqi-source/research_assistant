## 描述
使用Tavily搜索引擎搜索网络信息，获取最新资讯和相关链接

## 适用场景
- **只用于"搜索"步骤**
- 需要获取最新新闻或趋势信息时
- 需要查找特定主题的详细资料时
- 需要验证事实或获取数据支持时

## 不适用场景
- "阅读"步骤：应使用web_fetch
- "整理"步骤：不需要搜索
- "报告"步骤：应使用report_gen

## 输入参数
| 参数名 | 类型 | 说明 |
|--------|------|------|
| query | string | 搜索关键词，必填 |

## 执行步骤
1. 构建搜索请求对象，包含query参数
2. 调用Tavily API发送POST请求
3. 接收JSON响应并解析
4. 提取answer字段作为摘要
5. 提取results中的url字段作为相关链接
6. 返回结构化结果

## 输出格式
```json
{
    "success": true,
    "answer": "搜索结果的自然语言摘要",
    "urls": ["https://example.com/article1", "https://example.com/article2"]
}
```