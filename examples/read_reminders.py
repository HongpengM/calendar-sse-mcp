"""最小只读脚本：列出 macOS Reminder Lists 和 Reminders。

这是第 1 课的配套 demo。它不会创建、修改或删除任何提醒事项。
运行方式：
    python examples/read_reminders.py

第一次运行会弹出 macOS 权限框，询问是否允许终端访问“提醒事项”。
"""
import sys
import datetime
from Foundation import NSRunLoop, NSDefaultRunLoopMode, NSDate, NSCalendar
from EventKit import EKEventStore, EKEntityTypeReminder


def nsdate_to_iso(ns_date):
    """把 NSDate 转成 ISO 字符串。"""
    if ns_date is None:
        return None
    ts = ns_date.timeIntervalSince1970()
    dt = datetime.datetime.fromtimestamp(ts)
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def due_date_from_reminder(reminder):
    """读取 reminder 的 dueDateComponents 并转成 ISO 字符串。"""
    components = reminder.dueDateComponents()
    if components is None:
        return None
    calendar = NSCalendar.currentCalendar()
    ns_date = calendar.dateFromComponents_(components)
    return nsdate_to_iso(ns_date)


def request_reminder_access(store):
    """请求 Reminders 权限并等待用户响应。"""
    result = {"granted": False, "done": False}

    def callback(granted, error):
        result["granted"] = granted
        result["done"] = True
        if error:
            print(f"授权错误: {error}", file=sys.stderr)

    store.requestAccessToEntityType_completion_(EKEntityTypeReminder, callback)

    limit = NSDate.dateWithTimeIntervalSinceNow_(15.0)
    while not result["done"]:
        NSRunLoop.currentRunLoop().runMode_beforeDate_(
            NSDefaultRunLoopMode, limit
        )
    return result["granted"]


def main():
    store = EKEventStore.alloc().init()

    if not request_reminder_access(store):
        print("未获得 Reminders 权限。", file=sys.stderr)
        sys.exit(1)

    lists = store.calendarsForEntityType_(EKEntityTypeReminder)
    print(f"找到 {len(lists)} 个 Reminder List")

    predicate = store.predicateForRemindersInCalendars_(lists)
    fetched = {"done": False, "items": []}

    def on_reminders(reminders):
        fetched["items"] = list(reminders or [])
        fetched["done"] = True

    store.fetchRemindersMatchingPredicate_completion_(predicate, on_reminders)

    limit = NSDate.dateWithTimeIntervalSinceNow_(10.0)
    while not fetched["done"]:
        NSRunLoop.currentRunLoop().runMode_beforeDate_(
            NSDefaultRunLoopMode, limit
        )

    for reminder in fetched["items"]:
        title = reminder.title()
        completed = reminder.isCompleted()
        due = due_date_from_reminder(reminder)
        cal = reminder.calendar().title()
        print(f"[{cal}] {title} | completed={completed} | due={due}")


if __name__ == "__main__":
    main()
