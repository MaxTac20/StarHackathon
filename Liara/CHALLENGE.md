# Liara Challenge — North Star

This is the record of what the Liara challenge asks for, drawn from the challenge
introduction video and the challenge page. It is the reference our work gets checked
against.

It contains no design, architecture, or strategy. Those are decisions we make *within*
these requirements and they belong in their own documents — keeping them out is what
lets this file stay a reliable answer to "is this actually what was asked for?"

---

## 1. The problem

Liara's range of services keeps growing, and its documentation grows along with it.
There is now a large volume of Liara documentation.

A significant share of the tickets and phone calls reaching Liara support exist for one
of two reasons:

- the user did not understand something in the documentation, or
- the user never found the relevant document at all.

## 2. What is being asked

Liara asks that this problem be solved by implementing **an LLM-based application**.

On the shape of that application, the briefing is explicit:

- The first idea that will occur to most teams is a chatbot that knows the Liara docs
  and helps users use Liara's services. **This is acceptable** — *«بله این می‌شه»*.
- **But** other LLM-based solutions exist, and those other solutions **may even be
  better** — *«قطعاً راه‌حل‌های دیگه‌ای هم وجود داره ... و ممکنه اون راه‌حل‌های دیگه حتی
  بهتر هم باشن»*.
- The **more agentic** the solution's capabilities are — and specifically, agentic in
  the direction of **letting the user use Liara's services more easily and faster** —
  the more it scores. This is stated as carrying judging score and being among the
  judging criteria.

The solution is aimed at Liara's **users**, helping them use Liara's services.

## 3. Documentation sources

Liara's documentation is open source and available from:

- Official documentation: <https://docs.liara.ir/>
- Documentation GitHub repository: <https://github.com/liara-cloud/docs>

Either may be used — the rendered documentation on the website, or the documentation
software and repository on GitHub, which is itself open source.

## 4. Required deliverables

The final output must include:

1. **A link to the deployed project, running on Liara's infrastructure.**
2. **A link to the project's GitHub repository.**

The project must be **fully runnable and usable** on Liara's infrastructure.

Further detail from the briefing:

- Liara has **already credited the team's account** for this purpose.
- Liara's own site may be used to deploy, and deploying on the platform services (PaaS)
  is recommended.
- The deployed application must have **everything working** — judges must be able to
  test and use it **on that link**.
- Deployment carries **"a very significant score"** for this challenge.

## 5. If deployment is not possible

A team that cannot deploy to Liara for any reason may instead submit a **demo video** of
the product, so the remaining parts of the project can still be evaluated.

- The video must show the implemented capabilities **completely**.
- It should be **at least 5 minutes**, with the team explaining the product and
  **testing various scenarios** on it.
- In this case the **deployment score is forfeited entirely**, but all other parts of
  the project remain evaluable.

## 6. Judging criteria

The judges score **exactly** against these criteria and **exactly** these point values.
The briefing stresses consulting them **before implementing** and building according to
them, because it strongly affects the score.

### 1. کیفیت و صحت پاسخ‌ها — Answer quality and correctness — **80**

- صحت و مرتبط بودن پاسخ‌ها — correctness and relevance of answers
- کامل و کاربردی بودن پاسخ‌ها — answers being complete and practical
- توانایی پیدا کردن اطلاعات مناسب — ability to find the appropriate information
- کاهش پاسخ‌های نادرست و ساختگی — reducing incorrect and fabricated answers
- ارائه منبع مناسب — providing appropriate sources
- عملکرد مناسب در سوالات ساده و پیچیده — good performance on both simple and complex questions

### 2. طراحی UI و تجربه کاربری — UI design and user experience — **55**

- کیفیت طراحی و سادگی استفاده — design quality and ease of use
- تجربه مناسب در مکالمه — good conversational experience
- نمایش مناسب کد، لینک و اطلاعات فنی — proper display of code, links and technical information
- تجربه مناسب در ادامه Conversation — good experience when continuing a conversation
- Responsive بودن — being responsive
- توجه به جزئیات UX — attention to UX detail

### 3. قابلیت‌های Agentic و Personalization — Agentic capabilities and personalization — **50**

- درک صحیح Intent کاربر — correctly understanding user intent
- پرسیدن سؤال تکمیلی در صورت نیاز — asking follow-up questions when needed
- حفظ Context مکالمه — maintaining conversation context
- شخصی‌سازی پاسخ‌ها — personalizing answers
- پیشنهاد قدم بعدی به کاربر — suggesting the user's next step
- انجام فرآیندهای چندمرحله‌ای — carrying out multi-step processes
- استفاده خلاقانه و کاربردی از قابلیت‌های Agentic — creative and practical use of agentic capabilities

### 4. امنیت، پایداری و Monitoring — Security, stability and monitoring — **50**

- پیاده‌سازی Rate Limiting — implementing rate limiting
- مدیریت صحیح API Key و Secretها — correct management of API keys and secrets
- مدیریت خطا و شرایط Failure — error and failure-condition handling
- کنترل مصرف Token و درخواست‌های غیرضروری — controlling token consumption and unnecessary requests
- Logging و Monitoring — logging and monitoring
- طراحی معماری قابل توسعه و نگهداری — extensible and maintainable architecture design

### 5. استقرار روی زیرساخت لیارا — Deployment on Liara's infrastructure — **40**

- اجرای موفق پروژه روی زیرساخت لیارا — successfully running the project on Liara's infrastructure
- کیفیت فرآیند Deployment — quality of the deployment process
- Configuration مناسب — appropriate configuration
- آماده بودن پروژه برای استفاده در محیط Production — project's readiness for production use

### 6. بهینه‌سازی هزینه — Cost optimization — **25**

- انتخاب مناسب مدل و سرویس‌ها — appropriate choice of model and services
- کنترل مصرف Token — controlling token consumption
- کاهش درخواست‌های غیرضروری — reducing unnecessary requests
- استفاده از Cache در صورت نیاز — using caching where needed
- توجه به هزینه زیرساخت — attention to infrastructure cost
- ایجاد تعادل مناسب بین کیفیت پاسخ و هزینه — striking a good balance between answer quality and cost

### Totals

| معیار | Criterion | امتیاز |
|---|---|---:|
| کیفیت و صحت پاسخ‌ها | Answer quality and correctness | 80 |
| طراحی UI و تجربه کاربری | UI design and user experience | 55 |
| قابلیت‌های Agentic و Personalization | Agentic capabilities and personalization | 50 |
| امنیت، پایداری و Monitoring | Security, stability and monitoring | 50 |
| استقرار روی زیرساخت لیارا | Deployment on Liara's infrastructure | 40 |
| بهینه‌سازی هزینه | Cost optimization | 25 |
| **مجموع** | **Total** | **300** |

The Persian wording of each criterion is kept verbatim because that is the text the
judges score against; the English alongside it is a working translation, not a
substitute.

---

## Amendment rule

This file records the challenge as stated. If a requirement is corrected or clarified,
amend this file. Design decisions do not belong here.
