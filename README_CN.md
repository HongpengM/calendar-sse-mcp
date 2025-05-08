# Calendar SSE MCP

一个 [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) 服务器，用于通过 AppleScript 与 macOS Calendar.app 交互。

## 功能特点

- 列出 macOS Calendar.app 中的所有日历
- 获取特定日历的事件
- 按日期范围筛选事件
- 创建、更新和删除日历事件
- 通过文本查询搜索事件
- 为 AI 助手提供 MCP 资源和工具
- 包含常见操作的提示模板
- 全面的命令行界面，支持所有操作
- 内置启动代理支持后台运行
- 用于编程访问的 JSON API 端点
- 使用 dateparser 库进行强大的日期解析
- 使用 Pydantic v2 进行数据验证
- 动态启动代理检测和安装

## 系统要求

- macOS（已在 macOS 14 Sonoma 及以上版本测试）
- Python 3.10 或更新版本
- Calendar.app 至少设置了一个日历

## 安装方法

### 从源代码安装

克隆仓库并安装：

```bash
git clone https://github.com/HongpengM/calendar-sse-mcp.git # 或者你的分叉版本
cd calendar-sse-mcp
pip install -e .
```

### 使用 uv 安装

你可以直接使用 [uv](https://github.com/astral-sh/uv)（一个快速的 Python 包安装工具）进行安装：

```bash
uv pip install git+https://github.com/HongpengM/calendar-sse-mcp.git
```

注意：此包将来会在 PyPI 上提供。

```bash 
uv pip install calendar-sse-mcp
```

## 运行服务器

### 使用 `uvx` 安装启动代理并运行命令

安装和运行日历服务的最简单方法是使用 uvx：

```bash
# 使用默认设置（端口 27212）将服务器安装为启动代理
uvx --from calendar-sse-mcp calendar-sse server install

# 自定义安装
uvx --from calendar-sse-mcp calendar-sse server install --port 5000 --logdir ~/logs

# 在端口 27213 上安装开发服务器
uvx --from calendar-sse-mcp calendar-sse server install --dev

# 启动服务器（如果尚未运行）
uvx --from calendar-sse-mcp calendar-sse server start

# 停止服务器
uvx --from calendar-sse-mcp calendar-sse server stop

# 重启服务器
uvx --from calendar-sse-mcp calendar-sse server restart

# 检查服务器日志
uvx --from calendar-sse-mcp calendar-sse server logs
uvx --from calendar-sse-mcp calendar-sse server logs --level error  # 仅显示错误日志

# 卸载服务器
uvx --from calendar-sse-mcp calendar-sse server uninstall

# 直接在前台运行服务器（用于测试）
uvx --from calendar-sse-mcp calendar-sse server run
```

安装过程：
1. 设置启动代理在后台运行服务器
2. 配置登录时自动启动
3. 默认情况下，服务器在 http://localhost:27212 上可访问

### 从全局安装的包或仓库运行

或者，你也可以从通过 pip 安装或本地仓库运行另一个实例。首先安装服务器：

```bash
# 先安装服务器
pip install -e . # 在你的包仓库中，安装该包（如果你在 PATH 中设置了 pip 包，你将拥有 `calendar-mcp` 作为 shell 命令）
calendar-mcp server install # 这将安装服务器作为启动代理

# 然后你可以运行命令行命令
calendar-mcp cli --help
```

如果你不想在全局空间安装包，你也可以直接从仓库运行

```bash
python -m src.calendar_sse_mcp server install # 这不会在全局安装包

python -m src.calendar_sse_mcp cli --help
```

## Claude 配置

要将此日历服务添加到 Claude，请创建以下 JSON 配置：

```json
{
  "schema_version": "v1",
  "name": "Calendar",
  "description": "访问和管理 macOS Calendar.app 中的事件",
  "provider_uri": "http://localhost:27212",
  "provider_type": "mcp_server",
  "tools": [
    {
      "name": "list_all_calendars",
      "description": "列出 Calendar.app 中所有可用的日历"
    },
    {
      "name": "search_events",
      "description": "通过查询、日历名称和日期范围在 Calendar.app 中搜索事件"
    },
    {
      "name": "create_calendar_event",
      "description": "在 Calendar.app 中创建新事件"
    },
    {
      "name": "update_calendar_event",
      "description": "更新 Calendar.app 中的现有事件"
    },
    {
      "name": "delete_calendar_event",
      "description": "从 Calendar.app 中删除事件"
    }
  ]
}
```

将其保存为 `calendar-mcp.json` 并在设置中添加到 Claude。

## 命令行用法

该包提供了全面的命令行界面：

```bash
# 使用 uvx（推荐）
uvx --from calendar-sse-mcp calendar-sse [command] [options]

# 或直接使用模块
python -m calendar_sse_mcp [command] [options]
```

该工具提供两个主要子命令：
- `cli`：用于直接日历操作（创建/更新事件、搜索等）
- `server`：用于管理服务器（安装、启动、停止、查看日志等）

### 管理服务器

```bash
# 安装并启动启动代理
uvx --from calendar-sse-mcp calendar-sse server install

# 在安装期间自定义端口和日志目录
uvx --from calendar-sse-mcp calendar-sse server install --port 5000 --logdir ~/logs

# 在端口 27213 上安装开发服务器
uvx --from calendar-sse-mcp calendar-sse server install --dev

# 启动服务器（如果尚未运行）
uvx --from calendar-sse-mcp calendar-sse server start

# 停止服务器
uvx --from calendar-sse-mcp calendar-sse server stop

# 重启服务器
uvx --from calendar-sse-mcp calendar-sse server restart

# 检查服务器日志
uvx --from calendar-sse-mcp calendar-sse server logs
uvx --from calendar-sse-mcp calendar-sse server logs --level error  # 仅显示错误日志

# 卸载服务器
uvx --from calendar-sse-mcp calendar-sse server uninstall

# 直接在前台运行服务器（用于测试）
uvx --from calendar-sse-mcp calendar-sse server run
```

### 管理日历事件

使用 `cli` 子命令进行直接日历操作：

```bash
# 列出所有日历
uvx --from calendar-sse-mcp calendar-sse cli calendars

# 连接到端口 27213 上的开发服务器
uvx --from calendar-sse-mcp calendar-sse cli --dev calendars

# 获取日历中的事件
uvx --from calendar-sse-mcp calendar-sse cli events "Work"

# 创建新事件
uvx --from calendar-sse-mcp calendar-sse cli create --event "团队会议" --cal "Work" --start "10:00" --duration "1h"

# 使用灵活的日期/时间格式创建事件
uvx --from calendar-sse-mcp calendar-sse cli create --event "与约翰共进午餐" --cal "个人" \
  --date "下周一" --start "12pm" --duration "1.5小时" \
  --location "Joe's 餐厅" --description "讨论项目"

# 更新事件
uvx --from calendar-sse-mcp calendar-sse cli update "Work" "EVENT_ID" --summary "更新的会议"

# 删除事件
uvx --from calendar-sse-mcp calendar-sse cli delete "Work" "EVENT_ID"

# 搜索事件
uvx --from calendar-sse-mcp calendar-sse cli search "会议" --calendar "Work" --start-date "下周一" --duration "7d"
```

更多详情，请参阅 [CLI 工具文档](docs/cli_tools.md)。

## Calendar.app 权限

当你第一次运行服务器并尝试访问 Calendar.app 时，macOS 会提示你授予权限。你必须授予这些权限才能使脚本工作。

1. 出现提示时，点击"确定"允许访问
2. 要稍后检查或修改权限，请转到：
   - 系统设置 > 隐私与安全 > 自动化
   - 确保 Python/终端有控制 Calendar.app 的权限

## 隐私警告和免责声明

**重要提示**：此软件需要完全访问你的 macOS Calendar.app 及其所有数据。请注意以下几点：

- 当你运行此软件时，macOS 会提示你授予 `uv`、Python 或你的终端应用程序访问 Calendar.app 的权限
- 授予此权限将使应用程序完全读取和写入所有日历数据的权限
- 所有日历事件，包括潜在的敏感信息（会议、约会、个人事件）都将可被此软件访问
- 任何被授予此访问权限的应用程序都可能读取、修改或删除你的日历事件

通过安装和使用此软件，你承认：

1. 你了解所授予权限的范围
2. 你接受所涉及的潜在隐私和安全风险
3. 你有责任审查源代码或信任开发者
4. 不提供关于安全、隐私或数据完整性的任何保证

如果你对这些权限感到不舒服，请不要继续安装。

## API 参考

### MCP 资源

- `calendars://list` - 列出所有可用日历
- `calendar://{name}` - 获取有关特定日历的信息
- `events://{calendar_name}` - 获取日历中的所有事件
- `events://{calendar_name}/{start_date}/{end_date}` - 获取日期范围内的事件
- `event://{calendar_name}/{event_id}` - 通过 ID 获取特定事件

### JSON API 端点

有关详细信息，请参阅 [API 端点文档](docs/api_endpoints.md)。

- `api://calendars` - 以标准化 JSON 响应获取所有日历
- `api://events/{calendar_name}` - 以 JSON 格式获取日历中的事件
- `api://events/{calendar_name}/{start_date}/{end_date}` - 获取日期范围内的事件
- `api://events/create/{calendar_name}/{summary}/{start_date}/{end_date}` - 创建新事件
- `api://events/update/{event_id}/{calendar_name}` - 更新事件
- `api://events/delete/{event_id}/{calendar_name}` - 删除事件

### MCP 工具

- `list_all_calendars()` - 列出所有可用日历
- `search_events(query, calendar_name?, start_date?, end_date?)` - 搜索事件
- `create_calendar_event(calendar_name, summary, start_date, end_date, location?, description?)` - 创建新事件
- `update_calendar_event(event_id, calendar_name, summary?, start_date?, end_date?, location?, description?)` - 更新事件
- `delete_calendar_event(event_id, calendar_name)` - 删除事件

### MCP 提示

- `create_event_prompt(calendar_name, summary, date?, start_time?, end_time?, duration_minutes?, location?, description?)` - 创建新事件的提示
- `search_events_prompt(query, calendar_name?, start_date?, end_date?)` - 搜索事件的提示

## 文档

- [启动代理设置](docs/launch_agent_setup.md) - 如何使用 `server` 命令将服务器作为后台服务运行。
- [CLI 工具](docs/cli_tools.md) - `calendar-mcp` 的全面命令行工具参考。
- [日期处理](docs/date_handling.md) - 关于使用 dateparser 进行灵活日期解析的信息

## 日期解析

该包使用 `dateparser` 库进行强大的日期解析，它提供：

- 自然语言日期解析（"明天"、"下周"等）
- 支持相对日期（"从现在起 3 天"）
- 多种日期格式（MM/DD/YYYY、YYYY-MM-DD 等）
- 时区感知

支持的日期格式示例：
- "2023-05-15"（ISO 格式）
- "2023年5月15日"（自然语言）
- "明天下午 3 点"（相对时间）
- "下周一"（工作日参考）
- "05/15/2023"（美国格式）
- "15/05/2023"（欧洲格式）

## 数据验证

该包使用 Pydantic v2 进行数据验证，提供：

- 类型检查和验证
- 自定义验证器
- JSON schema 生成
- 序列化/反序列化
- 验证失败时的适当错误消息

## 未来增强

- CalDAV 支持，用于访问远程日历
- 重复事件支持
- 日历共享功能
- 支持与会者和邀请
- 即将到来的事件通知

## 贡献

欢迎贡献！请随时提交拉取请求。

## 许可证

该项目根据 MIT 许可证授权 - 有关详细信息，请参阅 LICENSE 文件。 