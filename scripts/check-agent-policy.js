"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const appPath = path.join(__dirname, "..", "app.js");
const indexPath = path.join(__dirname, "..", "index.html");
const appSource = fs.readFileSync(appPath, "utf8");
const indexSource = fs.readFileSync(indexPath, "utf8");

const speechLines = loadSpeechLines(appSource);
const lineEntries = Object.entries(speechLines);

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
  if (pattern.test(appSource)) {
    fail(`Potential privacy leak found in app.js: ${label}.`);
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

console.log("Agent speech and privacy policy checks passed.");

function loadSpeechLines(source) {
  const objectMatch = source.match(/const speechLines = (\{[\s\S]*?\n\});/);

  if (!objectMatch) {
    fail("Could not find the approved speech line object.");
  }

  return vm.runInNewContext(`(${objectMatch[1]})`, Object.create(null));
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
