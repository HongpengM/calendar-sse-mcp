# calendar-http-mcp

[English](README.md) | [中文](README_CN.md) | [GitHub](https://github.com/HongpengM/calendar-http-mcp)

一个用于与 macOS 日历交互的 [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) 服务器。

## 功能特性

- 从 macOS 日历应用列出所有日历
- 从特定日历获取事件
- 按日期范围筛选事件
- 创建、更新和删除日历事件
- 通过文本查询搜索事件
- **列出并管理 macOS 提醒事项列表和提醒**
- **创建、更新、完成和删除提醒事项**
- 为 AI 助手提供 MCP 资源和工具
- 包含常见操作的提示模板
- 全面的命令行界面，支持所有操作
- 内置启动代理支持，可在后台运行
- JSON API 端点，支持程序化访问
- 使用 dateparser 库进行稳健的日期解析
- 使用 Pydantic v2 进行数据验证
- 动态启动代理检测和安装

## 系统要求

- macOS（在 macOS 14 Sonoma 及以上版本测试）
- Python 3.10 或更新版本
- 已设置至少一个日历的日历应用
- 已设置至少一个列表的提醒事项应用（使用提醒功能时）

## 安装

### 从源代码安装

克隆仓库并安装：

```bash
git clone https://github.com/HongpengM/calendar-http-mcp.git # 或者你的分叉版本
cd calendar-http-mcp
pip install -e .
```

### 使用 uv 安装

你可以使用 [uv](https://github.com/astral-sh/uv)（一个快速的 Python 包安装器）直接安装：

```bash
uv pip install git+https://github.com/HongpengM/calendar-http-mcp.git
```

注意：这个包将来会在 PyPI 上可用。

```bash 
uv pip install calendar-http-mcp
```

## 运行服务器

### 使用 `uvx` 安装启动代理并运行命令

安装和运行日历服务最简单的方法是使用 uvx：

```bash
# 使用默认设置安装服务器作为启动代理（端口 27212）
uvx --from calendar-http-mcp calendar-mcp server install

# 自定义安装
uvx --from calendar-http-mcp calendar-mcp server install --port 5000 --logdir ~/logs

# 在端口 27213 上安装开发服务器
uvx --from calendar-http-mcp calendar-mcp server install --dev

# 启动服务器（如果尚未运行）
uvx --from calendar-http-mcp calendar-mcp server start

# 停止服务器
uvx --from calendar-http-mcp calendar-mcp server stop

# 重启服务器
uvx --from calendar-http-mcp calendar-mcp server restart

# 查看服务器日志
uvx --from calendar-http-mcp calendar-mcp server logs
uvx --from calendar-http-mcp calendar-mcp server logs --level error  # 仅显示错误日志

# 卸载服务器
uvx --from calendar-http-mcp calendar-mcp server uninstall

# 直接在前台运行服务器（用于测试）
uvx --from calendar-http-mcp calendar-mcp server run
```

安装过程：
1. 设置启动代理以在后台运行服务器
2. 配置为登录时自动启动
3. 使服务器可通过 http://localhost:27212 访问（默认）

### 从全局安装的包或仓库运行

或者，你也可以从 pip 安装的包或本地仓库运行另一个实例。首先安装服务器：


```bash

# 首先安装服务器 
pip install -e . # 在你的包仓库中，安装包（如果在 PATH 中设置了 pip 包，你将拥有 `calendar-mcp` 作为 shell 命令）
calendar-mcp server install # 这将服务器安装为启动代理

# 然后你可以运行命令行命令
calendar-mcp cli --help
```

如果你不想在全局空间安装包，你也可以直接从仓库运行

```bash

python -m src.calendar_http_mcp server install # 这不会在全局安装包

python -m src.calendar_http_mcp cli --help
```


## Claude 配置

要将此日历服务添加到 Claude，请创建以下 JSON 配置：

```json
{
  "schema_version": "v1",
  "name": "Calendar",
  "description": "访问和管理 macOS 日历应用中的事件",
  "provider_uri": "http://localhost:27212",
  "provider_type": "mcp_server",
  "tools": [
    {
      "name": "list_all_calendars",
      "description": "列出日历应用中的所有可用日历"
    },
    {
      "name": "search_events",
      "description": "通过查询、日历名称和日期范围在日历应用中搜索事件"
    },
    {
      "name": "create_calendar_event",
      "description": "在日历应用中创建新事件"
    },
    {
      "name": "update_calendar_event",
      "description": "更新日历应用中的现有事件"
    },
    {
      "name": "delete_calendar_event",
      "description": "从日历应用中删除事件"
    },
    {
      "name": "list_all_reminder_lists",
      "description": "列出提醒事项应用中的所有可用提醒列表（包含账户来源的限定名）"
    },
    {
      "name": "search_reminders",
      "description": "通过查询、列表名称和日期范围在提醒事项应用中搜索提醒"
    },
    {
      "name": "create_reminder",
      "description": "在已有的提醒事项列表中创建新提醒"
    },
    {
      "name": "update_reminder",
      "description": "更新提醒事项应用中的现有提醒"
    },
    {
      "name": "complete_reminder",
      "description": "将提醒事项应用中的现有提醒标记为已完成"
    },
    {
      "name": "delete_reminder",
      "description": "从提醒事项应用中删除提醒"
    }
  ]
}
```

将此保存为 `calendar-mcp.json` 并添加到你的 Claude 设置中。

## 命令行使用

该包提供全面的命令行界面：

```bash
# 使用 uvx（推荐）
uvx --from calendar-http-mcp calendar-mcp [command] [options]

# 或直接通过模块
python -m calendar_http_mcp [command] [options]
```

该工具提供两个主要子命令：
- `cli`：用于直接日历操作（创建/更新事件、搜索等）
- `server`：用于管理服务器（安装、启动、停止、查看日志等）

### 管理服务器

```bash
# 安装并启动启动代理
uvx --from calendar-http-mcp calendar-mcp server install

# 在安装期间自定义端口和日志目录
uvx --from calendar-http-mcp calendar-mcp server install --port 5000 --logdir ~/logs

# 在端口 27213 上安装开发服务器
uvx --from calendar-http-mcp calendar-mcp server install --dev

# 启动服务器（如果尚未运行）
uvx --from calendar-http-mcp calendar-mcp server start

# 停止服务器
uvx --from calendar-http-mcp calendar-mcp server stop

# 重启服务器
uvx --from calendar-http-mcp calendar-mcp server restart

# 查看服务器日志
uvx --from calendar-http-mcp calendar-mcp server logs
uvx --from calendar-http-mcp calendar-mcp server logs --level error  # 仅显示错误日志

# 卸载服务器
uvx --from calendar-http-mcp calendar-mcp server uninstall

# 直接在前台运行服务器（用于测试）
uvx --from calendar-http-mcp calendar-mcp server run
```

### 管理日历事件

使用 `cli` 子命令进行直接日历操作：

```bash
# 列出所有日历
uvx --from calendar-http-mcp calendar-mcp cli calendars

# 连接到端口 27213 上的开发服务器
uvx --from calendar-http-mcp calendar-mcp cli --dev calendars

# 从日历获取事件
uvx --from calendar-http-mcp calendar-mcp cli events "Work"

# 创建新事件
uvx --from calendar-http-mcp calendar-mcp cli create --event "团队会议" --cal "Work" --start "10:00" --duration "1h"

# 使用灵活的日期/时间格式创建事件
uvx --from calendar-http-mcp calendar-mcp cli create --event "与约翰共进午餐" --cal "个人" \
  --date "下周一" --start "12pm" --duration "1.5 hours" \
  --location "乔的餐厅" --description "讨论项目"

# 更新事件
uvx --from calendar-http-mcp calendar-mcp cli update "Work" "EVENT_ID" --summary "更新的会议"

# 删除事件
uvx --from calendar-http-mcp calendar-mcp cli delete "Work" "EVENT_ID"

# 搜索事件
uvx --from calendar-http-mcp calendar-mcp cli search "会议" --calendar "Work" --start-date "下周一" --duration "7d"
```

更多详情，请参阅 [CLI 工具文档](docs/cli_tools.md)。

### 管理提醒事项

使用 `cli` 子命令进行直接提醒事项操作：

```bash
# 列出所有提醒列表（限定名包含账户来源）
uvx --from calendar-http-mcp calendar-mcp cli reminder-lists

# 从特定列表获取提醒（默认范围：过去3天 ~ 未来7天 + 无截止日期）
uvx --from calendar-http-mcp calendar-mcp cli reminders "reminders:iCloud/Tasks"

# 创建新提醒
uvx --from calendar-http-mcp calendar-mcp cli create-reminder \
  --list "reminders:iCloud/Tasks" \
  --title "买牛奶" \
  --due-date "明天上午10点" \
  --notes "全脂牛奶"

# 完成提醒
uvx --from calendar-http-mcp calendar-mcp cli complete-reminder \
  "reminders:iCloud/Tasks" "REMINDER_ID"

# 更新提醒
uvx --from calendar-http-mcp calendar-mcp cli update-reminder \
  "reminders:iCloud/Tasks" "REMINDER_ID" \
  --title "买牛奶和鸡蛋" \
  --due-date "2026-07-02 18:00"

# 删除提醒
uvx --from calendar-http-mcp calendar-mcp cli delete-reminder \
  "reminders:iCloud/Tasks" "REMINDER_ID"
```

## 日历应用和提醒事项应用权限

首次运行服务器并尝试访问日历应用或提醒事项应用时，macOS 会提示你授予权限。你必须授予这些权限才能使脚本正常工作。

1. 出现提示时，点击"好"以允许访问
2. 稍后检查或修改权限，请转到：
   - 系统设置 > 隐私与安全 > 提醒事项（用于提醒事项访问）
   - 系统设置 > 隐私与安全 > 自动化
   - 确保 Python/终端具有控制日历应用和提醒事项应用的权限

如果提醒事项访问被拒绝，相关的 MCP 工具和 CLI 命令会返回清晰的错误信息，说明如何在系统设置中开启访问权限。

## 隐私警告和免责声明

**重要**：此软件需要完全访问你的 macOS 日历应用、提醒事项应用及其所有数据。请注意以下事项：

- 运行此软件时，macOS 会提示你授予日历应用和提醒事项应用对 `uv`、Python 或终端应用程序的访问权限
- 授予此权限将使应用程序能够完全读写访问你的所有日历数据和提醒数据
- 所有日历事件和提醒事项，包括潜在的敏感信息（会议、约会、个人任务），都将可被此软件访问
- 任何获得此访问权限的应用程序都可能读取、修改或删除你的日历事件和提醒事项

通过安装和使用此软件，你确认：

1. 你了解正在授予的权限范围
2. 你接受涉及的潜在隐私和安全风险
3. 你有责任审查源代码或信任开发者
4. 不提供有关安全性、隐私或数据完整性的保证

如果你对这些权限感到不适，请不要继续安装。

## API 参考

### MCP 资源

- `calendars://list` - 列出所有可用日历
- `calendar://{name}` - 获取有关特定日历的信息
- `events://{calendar_name}` - 获取日历中的所有事件
- `events://{calendar_name}/{start_date}/{end_date}` - 获取日期范围内的事件
- `event://{calendar_name}/{event_id}` - 通过 ID 获取特定事件
- `reminder-lists://list` - 列出所有可用提醒列表
- `reminders://{calendar_name}` - 从特定提醒列表获取提醒

### JSON API 端点

详细信息请参阅 [API 端点文档](docs/api_endpoints.md)。

- `api://calendars` - 获取所有日历作为标准化 JSON 响应
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
- `list_all_reminder_lists()` - 列出所有可用提醒列表
- `search_reminders(query, calendar_name?, start_date?, end_date?)` - 搜索提醒
- `create_reminder(calendar_name, title, due_date?, notes?, priority?)` - 创建新提醒
- `update_reminder(reminder_id, calendar_name, title?, due_date?, notes?, priority?, completed?)` - 更新提醒
- `complete_reminder(reminder_id, calendar_name)` - 将提醒标记为已完成
- `delete_reminder(reminder_id, calendar_name)` - 删除提醒

### MCP 提示

- `create_event_prompt(calendar_name, summary, date?, start_time?, end_time?, duration_minutes?, location?, description?)` - 创建新事件的提示
- `search_events_prompt(query, calendar_name?, start_date?, end_date?)` - 搜索事件的提示

## 文档

- [启动代理设置](docs/launch_agent_setup.md) - 如何使用 `server` 命令将服务器作为后台服务运行。
- [CLI 工具](docs/cli_tools.md) - `calendar-mcp` 的全面命令行工具参考。
- [日期处理](docs/date_handling.md) - 有关使用 dateparser 进行灵活日期解析的信息

## 日期解析

此包使用 `dateparser` 库进行稳健的日期解析，提供以下功能：

- 自然语言日期解析（"明天"、"下周"等）
- 支持相对日期（"3天后"）
- 多种日期格式（MM/DD/YYYY、YYYY-MM-DD 等）
- 时区感知

支持的日期格式示例：
- "2023-05-15"（ISO 格式）
- "2023年5月15日"（自然语言）
- "明天下午3点"（带时间的相对日期）
- "下周一"（星期参考）
- "05/15/2023"（美国格式）
- "15/05/2023"（欧洲格式）

## 数据验证

该包使用 Pydantic v2 进行数据验证，提供：

- 类型检查和验证
- 自定义验证器
- JSON 模式生成
- 序列化/反序列化
- 验证失败的适当错误消息

## 未来增强功能

- 支持 CalDAV 访问远程日历
- 支持重复事件
- 日历共享功能
- 支持与会者和邀请
- 即将发生的事件通知

## 贡献

欢迎贡献！请随时提交 Pull Request。

## 许可证

此项目根据 MIT 许可证授权 - 有关详细信息，请参阅 LICENSE 文件。
