import { readFile } from 'node:fs/promises'
import { evaluateResearchAcceptance } from './acceptance.mjs'

const historyPath = process.argv[2]
if (!historyPath) throw new Error('usage: node verify-history.mjs <dsh-history.json>')

const requiredUrls = [
  'https://docs.python.org/3/library/asyncio-task.html',
  'https://docs.python.org/3/library/asyncio-exceptions.html',
  'https://peps.python.org/pep-0654/',
]
const history = JSON.parse(await readFile(historyPath, 'utf8'))
const verdict = evaluateResearchAcceptance(history, {
  requiredUrls,
  maxCalls: 12,
  maxDurationMs: 360_000,
  maxWords: 250,
})
console.log(JSON.stringify(verdict, null, 2))
if (!verdict.passed) process.exitCode = 1
