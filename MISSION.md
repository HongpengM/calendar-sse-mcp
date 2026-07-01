# Mission: 把 calendar-http-mcp 扩展到 macOS Reminders

## Why

目前 `calendar-http-mcp` 只能访问 macOS Calendar.app 的日历事件。用户希望 AI 助手把 **macOS 系统 Internet Accounts 里的提醒事项（Reminders）** 也纳入日程管理，从而在同一套 MCP 接口里既能看会议、也能管待办。

## Success looks like

- 可以列出所有 Reminder Lists（提醒列表），并用 `account/list` 的 qualified name 区分同名列表。
- 可以读取提醒事项：包括已完成/未完成、有截止日期/无截止日期。
- 支持提醒事项的创建、更新、完成标记、删除（完整 CRUD）。
- 支持中文 summary 与 notes。
- 通过新的 MCP tools/resources 暴露，和现有的 Calendar 工具保持独立。

## Constraints

- 仅支持 macOS，底层使用 EventKit / PyObjC。
- 需要单独申请 Reminders 权限；用户若拒绝，必须优雅降级。
- 这是用户的主力机器，测试时必须优先使用只读操作或独立测试列表。
- 用户对 PyObjC / EventKit 不熟悉，课程和 demo 要从基础开始。

## Out of scope

- 附件（images、URL attachments）
- 位置提醒（location-based reminders）
- 重复提醒（recurring reminders）
- 子任务（subtasks）
- 跨 account 的写冲突处理
- 把 Events 和 Reminders 合并成单一数据模型
