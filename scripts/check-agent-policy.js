"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const appPath = path.join(__dirname, "..", "app.js");
const appSource = fs.readFileSync(appPath, "utf8");

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

console.log("Agent speech policy checks passed.");

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
