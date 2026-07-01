# calendar-http-mcp Reminders 扩展资源

## Knowledge

- [Apple: Creating events and reminders](https://developer.apple.com/documentation/eventkit/creating-events-and-reminders)
  官方 EventKit 事件与提醒事项创建/修改/删除语义。用于：理解 `EKReminder` 生命周期、`saveReminder:commit:error:`、`isCompleted` 与 `completionDate` 的关系。

- [Apple: EKReminder class reference](https://developer.apple.com/documentation/eventkit/ekreminder)
  官方 `EKReminder` 属性清单。用于：查询 `dueDateComponents`、`startDateComponents`、`isCompleted`、`completionDate`、`priority`、`notes` 等字段。

- [Apple: Retrieving events and reminders](https://developer.apple.com/documentation/eventkit/retrieving-events-and-reminders)
  官方通过 predicate 获取事件与提醒事项的文档。用于：理解 `fetchRemindersMatchingPredicate:completion:`、`predicateForRemindersInCalendars:`、按完成状态/日期范围查询。

- [Apple: EKSource class reference](https://developer.apple.com/documentation/eventkit/eksource)
  官方 EventKit account/source 抽象。用于：通过 `source.title`、`sourceIdentifier` 区分不同 account（iCloud / Google / Exchange）下的同名列表。

- [Apple: EKCalendar.source property](https://developer.apple.com/documentation/eventkit/ekcalendar/source)
  官方说明 calendar 属于哪个 source/account。用于：构造 `account/list` qualified name，解决跨 account 同名 reminder list 冲突。

- [Accessing Reminders with EventKit (Part 1) — kykim](https://kykim.github.io/blog/2012/10/09/accessing-reminders-with-eventkit-part-1/)
  一篇较老但概念清晰的 EventKit Reminders 入门博客。用于：理解 `EKEventStore`、`EKCalendar` 同时代表 calendar 与 reminder list、`EKReminder` 与 `EKEvent` 同继承自 `EKCalendarItem` 等核心概念。

- [Creating reminder lists with EventKit from your app — Create with Swift](https://www.createwithswift.com/creating-reminder-lists-with-eventkit-from-your-app/)
  现代 Swift 示例，演示列出 reminder lists、创建列表、添加 reminder、处理 `EKSource`。用于：对照 PyObjC 写法，理解 source 优先选择策略（local / CalDAV）。

## Wisdom (Communities)

- [Apple Developer Forums — EventKit](https://developer.apple.com/forums/tags/eventkit/)
  官方论坛，适合提问权限、predicate 行为、source 处理等底层问题。

- [Stack Overflow — [eventkit] tag](https://stackoverflow.com/questions/tagged/eventkit)
  大量 EventKit 实际问题与代码示例。注意甄别 iOS-only 与 macOS 差异。

- [r/MacOSProgramming](https://www.reddit.com/r/MacOSProgramming/)
  macOS 原生开发讨论区，适合分享 PyObjC / EventKit CLI 经验。

## Gaps

- 缺少一份权威的 **PyObjC + EventKit Reminders** 示例。现有资源多为 Swift/Objective-C，需要我们在课程/demo 中自己翻译并验证 PyObjC 桥接代码。
