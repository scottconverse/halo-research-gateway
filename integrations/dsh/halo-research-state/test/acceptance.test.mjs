import assert from 'node:assert/strict'
import test from 'node:test'
import { evaluateResearchAcceptance } from '../acceptance.mjs'

const task = 'https://docs.python.org/3/library/asyncio-task.html'
const exceptions = 'https://docs.python.org/3/library/asyncio-exceptions.html'
const pep = 'https://peps.python.org/pep-0654/'

function message(seq, type, data, time = 1_000 + seq) {
  return { event: { type, seq, time, data } }
}

function gatewayResult(seq, callId, url, content, { part = 1, parts = 1, complete = true, cursor = null } = {}) {
  const envelope = {
    schema_version: '1.5', ok: true, tool: 'web_fetch', provider: 'direct-http',
    coverage: { complete }, page: { number: part, next_cursor: cursor }, warnings: complete ? [] : ['RESULT_TRUNCATED'],
    items: [{ title: url, url, content, metadata: { content_part: part, content_parts: parts } }],
  }
  return message(seq, 'tool/result', { message: {
    source: { kind: 'tool', callId }, role: 'user', id: `r-${seq}`,
    content: [{ type: 'tool-result', toolCallId: callId, content: [{ type: 'text', text: JSON.stringify(envelope) }], isError: false }],
  } })
}

function fixture(finalText, { calls = 6, endKind = 'completed', finalTime = 200_000 } = {}) {
  const prompt = `Research TaskGroup sibling cancellation, re-raising CancelledError, and grouping multiple child failures.

At most twelve research calls and six minutes. Finish in at most 250 words.`
  const events = [message(1, 'user/message', {
    role: 'user', id: 'u', source: { kind: 'user' }, content: [{ type: 'text', text: prompt }],
  }, 1_000)]
  const rows = [
    [task, 'The first time a task in the group fails with a normal exception, the remaining tasks in the group are cancelled.', 1, 11, false, 'next-task'],
    [task, 'Once all tasks have finished, failures are combined in an ExceptionGroup and raised.', 2, 11, false, 'next-task-2'],
    [exceptions, 'CancelledError can be caught for cleanup, but in almost all situations the exception must be re-raised.', 1, 1, true, null],
    [pep, 'ExceptionGroup represents a group of unrelated exceptions propagated together, allowing multiple failures to be reported.', 1, 14, false, 'next-pep'],
  ]
  let seq = 2
  for (let index = 0; index < calls; index += 1) {
    const row = rows[Math.min(index, rows.length - 1)]
    const callId = `c-${index}`
    events.push(message(seq++, 'tool/call', { callId, name: 'mcp__halo_research__web_fetch', arguments: JSON.stringify({ url: row[0], ...(index === 1 ? { cursor: 'next-task' } : {}) }) }))
    if (index < rows.length) events.push(gatewayResult(seq++, callId, row[0], row[1], { part: row[2], parts: row[3], complete: row[4], cursor: row[5] }))
  }
  events.push(message(seq++, 'assistant/message', { message: {
    role: 'assistant', id: 'a', source: { kind: 'model' }, content: [{ type: 'text', text: finalText }],
  } }, finalTime))
  events.push(message(seq, 'turn/end', { reason: { kind: endKind } }, finalTime + 1))
  return { events }
}

const passing = `When a TaskGroup child raises a normal exception, the remaining sibling tasks are cancelled and awaited; the failure is then raised after the group settles. ${task}

Coroutine cleanup code should generally re-raise CancelledError instead of swallowing it. Multiple child failures can be combined into an ExceptionGroup so they are reported together and selectively handled. ${exceptions} ${pep}

Coverage limit: the relevant excerpts were reached, but the task and PEP pages still had unread continuations, so this is a partial—not complete—reading.`

test('accepts only a completed, cited, evidence-backed workflow within every stated bound', () => {
  const verdict = evaluateResearchAcceptance(fixture(passing), { requiredUrls: [task, exceptions, pep], maxCalls: 12, maxDurationMs: 360_000, maxWords: 250 })
  assert.equal(verdict.passed, true, JSON.stringify(verdict, null, 2))
  assert.equal(verdict.checks.completed, true)
  assert.equal(verdict.checks.call_budget, true)
  assert.equal(verdict.checks.time_budget, true)
  assert.equal(verdict.checks.word_budget, true)
  assert.equal(verdict.checks.required_sources_fetched, true)
  assert.equal(verdict.checks.actual_continuation, true)
  assert.equal(verdict.checks.required_citations, true)
  assert.equal(verdict.checks.coverage_disclosed, true)
  assert.equal(verdict.checks.claims_supported_by_retrieved_text, true)
})

test('rejects over-budget, uncited, falsely complete, or semantically unsupported answers', () => {
  const falseAnswer = `All siblings finish normally. CancelledError should be swallowed. Every source was read completely. ${task}`
  const verdict = evaluateResearchAcceptance(fixture(falseAnswer, { calls: 13, endKind: 'completed', finalTime: 400_000 }), {
    requiredUrls: [task, exceptions, pep], maxCalls: 12, maxDurationMs: 360_000, maxWords: 250,
  })
  assert.equal(verdict.passed, false)
  assert.equal(verdict.checks.call_budget, false)
  assert.equal(verdict.checks.time_budget, false)
  assert.equal(verdict.checks.required_citations, false)
  assert.equal(verdict.checks.coverage_disclosed, false)
  assert.equal(verdict.checks.claims_supported_by_retrieved_text, false)
})
