#!/usr/bin/env node
// Publish a pull request comment from `tessl change risk --json` output.
import { readFileSync, writeFileSync } from 'node:fs';

function fail(message) {
  console.error(`publish-risk-comment.mjs: ${message}`);
  process.exit(1);
}

function env(name, required = true) {
  const value = process.env[name];
  if ((value === undefined || value === '') && required) fail(`missing required env ${name}`);
  return value;
}

function readJson(path) {
  try {
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch (error) {
    fail(`could not read JSON from ${path}: ${error.message}`);
  }
}

function pick(obj, names) {
  for (const name of names) {
    if (obj && obj[name] !== undefined && obj[name] !== null) return obj[name];
  }
  return undefined;
}

function boolValue(value) {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'string') return value.toLowerCase() === 'true';
  return undefined;
}

function linesFrom(value) {
  if (!Array.isArray(value) || value.length === 0) return ['- None reported.'];
  return value.map((item) => `- ${String(item)}`);
}

const repoName = env('REPO');
const prNumber = env('PR_NUMBER');
const token = env('GH_TOKEN');
const assessedSha = env('ASSESSED_SHA');
const riskPath = env('RISK_OUTPUT', false) ?? 'change-risk.json';
const outPath = env('OUT', false) ?? 'risk-publish.json';
const risk = readJson(riskPath);

const decision = pick(risk, ['decision', 'gateDecision', 'gate', 'result']) ?? risk;
const judgment = pick(risk, ['judgment', 'agentJudgment', 'assessment']) ?? decision;
const reviewRequired = boolValue(
  pick(risk, ['humanReviewRequired', 'requiresHumanReview', 'reviewRequired']) ??
    pick(decision, ['humanReviewRequired', 'requiresHumanReview', 'reviewRequired']),
);
const eligibleForNoHumanReview = boolValue(
  pick(risk, ['eligibleForNoHumanReview', 'noHumanReviewAllowed']) ??
    pick(decision, ['eligibleForNoHumanReview', 'noHumanReviewAllowed']),
);
const riskLevel = pick(judgment, ['riskLevel', 'risk', 'level']) ?? pick(decision, ['riskLevel', 'risk', 'level']) ?? pick(risk, ['riskLevel', 'risk', 'level']) ?? 'unknown';
const confidence = pick(judgment, ['confidence']) ?? pick(decision, ['confidence']) ?? pick(risk, ['confidence']) ?? 'unknown';
const summary = pick(judgment, ['summary']) ?? pick(decision, ['summary', 'reason']) ?? pick(risk, ['summary', 'reason']) ?? 'No summary was reported.';
const riskFactors = pick(judgment, ['riskFactors']) ?? pick(decision, ['riskFactors']) ?? pick(risk, ['riskFactors']) ?? [];
const protectiveFactors = pick(judgment, ['protectiveFactors']) ?? pick(decision, ['protectiveFactors']) ?? pick(risk, ['protectiveFactors']) ?? [];
const requiredReasons = pick(judgment, ['requiredHumanReviewReasons']) ?? pick(decision, ['requiredHumanReviewReasons', 'reasons']) ?? pick(risk, ['requiredHumanReviewReasons', 'reasons']) ?? [];
const policyCitations = pick(judgment, ['policyCitations']) ?? pick(decision, ['policyCitations']) ?? pick(risk, ['policyCitations']) ?? [];

const reviewText = reviewRequired === undefined
  ? 'Unknown — inspect artifact output'
  : reviewRequired ? 'Yes — human review required' : 'No — policy allows no-human-review';
const eligibilityText = eligibleForNoHumanReview === undefined
  ? 'Unknown'
  : eligibleForNoHumanReview ? 'Eligible to skip human review' : 'Not eligible to skip human review';

const body = [
  `<!-- tessl-change-risk assessed-sha=${assessedSha} -->`,
  '## tessl change risk:',
  '',
  `- **Assessed SHA:** \`${assessedSha}\``,
  `- **Human review required:** ${reviewText}`,
  `- **No-human-review eligibility:** ${eligibilityText}`,
  `- **Risk level:** ${riskLevel}`,
  `- **Confidence:** ${confidence}`,
  '',
  String(summary),
  '',
  '<details>',
  '<summary>Risk evidence</summary>',
  '',
  '**Risk factors**',
  ...linesFrom(riskFactors),
  '',
  '**Protective factors**',
  ...linesFrom(protectiveFactors),
  '',
  '**Human-review reasons**',
  ...linesFrom(requiredReasons),
  '',
  '**Policy citations**',
  ...linesFrom(policyCitations),
  '</details>',
  '',
  'This advisory comment is produced by `tessl change risk`. Comment `@tessl-change-risk` to refresh it.',
].join('\n');

const [owner, repo, ...rest] = repoName.split('/');
if (!owner || !repo || rest.length > 0) fail(`REPO must be owner/repo; got ${JSON.stringify(repoName)}`);

const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/issues/${prNumber}/comments`, {
  method: 'POST',
  headers: {
    accept: 'application/vnd.github+json',
    authorization: `Bearer ${token}`,
    'content-type': 'application/json',
    'x-github-api-version': '2022-11-28',
  },
  body: JSON.stringify({ body }),
});

const text = await response.text();
if (!response.ok) fail(`GitHub issue comment failed (HTTP ${response.status}): ${text}`);
let created;
try {
  created = JSON.parse(text);
} catch (error) {
  fail(`could not parse GitHub comment response: ${error.message}`);
}
writeFileSync(outPath, `${JSON.stringify({ commentId: created.id ?? null, commentUrl: created.html_url ?? null, assessedSha, reviewRequired, riskLevel, confidence }, null, 2)}\n`);
console.error(`publish-risk-comment.mjs: created comment ${created.id ?? '(unknown id)'}`);
