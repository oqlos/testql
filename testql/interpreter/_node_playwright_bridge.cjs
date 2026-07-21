"use strict";

const readline = require("node:readline");
const {createRequire} = require("node:module");

let browser = null;
let page = null;

function playwrightFrom(packagePath) {
  const requireFromProject = createRequire(`${packagePath}/package.json`);
  return requireFromProject(packagePath);
}

function locator(selector, first = false) {
  const result = page.locator(selector);
  return first ? result.first() : result;
}

function browserExpression(source) {
  const value = String(source).trim();
  if (
    value.startsWith("function") ||
    value.startsWith("async function") ||
    value.includes("=>")
  ) {
    return (0, eval)(`(${value})`);
  }
  return value;
}

async function dispatch(command, args) {
  switch (command) {
    case "start": {
      const playwright = playwrightFrom(args.package_path);
      const launch = {
        headless: args.headless,
        args: ["--no-sandbox", "--disable-setuid-sandbox"],
      };
      if (args.executable_path) launch.executablePath = args.executable_path;
      browser = await playwright.chromium.launch(launch);
      page = await browser.newPage();
      page.setDefaultTimeout(args.timeout);
      page.setDefaultNavigationTimeout(args.navigation_timeout);
      await page.goto(args.url, {timeout: args.navigation_timeout});
      return {url: page.url()};
    }
    case "goto":
      await page.goto(args.url, {timeout: args.timeout});
      return {url: page.url()};
    case "add_init_script":
      await page.addInitScript({content: args.script});
      return true;
    case "performance_metrics":
      return Promise.all(page.frames().map(async (frame) => {
        try {
          return await frame.evaluate(browserExpression(args.expression));
        } catch (_) {
          return null;
        }
      }));
    case "wait_for_url":
      await page.waitForURL(args.url, {waitUntil: args.wait_until, timeout: args.timeout});
      return {url: page.url()};
    case "url":
      return page.url();
    case "is_visible":
      return locator(args.selector, true).isVisible({timeout: args.timeout});
    case "click":
      await locator(args.selector, args.first).click({timeout: args.timeout});
      return true;
    case "fill":
      await page.fill(args.selector, args.value, {timeout: args.timeout});
      return true;
    case "select_option": {
      const option = args.mode === "label" ? {label: args.value} : {value: args.value};
      try {
        return await page.selectOption(args.selector, option, {timeout: args.timeout});
      } catch (error) {
        if (String(error).includes("did not find some options")) return [];
        throw error;
      }
    }
    case "locator_evaluate":
      return locator(args.selector, args.first).evaluate(
        browserExpression(args.expression),
        args.arg,
      );
    case "scroll_element":
      await locator(args.selector, args.first).evaluate(
        (el, delta) => el.scrollBy({left: delta.x, top: delta.y, behavior: "auto"}),
        {x: args.x, y: args.y},
      );
      return true;
    case "wheel":
      await page.mouse.wheel(args.x, args.y);
      return true;
    case "inner_text":
      return page.innerText(args.selector, {timeout: args.timeout});
    case "evaluate":
      return page.evaluate(browserExpression(args.expression));
    case "count":
      return locator(args.selector, args.first).count();
    case "input_value":
      return locator(args.selector, args.first).inputValue({timeout: args.timeout});
    case "get_attribute":
      return locator(args.selector, args.first).getAttribute(args.name, {timeout: args.timeout});
    case "screenshot":
      if (args.selector) {
        await locator(args.selector, args.first).screenshot({path: args.path});
      } else {
        await page.screenshot({path: args.path});
      }
      return true;
    case "close":
      if (browser) await browser.close();
      browser = null;
      page = null;
      return true;
    default:
      throw new Error(`unsupported bridge command: ${command}`);
  }
}

const input = readline.createInterface({input: process.stdin, crlfDelay: Infinity});
input.on("line", async (line) => {
  let request;
  try {
    request = JSON.parse(line);
    const result = await dispatch(request.command, request.args || {});
    process.stdout.write(`${JSON.stringify({id: request.id, ok: true, result})}\n`);
  } catch (error) {
    process.stdout.write(`${JSON.stringify({
      id: request?.id,
      ok: false,
      error: error?.stack || String(error),
    })}\n`);
  }
});

async function shutdown() {
  try {
    if (browser) await browser.close();
  } finally {
    process.exit(0);
  }
}

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
