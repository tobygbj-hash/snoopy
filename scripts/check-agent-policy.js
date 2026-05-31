"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const appPath = path.join(__dirname, "..", "app.js");
const indexPath = path.join(__dirname, "..", "index.html");
const summaryBookmarkletPath = path.join(__dirname, "..", "summary-bookmarklet.html");
const summaryBookmarkletScriptPath = path.join(__dirname, "..", "summary-bookmarklet.js");
const extensionDir = path.join(__dirname, "..", "extension");
const extensionManifestPath = path.join(extensionDir, "manifest.json");
const appSource = fs.readFileSync(appPath, "utf8");
const indexSource = fs.readFileSync(indexPath, "utf8");
const summaryBookmarkletSource = fs.readFileSync(summaryBookmarkletScriptPath, "utf8");
const summaryBookmarkletHtml = fs.readFileSync(summaryBookmarkletPath, "utf8");
const extensionRuntimeSources = [
  "content-script.js",
  "content.css",
  "popup.js",
  "popup.css",
  "popup.html",
].map((fileName) => fs.readFileSync(path.join(extensionDir, fileName), "utf8"));
const extensionSources = [
  ...extensionRuntimeSources,
  fs.readFileSync(extensionManifestPath, "utf8"),
];
const browserSource = [appSource, summaryBookmarkletSource, ...extensionSources].join("\n");
const extensionManifest = JSON.parse(fs.readFileSync(extensionManifestPath, "utf8"));

const speechLines = loadSpeechLines(appSource);
const wakeWords = loadWakeWords(appSource);
const lineEntries = Object.entries(speechLines);

if (wakeWords.length < 2) {
  fail("At least two wake phrases must be configured.");
}

for (const phrase of wakeWords) {
  if (!/\bsnoopy\b/i.test(phrase)) {
    fail(`Wake phrase "${phrase}" must include the word snoopy.`);
  }
}

if (lineEntries.length === 0) {
  fail("No approved speech lines were found.");
}

for (const [key, line] of lineEntries) {
  if (!/\bToby\b/.test(line)) {
    fail(`The "${key}" speech line does not refer to Toby.`);
  }

  if (!/^[\w\s.,'-]+$/.test(line)) {
    fail(`The "${key}" speech line contains unexpected punctuation.`);
  }
}

const spokenKeys = Array.from(appSource.matchAll(/\bspeak\("([^"]+)"\)/g), (match) => match[1]);

for (const key of spokenKeys) {
  if (!Object.prototype.hasOwnProperty.call(speechLines, key)) {
    fail(`The "${key}" speech key is not in the approved speech list.`);
  }
}

const forbiddenLeakPatterns = [
  ["localStorage", /\blocalStorage\b/],
  ["sessionStorage", /\bsessionStorage\b/],
  ["cookies", /document\.cookie/],
  ["fetch", /\bfetch\s*\(/],
  ["XMLHttpRequest", /\bXMLHttpRequest\b/],
  ["sendBeacon", /\bsendBeacon\b/],
];

for (const [label, pattern] of forbiddenLeakPatterns) {
  if (pattern.test(browserSource)) {
    fail(`Potential privacy leak found in browser code: ${label}.`);
  }
}

if (!/Content-Security-Policy/.test(indexSource)) {
  fail("index.html is missing a Content Security Policy.");
}

if (!/connect-src 'none'/.test(indexSource)) {
  fail("Content Security Policy must block app network connections.");
}

if (!/<meta name="referrer" content="no-referrer" \/>/.test(indexSource)) {
  fail("index.html is missing the no-referrer policy.");
}

if (!/rel="noopener noreferrer"/.test(indexSource)) {
  fail("External links must use noopener noreferrer.");
}

if (
  /window\.open\("", "snoopy-search-results"\)/.test(appSource) &&
  !/reservedSearchWindow\.opener = null/.test(appSource)
) {
  fail("Reserved search windows must clear window.opener before navigation.");
}

if (
  /window\.open\(searchUrl/.test(appSource) &&
  !/window\.open\(searchUrl, "_blank", "noopener,noreferrer"\)/.test(appSource)
) {
  fail("Fallback search windows must include noopener,noreferrer.");
}

if (/<script[^>]+src="https?:\/\//.test(indexSource)) {
  fail("Remote scripts are not allowed.");
}

if (/<link[^>]+href="https?:\/\//.test(indexSource)) {
  fail("Remote stylesheets are not allowed.");
}

if (!/Content-Security-Policy/.test(summaryBookmarkletHtml)) {
  fail("summary-bookmarklet.html is missing a Content Security Policy.");
}

if (!/connect-src 'none'/.test(summaryBookmarkletHtml)) {
  fail("summary-bookmarklet.html must block network connections.");
}

if (/<script[^>]+src="https?:\/\//.test(summaryBookmarkletHtml)) {
  fail("Remote scripts are not allowed on the bookmarklet setup page.");
}

if (/<link[^>]+href="https?:\/\//.test(summaryBookmarkletHtml)) {
  fail("Remote stylesheets are not allowed on the bookmarklet setup page.");
}

if (/\bfetch\s*\(|XMLHttpRequest|sendBeacon|localStorage|sessionStorage|document\.cookie/.test(summaryBookmarkletSource)) {
  fail("Bookmarklet setup code must not use storage, cookies, or network calls.");
}

if (!Array.isArray(extensionManifest.host_permissions)) {
  fail("Extension must declare host_permissions explicitly.");
}

if (
  extensionManifest.host_permissions.length !== 1 ||
  extensionManifest.host_permissions[0] !== "https://www.google.com/*"
) {
  fail("Extension host permissions must stay limited to Google pages.");
}

if (extensionManifest.permissions?.includes("storage")) {
  fail("Extension must not request storage permission.");
}

if (extensionManifest.background) {
  fail("Extension must not run a background worker.");
}

if (/https?:\/\//.test(extensionRuntimeSources.join("\n"))) {
  fail("Extension runtime files must not load remote assets or make remote calls.");
}

console.log("Agent speech and privacy policy checks passed.");

function loadSpeechLines(source) {
  const objectMatch = source.match(/const speechLines = (\{[\s\S]*?\n\});/);

  if (!objectMatch) {
    fail("Could not find the approved speech line object.");
  }

  return vm.runInNewContext(`(${objectMatch[1]})`, Object.create(null));
}

function loadWakeWords(source) {
  const arrayMatch = source.match(/const wakeWords = (\[[\s\S]*?\n\]);/);

  if (!arrayMatch) {
    fail("Could not find the wake phrase list.");
  }

  return vm.runInNewContext(arrayMatch[1], Object.create(null));
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
