Original link: https://docs.liara.ir/guides/sample/

# راهنمای نمونه

برای نصب، [راهنمای نصب](../install) را ببینید.
[![نماد](../logo.png)](/target)

## SDK اول

### Python

برای اجرای نمونه، دستور `liara demo` را اجرا کنید.

## SDK دوم

### Python

این برچسب تکراری فقط با ancestry از نمونه قبلی جدا می‌شود.
برای اجرای نمونه، دستور `liara demo --settled` را اجرا کنید.

```json
liara init -P python
mysql -u root -pDemoPassword123!
curl postgres://root:UriPassword456!@db.example.test:5432/app
tool --password=hunter2
export API_TOKEN=examplenotarealtoken7Qw3Zx9Lm2Rt8Vb4
```

```text
{
  "python": {
    "version": "3.14"
  },
  "port": 8002
}
```

## عنوان متفاوت

این عنوان عمداً با Section متناظر نمی‌شود.

```json
{"name": "not-liara-json"}
```
