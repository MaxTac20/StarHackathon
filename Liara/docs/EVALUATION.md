# EVALUATION

Evidence for the Liara judging rubric. This checkpoint covers criterion 1, answer quality;
the remaining rubric criteria are intentionally not marked evaluated here.

**Evaluated:** 2026-08-20

## Answer-engine configuration

- Corpus source commit: `liara-cloud/docs@31f2ef7`
- Audited regenerated snapshot: 5,287 chunks from ingestion commit `57a3af8`
- Snapshot SHA-256:
  `90f96de9b3bb5147e4525fad8bcadd2febc1aaeffeed8f0fc7a69c71d92aa3ac`
- Embeddings: `qwen/qwen3-embedding-8b`, 1,024 dimensions
- Generation: `openai/gpt-5.6-luna`, high reasoning effort
- Full embedding run: 5,287 chunks, 1,506,676 tokens, 737.78 seconds,
  **$0.01506676**
- Test endpoint: `POST http://127.0.0.1:8022/api/chat`

Citation policy is structural rather than prompt-only. The model receives opaque source
IDs such as `S1`, never citation URLs. The server maps only IDs from the retrieved context
to their stored `cite_url`; unknown IDs and uncited draft lines are omitted. Inline numbers
use the same URL-deduplicated order as `data-sources`.

## Criterion 1 verdict

| Sub-criterion | Verdict | Evidence |
|---|---|---|
| Correct and relevant | Pass on the exercised cases | Persian Django answer covers both upload limit and persistence; English answer targets the exact worker-timeout page |
| Complete and practical | Pass on the exercised cases | Both answers end with a concrete verification action |
| Finds appropriate information | Pass after measured query planning | Multi-intent interleaving recovered filesystem and disk evidence that the single full query missed |
| Reduces fabricated answers | Pass | Server citation gate plus live unsupported-question refusal |
| Provides appropriate sources | Pass | Seven unique inline targets returned HTTP 200 and contained the cited claim |
| Simple and complex questions | Pass on the exercised cases | English single-intent timeout plus Persian multi-hop upload/persistence |

This is evidence for the exercised cases, not a golden-set score.

## Measured live runs

| Case | First event | Sources/reasoning | Answer start | Done | Cost |
|---|---:|---:|---:|---:|---:|
| Persian multi-hop, cache hit | 0.073 s | 8.367 s | 16.303 s | 20.089 s | $0.00147626 |
| English worker timeout | 0.073 s | 1.519 s | 7.800 s | 9.554 s | $0.00175648 |
| Unsupported laptop warranty | 0.104 s | 1.448 s | 3.186 s | 3.186 s | $0.00075291 |

The Persian cache-seed request cost $0.00220089. Its immediate identical repeat reported
3,281 cache-read input tokens and cost $0.00147626, a 32.9% measured reduction.

## Persian transcript

**Question**

> در برنامه Django فایل‌های آپلودشده بعد از deploy پاک می‌شوند؛ چطور محدودیت
> آپلود Nginx را بالا ببرم و فایل‌ها را ماندگار کنم؟

**Reasoning part**

> 12 بخش از 10 صفحه بازیابی شد؛ اکنون هر ادعا با شناسه‌های همین منابع تطبیق داده
> می‌شود.

**Answer**

### ۱) افزایش محدودیت آپلود در Nginx

