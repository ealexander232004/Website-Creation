# API reference used by this account

Base URL: `https://api.capsolver.com`

Authentication is sent in the JSON request body as `clientKey`. It is not an
HTTP bearer token or query-string parameter.

## Account balance

`POST /getBalance`

```json
{
  "clientKey": "YOUR_CAPSOLVER_API_KEY"
}
```

## Create a task

`POST /createTask`

Google reCAPTCHA v2 without a proxy:

```json
{
  "clientKey": "YOUR_CAPSOLVER_API_KEY",
  "task": {
    "type": "ReCaptchaV2TaskProxyLess",
    "websiteURL": "https://example.com/challenge",
    "websiteKey": "PUBLIC_SITE_KEY",
    "isInvisible": false,
    "isSession": true
  }
}
```

The existing integration also uses these variants:

- `ReCaptchaV2Task` — add a credentialed `proxy` URL to the task.
- `ReCaptchaV2EnterpriseTaskProxyLess` — enterprise challenge without proxy.
- `ReCaptchaV2EnterpriseTask` — enterprise challenge with proxy.
- `recaptchaDataSValue` — optional Google reCAPTCHA v2 `data-s` value.
- `enterprisePayload: {"s": "..."}` — enterprise `data-s` value.
- `pageAction` — optional action name.

## Poll task result

`POST /getTaskResult`

```json
{
  "clientKey": "YOUR_CAPSOLVER_API_KEY",
  "taskId": "TASK_ID_FROM_CREATE_TASK"
}
```

Continue polling while `status` is `processing`. Stop on `ready` and read the
`solution`. Treat a nonzero `errorId` as an error and record `errorCode` and
`errorDescription` without logging credentials or returned solution tokens.

## Secret-handling rules

- Never include the API key in URLs, logs, exceptions, screenshots, or commits.
- Do not log CAPTCHA solution tokens or returned session cookies.
- Use `getBalance` for a free credential check before creating paid tasks.
- Use the same proxy/session identity for a proxy-bound task and the browser or
  HTTP request that consumes its solution.
