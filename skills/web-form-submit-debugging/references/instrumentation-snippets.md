# Instrumentation snippets

Run these in the page context (browser extension JavaScript tool or DevTools
console). Some tools redact cookie and query-string data from results; that is
expected. Install first, act, then read `window.__log`.

## 1. Install hooks

```javascript
window.__log = [];
const L = (m) => window.__log.push(new Date().toISOString().slice(11, 23) + ' ' + m);
const of = window.fetch;
window.fetch = function (u, o) {
  L('fetch ' + ((o && o.method) || 'GET') + ' ' + String(u).slice(0, 140));
  return of.apply(this, arguments).then(
    (r) => { L('fetch-> ' + r.status + ' ' + String(u).slice(0, 60)); return r; },
    (e) => { L('fetch-err ' + e.message); throw e; });
};
const ox = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function (m, u) { L('xhr ' + m + ' ' + String(u).slice(0, 140)); return ox.apply(this, arguments); };
const ps = history.pushState, rs = history.replaceState;
history.pushState = function () { L('pushState ' + arguments[2]); return ps.apply(this, arguments); };
history.replaceState = function () { L('replaceState ' + arguments[2]); return rs.apply(this, arguments); };
const oo = window.open;
window.open = function (u) { L('window.open ' + u); return oo.apply(this, arguments); };
window.addEventListener('error', (e) => L('error ' + e.message));
window.addEventListener('unhandledrejection', (e) => L('rejection ' + (e.reason && e.reason.message || e.reason)));
window.addEventListener('beforeunload', () => L('beforeunload'));
document.addEventListener('submit', (e) => L('submit event; defaultPrevented=' + e.defaultPrevented), true);
'hooks installed';
```

## 2. Click and read

```javascript
window.__log.length = 0;
[...document.querySelectorAll('button')].find((b) => b.textContent.trim() === 'Next').click();
await new Promise((r) => setTimeout(r, 5000));
({ log: window.__log, url: location.href.slice(0, 100),
   errors: [...document.querySelectorAll('[class*="error"],[role="alert"]')].map((e) => e.textContent.trim()).filter(Boolean).slice(0, 5) });
```

## 3. Inspect the form shape

```javascript
const f = document.querySelector('form');
({ forms: document.forms.length, action: f && f.getAttribute('action'),
   inForm: !!document.querySelector('button[type=submit]')?.closest('form'),
   invalid: f ? [...f.querySelectorAll(':invalid')].map((e) => e.name || e.tagName) : null,
   hidden: f ? [...f.querySelectorAll('input[type=hidden]')].map((i) => i.name) : null });
```

## 4. Read what the analytics call carried

Wrap `fetch` as in snippet 1 but, for URLs containing the analytics host, push
`JSON.parse(o.body)` into the log. Event names such as "form started" and "form
submitted" with empty form ids confirm the page tracked the click without
calling its own API.

## 5. Probe the analytics endpoint

`await fetch(<analytics url>, {method:'POST', mode:'cors', headers:{'Content-Type':'application/json'}, body:'{}'})`
and log the status. A 2xx/204 means the endpoint is reachable and blocking is
not the cause.

## 6. Environment checks

- External scripts: `[...document.scripts].map(s => s.src).filter(Boolean)`.
- Captcha: check `window.turnstile`, `window.grecaptcha`, `window.hcaptcha` and
  `document.querySelectorAll('iframe')` sources.
- Extension injection: look for nodes with extension-specific ids or classes
  inside the form.