در ریشه پروژه Django فایلی با نام `liara_nginx.conf` ایجاد کنید و مقدار
`client_max_body_size` را به اندازه موردنیاز تغییر دهید؛ مقدار نمونه زیر سقف آپلود را
به `250M` می‌رساند. [1](https://docs.liara.ir/paas/django/fix-common-errors/upload-limit-size/)

```nginx
client_max_body_size 250M;

location /media {
  alias /usr/src/app/media;
}

location /static {
  alias /usr/src/app/staticfiles;
}

location / {
  try_files /dev/null @django_app;
}

location ~\.sqlite3$ {
  deny all;
  error_page 403 =404 /;
}

location ~ /\.well-known {
  allow all;
}
```

پس از قرار دادن فایل در ریشه پروژه، برنامه را مجدداً در Liara مستقر کنید تا تنظیمات
Nginx اعمال شود. [1](https://docs.liara.ir/paas/django/fix-common-errors/upload-limit-size/)
[8](https://docs.liara.ir/paas/django/how-tos/customize-nginx/)

### ۲) ماندگار کردن فایل‌های آپلودی

فایل‌سیستم برنامه‌های Liara به‌صورت ReadOnly است و دایرکتوری `tmp/` تنها استثنای این
قاعده محسوب می‌شود؛ این دایرکتوری در همه پلن‌ها `100MB` فضا دارد و برای فایل‌های
آپلودی موقتی مناسب است.
[2](https://docs.liara.ir/paas/details/file-system/#tmp-directory)

برای نگهداری فایل‌های آپلودی در فضای جداگانه، یک disk با حجم دلخواه ایجاد کنید و آن را
به مسیری که برنامه برای فایل‌های Media استفاده می‌کند متصل کنید.
[2](https://docs.liara.ir/paas/details/file-system/#tmp-directory)
[5](https://docs.liara.ir/paas/disks/route/)

در مرحله دوم استقرار، نام disk و مسیر اتصال را وارد کنید؛ مسیر می‌تواند نسبی یا
absolute باشد. [5](https://docs.liara.ir/paas/disks/route/)

مسیر alias در پیکربندی Nginx نمونه، `/usr/src/app/media` است؛ بنابراین مسیر اتصال disk
و مسیر ذخیره‌سازی Media در برنامه باید با این مسیر هماهنگ باشند.
[1](https://docs.liara.ir/paas/django/fix-common-errors/upload-limit-size/)
[5](https://docs.liara.ir/paas/disks/route/)

اگر فعلاً ذخیره‌سازی موقت کافی است، می‌توانید disk را به مسیر `tmp/` متصل کنید تا فضای
این دایرکتوری افزایش یابد؛ مستندات برای افزایش فضای `tmp/` همین روش را پیشنهاد
می‌کنند. [2](https://docs.liara.ir/paas/details/file-system/#tmp-directory)

### ترتیب پیشنهادی

1. یک disk با حجم موردنیاز ایجاد کنید.
   [2](https://docs.liara.ir/paas/details/file-system/#tmp-directory)
   [7](https://docs.liara.ir/paas/disks/about/)
2. disk را در Liara Console به مسیر Media برنامه متصل کنید؛ مسیر را می‌توان نسبی یا
   absolute وارد کرد. [5](https://docs.liara.ir/paas/disks/route/)
3. در ریشه پروژه فایل `liara_nginx.conf` را با تنظیمات بالا قرار دهید و مقدار
   `client_max_body_size` را تنظیم کنید.
   [1](https://docs.liara.ir/paas/django/fix-common-errors/upload-limit-size/)
   [8](https://docs.liara.ir/paas/django/how-tos/customize-nginx/)
4. برنامه را مجدداً deploy کنید.
   [1](https://docs.liara.ir/paas/django/fix-common-errors/upload-limit-size/)
   [5](https://docs.liara.ir/paas/disks/route/)
5. برای بررسی، یک فایل بزرگ‌تر از `1MB`، مثلاً فایلی نزدیک به `250MB`، آپلود کنید و
   سپس بعد از deploy مجدد وجود همان فایل را در مسیر Media بررسی کنید.
   [1](https://docs.liara.ir/paas/django/fix-common-errors/upload-limit-size/)
   [5](https://docs.liara.ir/paas/disks/route/)

## English transcript

**Question**

> How can I raise GUNICORN_TIMEOUT for a Django app on Liara, and what should I
> verify afterward?

**Reasoning part**

> Retrieved 12 sections across 8 pages; each claim is now being checked against
> only those source IDs.

**Answer**

### Raise the timeout

1. Open your Django app's environment-variable settings in Liara.
   [1](https://docs.liara.ir/paas/django/fix-common-errors/worker-timeout/)
2. Add the variable `GUNICORN_TIMEOUT`.
   [1](https://docs.liara.ir/paas/django/fix-common-errors/worker-timeout/)
3. Set its value to the required timeout in seconds; use a value greater than `30`
   if the app needs more than 30 seconds to process a request.
   [1](https://docs.liara.ir/paas/django/fix-common-errors/worker-timeout/)
4. Save the setting and redeploy or restart the app if Liara requires it for the
   updated environment variable to take effect.
   [1](https://docs.liara.ir/paas/django/fix-common-errors/worker-timeout/)

For example, configure `GUNICORN_TIMEOUT` with a numeric value representing seconds,
rather than changing Gunicorn configuration inside Django.
[1](https://docs.liara.ir/paas/django/fix-common-errors/worker-timeout/)

### Verify afterward

- Check the app status in the Liara user panel and confirm that it is ready to use.
  [2](https://docs.liara.ir/paas/django/how-tos/create-app/)
- Review the application's behavior or logs for the request that previously timed out,
  and confirm that the `WORKER TIMEOUT` condition no longer occurs. A `WORKER TIMEOUT`
  means that a worker did not send a response within the permitted processing time and
  was stopped and restarted by Gunicorn.
  [1](https://docs.liara.ir/paas/django/fix-common-errors/worker-timeout/)
- Perform one concrete verification now: repeat the previously slow request and confirm
  that it completes without a `WORKER TIMEOUT`.
  [1](https://docs.liara.ir/paas/django/fix-common-errors/worker-timeout/)

## Refusal transcript

**Question**

> لیارا برای لپ‌تاپ‌های تولید خودش چند سال گارانتی سخت‌افزاری می‌دهد؟

**Notice**

> منابع بازیابی‌شده پاسخ قابل اتکایی برای این پرسش نداشتند؛ پاسخ بدون پشتوانه تولید
> نشد.

**Answer**

> در مستندات بازیابی‌شده‌ی لیارا پاسخ قابل اتکایی برای این پرسش پیدا نکردم. بهتر است
> نام دقیق سرویس یا پلتفرم، مسیر استقرار (`CLI`، `Console` یا `GitHub`) و متن کامل خطا
> را جست‌وجو یا در پرسش بعدی ارسال کنید.

## Citation resolution

All unique inline targets returned HTTP 200 on 2026-08-20.

| Target | Fragment | Claim checked on live page |
|---|---|---|
| Django upload limit | page | `liara_nginx.conf`, `client_max_body_size`, `250M` |
| File system | `#tmp-directory` present | `tmp/`, 100 MB, create disk, define route |
| Disk route | page | relative and absolute mount paths |
| Disk overview | page | create-disk navigation |
| Django custom Nginx | page | `liara_nginx.conf` |
| Django worker timeout | page | `WORKER TIMEOUT`, `GUNICORN_TIMEOUT`, 30 seconds |
| Django app creation | page | ready-to-use state in the user panel |

## Known limitations and deliberate choices

- `data-sources` is emitted before generation, so it represents reviewed sources; the
  inline citation gate determines which of those actually support the final answer.
- OpenRouter sometimes bills reasoning tokens without exposing reasoning deltas. A
  deterministic evidence-summary reasoning part is therefore always streamed, and any
  safe provider reasoning deltas are appended when present.
- High reasoning effort is fixed for this checkpoint because the handoff explicitly
  requires it, overriding `DESIGN.md`'s earlier adaptive-effort proposal.
- The audited corpus regeneration was loaded from the ingestion worktree without merging
  or rebasing it. Production must load the same snapshot after that branch lands.
- The live ISR page renders `next/server/app.` and `next/server/pages.` in extracted text;
  that suspicious direction/punctuation case was not used as acceptance evidence and was
  not publicly labeled defective without the near-zero-false-positive proof required by
  decision 0004.
