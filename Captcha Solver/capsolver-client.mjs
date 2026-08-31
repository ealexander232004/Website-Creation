import fs from "node:fs";

export class CapSolverError extends Error {}

export function loadEnvFile(path = "capsolver.env") {
  const text = fs.readFileSync(path, "utf8");
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || !line.includes("=")) continue;
    const separator = line.indexOf("=");
    const name = line.slice(0, separator).trim();
    let value = line.slice(separator + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    process.env[name] = value;
  }
}

export class CapSolverClient {
  constructor({ apiKey, baseUrl = "https://api.capsolver.com", timeoutMs = 30_000 }) {
    if (!apiKey) throw new Error("A CapSolver API key is required");
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.timeoutMs = timeoutMs;
  }

  static fromEnvironment() {
    return new CapSolverClient({
      apiKey: process.env.CAPSOLVER_API_KEY,
      baseUrl: process.env.CAPSOLVER_API_URL || "https://api.capsolver.com",
    });
  }

  async getBalance() {
    const data = await this.post("getBalance", {});
    return Number(data.balance || 0);
  }

  createTask(task) {
    return this.post("createTask", { task });
  }

  getTaskResult(taskId) {
    return this.post("getTaskResult", { taskId });
  }

  async solve(task, { solveTimeoutMs = 120_000, pollIntervalMs = 1_000 } = {}) {
    const created = await this.createTask(task);
    if (created.solution) return created.solution;
    if (!created.taskId) throw new CapSolverError("CapSolver returned no task ID");

    const deadline = Date.now() + solveTimeoutMs;
    while (Date.now() < deadline) {
      const result = await this.getTaskResult(created.taskId);
      if (result.status === "ready") {
        if (!result.solution) throw new CapSolverError("CapSolver returned no solution");
        return result.solution;
      }
      if (![undefined, "processing", "idle"].includes(result.status)) {
        throw new CapSolverError("CapSolver returned an unexpected task status");
      }
      await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
    }
    throw new CapSolverError("CapSolver task timed out");
  }

  async post(endpoint, payload) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await fetch(`${this.baseUrl}/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clientKey: this.apiKey, ...payload }),
        signal: controller.signal,
      });
      if (!response.ok) throw new CapSolverError(`CapSolver ${endpoint} request failed`);
      const data = await response.json();
      if (data.errorId) {
        throw new CapSolverError(
          `CapSolver ${data.errorCode || "UNKNOWN_ERROR"}: ${data.errorDescription || "request rejected"}`,
        );
      }
      return data;
    } catch (error) {
      if (error instanceof CapSolverError) throw error;
      throw new CapSolverError(`CapSolver ${endpoint} request failed`);
    } finally {
      clearTimeout(timeout);
    }
  }
}

export function recaptchaV2Task({
  websiteURL,
  websiteKey,
  proxy,
  enterprise = false,
  invisible = false,
  dataS,
  pageAction,
}) {
  let type = enterprise ? "ReCaptchaV2EnterpriseTask" : "ReCaptchaV2Task";
  if (!proxy) type += "ProxyLess";
  const task = {
    type,
    websiteURL,
    websiteKey,
    isInvisible: invisible,
    isSession: true,
  };
  if (proxy) task.proxy = proxy;
  if (dataS) {
    if (enterprise) task.enterprisePayload = { s: dataS };
    else task.recaptchaDataSValue = dataS;
  }
  if (pageAction) task.pageAction = pageAction;
  return task;
}
