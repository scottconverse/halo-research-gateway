import { buildVerifiedResearchState } from './index.mjs'

function unwrap(history) {
  if (!Array.isArray(history?.events)) return []
  return history.events.map(entry => entry?.event ?? entry).filter(Boolean)
}

function assistantText(event) {
  return event?.data?.message?.content
    ?.filter(block => block?.type === 'text' && typeof block.text === 'string')
    .map(block => block.text)
    .join('\n') ?? ''
}

function words(text) {
  const trimmed = text.trim()
  return trimmed === '' ? 0 : trimmed.split(/\s+/).length
}

function sourceByUrl(state, url) {
  return state?.sources.find(source => source.url === url)
}

function sourceEvidence(source) {
  return source?.excerpts.join('\n').toLowerCase() ?? ''
}

function semanticChecks(final, state, requiredUrls) {
  const lower = final.toLowerCase()
  const taskSource = requiredUrls.find(url => /asyncio-task\.html/.test(url))
  const exceptionSource = requiredUrls.find(url => /asyncio-exceptions\.html/.test(url))
  const groupSource = requiredUrls.find(url => /pep-0654/.test(url))
  const taskEvidence = sourceEvidence(sourceByUrl(state, taskSource))
  const exceptionEvidence = sourceEvidence(sourceByUrl(state, exceptionSource))
  const groupEvidence = sourceEvidence(sourceByUrl(state, groupSource))

  const siblingClaim = (/(?:remaining|sibling)\w*[\s\S]{0,100}cancel/.test(lower)
    || /cancel\w*[\s\S]{0,100}(?:remaining|sibling)/.test(lower))
    && !/(?:remaining|sibling)\w*[\s\S]{0,50}(?:finish|complete)\w*\s+normally/.test(lower)
  const reraisingClaim = /cancellederror/.test(lower)
    && /(?:re-?raise|propagat|do not swallow|not swallow)/.test(lower)
    && !/cancellederror[^.]{0,80}(?:should|must)\s+be\s+swallowed/.test(lower)
  const groupingClaim = /exception\s*group|exceptiongroup/.test(lower)
    && /multiple|combined|together|several/.test(lower)
  const answerClaims = siblingClaim && reraisingClaim && groupingClaim

  const evidenceSupports = /remaining tasks/.test(taskEvidence) && /cancel/.test(taskEvidence)
    && /re-raised|re-raise/.test(exceptionEvidence)
    && /exceptiongroup|exception group/.test(groupEvidence)
    && /multiple|unrelated|more than one|all of them/.test(groupEvidence)

  const paragraphs = final.split(/\n\s*\n+/).map(value => value.trim()).filter(Boolean)
  const taskCitationNearClaim = paragraphs.some(paragraph => paragraph.includes(taskSource ?? '\0')
    && /remaining|sibling/i.test(paragraph) && /cancel/i.test(paragraph))
  const exceptionCitationNearClaim = paragraphs.some(paragraph => paragraph.includes(exceptionSource ?? '\0')
    && /CancelledError/i.test(paragraph) && /re-?raise|propagat|swallow/i.test(paragraph))
  const groupCitationNearClaim = paragraphs.some(paragraph => paragraph.includes(groupSource ?? '\0')
    && /ExceptionGroup|exception group/i.test(paragraph) && /multiple|combined|together/i.test(paragraph))

  return {
    answerClaims,
    evidenceSupports,
    citationsNearClaims: taskCitationNearClaim && exceptionCitationNearClaim && groupCitationNearClaim,
  }
}

export function evaluateResearchAcceptance(history, options = {}) {
  const requiredUrls = options.requiredUrls ?? []
  const maxCalls = options.maxCalls ?? 12
  const maxDurationMs = options.maxDurationMs ?? 360_000
  const maxWords = options.maxWords ?? 250
  const events = unwrap(history)
  const state = buildVerifiedResearchState(events)
  const request = events.findLast(event => event.type === 'user/message' && event.data?.source?.kind === 'user')
  const finalEvent = events.findLast(event => event.type === 'assistant/message')
  const final = assistantText(finalEvent)
  const turnEnd = events.findLast(event => event.type === 'turn/end')
  const finalHasToolCalls = finalEvent?.data?.message?.content?.some(block => block?.type === 'tool-call') === true
  const fetched = new Set(state?.sources.map(source => source.url) ?? [])
  const incomplete = state?.sources.some(source => !source.complete || source.nextCursor !== null) === true
  const positiveCoverage = /partial|incomplete|unread|continuation|not (?:a )?complete|not fully/i.test(final)
  const falseCompleteness = incomplete && /(?:all|every|each)\s+(?:three\s+)?(?:source|page)s?[^.]{0,50}(?:fully|completely)\s+(?:read|fetched)|complete reading of (?:all|every)/i.test(final)
  const semantic = semanticChecks(final, state, requiredUrls)
  const elapsedMs = request && finalEvent ? Math.max(0, finalEvent.time - request.time) : null
  const wordCount = words(final)

  const checks = {
    completed: turnEnd?.data?.reason?.kind === 'completed' && !finalHasToolCalls && final.trim() !== '',
    call_budget: state !== null && state.researchCalls <= maxCalls,
    time_budget: elapsedMs !== null && elapsedMs <= maxDurationMs,
    word_budget: wordCount > 0 && wordCount <= maxWords,
    required_sources_fetched: requiredUrls.length > 0 && requiredUrls.every(url => fetched.has(url)),
    actual_continuation: state?.sources.some(source => source.observedParts.length >= 2) === true,
    required_citations: requiredUrls.length > 0 && requiredUrls.every(url => final.includes(url)),
    citations_near_claims: semantic.citationsNearClaims,
    coverage_disclosed: !incomplete || (positiveCoverage && !falseCompleteness),
    claims_supported_by_retrieved_text: semantic.answerClaims && semantic.evidenceSupports,
    successful_gateway_results: (state?.successfulResults ?? 0) >= 4,
  }
  return {
    passed: Object.values(checks).every(Boolean),
    checks,
    metrics: {
      calls: state?.researchCalls ?? 0,
      elapsedMs,
      words: wordCount,
      successfulResults: state?.successfulResults ?? 0,
      fetchedUrls: [...fetched],
      incompleteUrls: state?.sources.filter(source => !source.complete || source.nextCursor !== null).map(source => source.url) ?? [],
    },
    final,
    manualEvidenceReviewRequired: true,
  }
}
