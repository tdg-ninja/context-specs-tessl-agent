#!/usr/bin/env node
// Publish a single GitHub PR review from `tessl change review --json` output.
import { readFileSync, writeFileSync } from 'node:fs';

function fail(message) {
  console.error(`publish-review.mjs: ${message}`);
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

function skillDisplayName(ref) {
  const selected = String(ref).split('#').pop();
  const withoutVersion = selected.replace(/@[^/@#]+$/, '');
  const parts = withoutVersion.split('/').filter(Boolean);
  const leaf = parts.at(-1) ?? withoutVersion;
  return leaf === 'SKILL.md' && parts.length > 1 ? parts.at(-2) : leaf;
}

const repoName = env('REPO');
const prNumber = env('PR_NUMBER');
const token = env('GH_TOKEN');
const reviewPath = env('REVIEW_OUTPUT', false) ?? 'change-review.json';
const outPath = env('OUT', false) ?? 'review-publish.json';
const reviewAction = env('REVIEW_ACTION', false) ?? 'comment';

if (reviewAction !== 'comment' && reviewAction !== 'request-changes-on-findings') {
  fail(`REVIEW_ACTION must be comment or request-changes-on-findings; got ${JSON.stringify(reviewAction)}`);
}

const review = readJson(reviewPath);
if (!review.summary || typeof review.summary !== 'object') fail('review JSON missing object summary');
if (!Array.isArray(review.comments)) fail('review JSON missing array comments');
if (!review.metadata || typeof review.metadata !== 'object') fail('review JSON missing object metadata');

const headSha = review.metadata.headSha;
if (typeof headSha !== 'string' || headSha === '') fail('review metadata missing string headSha');
if (!Array.isArray(review.metadata.skills)) fail('review metadata missing array skills');
if (typeof review.summary.overview !== 'string') fail('review summary missing string overview');
if (!Array.isArray(review.summary.warnings)) fail('review summary missing array warnings');
if (!Array.isArray(review.summary.unplacedFindings)) fail('review summary missing array unplacedFindings');

const marker = '<!-- tessl-change-review -->';
const overview = review.summary.overview.trim().replace(/^#{1,6}\s+findings\s*\n+/i, '').trim();
const skillNames = review.metadata.skills.map(skillDisplayName);
const bodyParts = [
  marker,
  '## tessl change review:',
  skillNames.length > 0
    ? `Reviewed against skills: ${skillNames.map((name) => `\`${name}\``).join(', ')}`
    : 'Reviewed against skills: _none reported_',
  overview === '' ? '_No summary was produced for this diff._' : overview,
];

if (review.summary.unplacedFindings.length > 0) {
  bodyParts.push([
    '<details>',
    `<summary>Unplaced findings (${review.summary.unplacedFindings.length}) — could not anchor to a changed hunk</summary>`,
    '',
    review.summary.unplacedFindings.map((finding) => {
      const location = [finding.path, finding.line ? `line ${finding.line}` : '', finding.side].filter(Boolean).join(':');
      const where = location ? ` \`${location}\`` : '';
      const reason = finding.reason ? ` (${finding.reason})` : '';
      return `- **Unplaced finding**${where}${reason}\n  ${String(finding.body ?? '').replace(/\n/g, '\n  ')}`;
    }).join('\n'),
    '</details>',
  ].join('\n'));
}

if (review.summary.warnings.length > 0) {
  bodyParts.push([
    '<details>',
    `<summary>Warnings (${review.summary.warnings.length})</summary>`,
    '',
    review.summary.warnings.map((warning) => `- ${warning}`).join('\n'),
    '</details>',
  ].join('\n'));
}

bodyParts.push('---\nTo trigger a re-review, comment `@tessl-change-review`.');
const body = bodyParts.join('\n\n');

const comments = review.comments.map((comment, index) => {
  if (!comment || typeof comment !== 'object') fail(`comments[${index}] is not an object`);
  if (typeof comment.path !== 'string' || comment.path === '') fail(`comments[${index}] missing string path`);
  if (!Number.isInteger(comment.line) || comment.line < 1) fail(`comments[${index}] line must be a positive integer`);
  if (comment.side !== 'LEFT' && comment.side !== 'RIGHT') fail(`comments[${index}] side must be LEFT or RIGHT`);
  if (typeof comment.body !== 'string' || comment.body === '') fail(`comments[${index}] missing string body`);
  const mapped = { path: comment.path, line: comment.line, side: comment.side, body: comment.body };
  if (comment.startLine !== undefined) {
    if (!Number.isInteger(comment.startLine) || comment.startLine < 1) fail(`comments[${index}] startLine must be a positive integer`);
    if (comment.startLine < comment.line) {
      mapped.start_line = comment.startLine;
      if (comment.startSide !== undefined) {
        if (comment.startSide !== 'LEFT' && comment.startSide !== 'RIGHT') fail(`comments[${index}] startSide must be LEFT or RIGHT`);
        mapped.start_side = comment.startSide;
      }
    }
  }
  return mapped;
});

const hasFindings = comments.length > 0 || review.summary.unplacedFindings.length > 0;
const event = reviewAction === 'request-changes-on-findings' && hasFindings ? 'REQUEST_CHANGES' : 'COMMENT';
const [owner, repo, ...rest] = repoName.split('/');
if (!owner || !repo || rest.length > 0) fail(`REPO must be owner/repo; got ${JSON.stringify(repoName)}`);

const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/pulls/${prNumber}/reviews`, {
  method: 'POST',
  headers: {
    accept: 'application/vnd.github+json',
    authorization: `Bearer ${token}`,
    'content-type': 'application/json',
    'x-github-api-version': '2022-11-28',
  },
  body: JSON.stringify({ commit_id: headSha, event, body, comments }),
});

const text = await response.text();
if (!response.ok) fail(`GitHub createReview failed (HTTP ${response.status}): ${text}`);

let created;
try {
  created = JSON.parse(text);
} catch (error) {
  fail(`could not parse GitHub createReview response: ${error.message}`);
}

writeFileSync(outPath, `${JSON.stringify({ reviewId: created.id ?? null, reviewUrl: created.html_url ?? null, commitId: headSha, event, commentCount: comments.length }, null, 2)}\n`);
console.error(`publish-review.mjs: created review ${created.id ?? '(unknown id)'}`);
