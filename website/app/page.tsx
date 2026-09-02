import {
  ArrowRight,
  BookOpen,
  Bot,
  Braces,
  CheckCircle2,
  Database,
  ExternalLink,
  Code2,
  Globe2,
  KeyRound,
  Network,
  Search,
  ShieldCheck,
  Terminal,
  Workflow,
} from 'lucide-react';

import { buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const capabilities = [
  {
    icon: Search,
    title: 'Discovery that keeps going',
    body: 'Anonymous Exa with DDGS fallback, bounded deep research, read-only GitHub App results, public captions, and structured community threads.',
  },
  {
    icon: Globe2,
    title: 'Fetch and real browser crawl',
    body: 'Read ordinary pages directly, or render JavaScript with gateway-owned Chrome. Cookie-only research sessions and WebSocket checks have fixture coverage; real login compatibility still needs testing.',
  },
  {
    icon: Database,
    title: 'Evidence that survives the turn',
    body: 'Persistent cache, durable jobs, fair client queues, signed continuation pages, canonical URLs, deduplication, and citable evidence.',
  },
  {
    icon: KeyRound,
    title: 'Operator-owned identity',
    body: 'Encrypted research connections, OAuth sign-in, a read-only GitHub App, and reviewed cookie-only research-session import.',
  },
  {
    icon: Workflow,
    title: 'Research, not account operations',
    body: 'Find sources, read them, and return cited evidence. No email sending, GitHub posting, shopping, or account changes.',
  },
  {
    icon: ShieldCheck,
    title: 'Explicit limits and coverage',
    body: 'Public web sources and named local targets, with shared queues and visible partial results. Optional challenge/proxy adapters are disabled; complete crawl routing is not yet verified.',
  },
];

const toolGroups = [
  ['Public web', 'web_search · web_fetch · web_crawl'],
  [
    'Communities',
    'reddit_search · reddit_thread · community_search · community_thread',
  ],
  [
    'Deep evidence',
    'document_extract · deep_research · github_research · transcript_fetch',
  ],
  ['Local + durable', 'local_fetch · local_crawl · research_job'],
];

const hosts = ['DSH', 'Codex', 'Claude Code', 'OpenCode', 'LM Studio Bionic'];

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden bg-background text-foreground">
      <nav className="sticky top-0 z-50 border-b border-white/8 bg-background/85 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 lg:px-8">
          <a
            href="#top"
            className="flex items-center gap-3 font-semibold tracking-tight"
          >
            <span className="grid size-9 place-items-center rounded-xl border border-cyan-300/25 bg-cyan-300/10 text-cyan-200">
              <Network className="size-5" />
            </span>
            <span>Halo Research Gateway</span>
            <span className="hidden rounded-full border border-emerald-300/20 bg-emerald-300/8 px-2 py-0.5 font-mono text-[10px] text-emerald-200 sm:inline">
              v0.2.0
            </span>
          </a>
          <div className="hidden items-center gap-7 text-sm text-slate-400 md:flex">
            <a className="transition hover:text-white" href="#architecture">
              Architecture
            </a>
            <a className="transition hover:text-white" href="#capabilities">
              Capabilities
            </a>
            <a className="transition hover:text-white" href="#proof">
              Proof
            </a>
            <a className="transition hover:text-white" href="#start">
              Quick start
            </a>
          </div>
        </div>
      </nav>

      <section id="top" className="relative border-b border-white/8">
        <div className="halo-grid absolute inset-0 opacity-45" />
        <div className="halo-orb absolute -right-32 top-4 size-[520px] rounded-full" />
        <div className="relative mx-auto grid max-w-7xl gap-16 px-5 pb-24 pt-20 lg:grid-cols-[1.12fr_.88fr] lg:px-8 lg:pb-32 lg:pt-28">
          <div>
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/7 px-3 py-1.5 font-mono text-xs text-cyan-100">
              <span className="size-1.5 rounded-full bg-emerald-300 shadow-[0_0_12px_#6ee7b7]" />
              DSH-first · localhost-only · source-backed
            </div>
            <h1 className="max-w-4xl text-balance text-5xl font-semibold leading-[.98] tracking-[-0.05em] text-white sm:text-6xl lg:text-[82px]">
              One research plane.
              <br />
              <span className="text-cyan-200">Every agent.</span>
            </h1>
            <p className="mt-7 max-w-2xl text-pretty text-lg leading-8 text-slate-300 sm:text-xl">
              Give DSH the tools to find web sources, read pages and documents,
              compare evidence, and return useful citations. The Gateway runs
              locally on Windows. It does not send email, post to GitHub, buy
              things, or manage accounts.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <a
                href="#start"
                className={cn(
                  buttonVariants({ size: 'lg' }),
                  'h-11 bg-cyan-200 px-5 text-slate-950 hover:bg-cyan-100',
                )}
              >
                Read installation steps <ArrowRight />
              </a>
              <a
                href="https://github.com/scottconverse/halo-research-gateway"
                className={cn(
                  buttonVariants({ variant: 'outline', size: 'lg' }),
                  'h-11 border-white/15 bg-white/4 px-5 text-white hover:bg-white/9',
                )}
              >
                <Code2 /> View repository
              </a>
            </div>
            <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 text-sm text-slate-400">
              {[
                '14 research tools',
                '176 local regression tests',
                'DSH is the primary client',
              ].map((item) => (
                <span key={item} className="flex items-center gap-2">
                  <CheckCircle2 className="size-4 text-emerald-300" />
                  {item}
                </span>
              ))}
            </div>
          </div>

          <div className="relative lg:pt-4">
            <div className="rounded-3xl border border-white/10 bg-[#091723]/90 p-3 shadow-2xl shadow-cyan-950/40">
              <div className="flex items-center gap-2 border-b border-white/8 px-3 py-3 font-mono text-[11px] text-slate-500">
                <span className="size-2.5 rounded-full bg-rose-400/70" />
                <span className="size-2.5 rounded-full bg-amber-300/70" />
                <span className="size-2.5 rounded-full bg-emerald-300/70" />
                <span className="ml-2">Example flow · not a live session</span>
              </div>
              <div className="space-y-3 p-4 sm:p-6">
                <div className="rounded-2xl border border-cyan-300/15 bg-cyan-300/6 p-4">
                  <div className="mb-2 flex items-center justify-between font-mono text-[11px] uppercase tracking-widest text-cyan-200">
                    <span>DSH planner</span>
                    <span>primary</span>
                  </div>
                  <p className="text-sm leading-6 text-slate-200">
                    Research current browser interception patterns. Prefer
                    official sources, then compare community findings.
                  </p>
                </div>
                <div className="ml-5 rounded-2xl border border-white/9 bg-white/3 p-4">
                  <div className="mb-3 flex items-center gap-2 font-mono text-[11px] text-emerald-200">
                    <Search className="size-3.5" />{' '}
                    mcp__halo_research__web_search
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center font-mono text-[10px] text-slate-400">
                    <span className="rounded-lg bg-black/20 px-2 py-2">
                      3 sources
                    </span>
                    <span className="rounded-lg bg-black/20 px-2 py-2">
                      cache: miss
                    </span>
                    <span className="rounded-lg bg-black/20 px-2 py-2">
                      schema 1.5
                    </span>
                  </div>
                </div>
                <div className="ml-10 rounded-2xl border border-white/9 bg-white/3 p-4">
                  <div className="mb-3 flex items-center gap-2 font-mono text-[11px] text-cyan-100">
                    <Globe2 className="size-3.5" /> web_crawl · owned Chrome
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-black/30">
                    <div className="h-full w-[78%] rounded-full bg-gradient-to-r from-cyan-300 to-emerald-300" />
                  </div>
                  <p className="mt-3 font-mono text-[10px] text-slate-500">
                    route validated · evidence preserved · cursor signed
                  </p>
                </div>
                <div className="flex items-center justify-between rounded-2xl border border-emerald-300/15 bg-emerald-300/6 p-4 text-sm">
                  <span className="flex items-center gap-2 text-emerald-100">
                    <CheckCircle2 className="size-4" /> Source-backed packet
                    ready
                  </span>
                  <span className="font-mono text-[10px] text-slate-400">
                    2,000 chars
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="architecture" className="border-b border-white/8 py-24">
        <div className="mx-auto grid max-w-7xl gap-12 px-5 lg:grid-cols-[.8fr_1.2fr] lg:px-8">
          <div>
            <p className="section-kicker">Architecture</p>
            <h2 className="section-title">
              The shared layer local agents were missing.
            </h2>
            <p className="section-copy">
              One process owns discovery budgets, cache, browser concurrency,
              durable research jobs, and encrypted research connections. Every
              host gets the same semantics; DSH stays in charge.
            </p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/[.025] p-5 sm:p-8">
            <div className="grid gap-4 sm:grid-cols-[1fr_auto_1.2fr] sm:items-center">
              <div className="space-y-2">
                {hosts.map((host, index) => (
                  <div
                    key={host}
                    className={cn(
                      'flex items-center gap-3 rounded-xl border px-4 py-3 text-sm',
                      index === 0
                        ? 'border-cyan-300/25 bg-cyan-300/8 text-cyan-100'
                        : 'border-white/8 bg-black/15 text-slate-300',
                    )}
                  >
                    <Bot className="size-4" />
                    {host}
                    {index === 0 && (
                      <span className="ml-auto font-mono text-[9px] uppercase text-cyan-300">
                        primary
                      </span>
                    )}
                  </div>
                ))}
              </div>
              <ArrowRight className="hidden text-cyan-300/60 sm:block" />
              <div className="rounded-2xl border border-emerald-300/20 bg-[#081b20] p-5">
                <div className="flex items-center gap-3">
                  <span className="grid size-10 place-items-center rounded-xl bg-emerald-300/10 text-emerald-200">
                    <Network />
                  </span>
                  <div>
                    <strong className="block text-white">Halo Gateway</strong>
                    <span className="font-mono text-[10px] text-slate-500">
                      127.0.0.1:8765/mcp
                    </span>
                  </div>
                </div>
                <div className="mt-5 space-y-2 font-mono text-[10px] text-slate-400">
                  {[
                    'search + deep research + Crawl4AI',
                    'GitHub + transcripts + communities',
                    'cache + queues + signed cursors',
                    'DPAPI vault + OAuth PKCE',
                    'research jobs + cookie-import review',
                  ].map((line) => (
                    <div
                      key={line}
                      className="rounded-lg border border-white/6 bg-black/20 px-3 py-2"
                    >
                      {line}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="capabilities" className="py-24">
        <div className="mx-auto max-w-7xl px-5 lg:px-8">
          <div className="max-w-3xl">
            <p className="section-kicker">Complete research surface</p>
            <h2 className="section-title">
              Built for the messy web, not a demo query.
            </h2>
            <p className="section-copy">
              Ordinary pages stay fast. JavaScript gets a real browser. Long
              research becomes a resumable job. Authenticated work stays
              operator-owned.
            </p>
          </div>
          <div className="mt-14 grid gap-px overflow-hidden rounded-3xl border border-white/9 bg-white/9 md:grid-cols-2 lg:grid-cols-3">
            {capabilities.map(({ icon: Icon, title, body }) => (
              <article
                key={title}
                className="bg-background p-7 transition hover:bg-white/[.025] sm:p-8"
              >
                <span className="mb-6 grid size-11 place-items-center rounded-xl border border-cyan-300/18 bg-cyan-300/7 text-cyan-200">
                  <Icon />
                </span>
                <h3 className="text-lg font-semibold text-white">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-400">{body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="border-y border-white/8 bg-[#08131e] py-24">
        <div className="mx-auto grid max-w-7xl gap-12 px-5 lg:grid-cols-[.75fr_1.25fr] lg:px-8">
          <div>
            <p className="section-kicker">Tool contract</p>
            <h2 className="section-title">
              Fourteen tools. Find, read, and cite.
            </h2>
            <p className="section-copy">
              One shared toolkit for finding sources, reading their contents,
              and returning citations. Account operations are outside its scope.
            </p>
          </div>
          <div className="space-y-3">
            {toolGroups.map(([label, tools], index) => (
              <div
                key={label}
                className="grid gap-2 rounded-2xl border border-white/8 bg-black/15 p-4 sm:grid-cols-[140px_1fr] sm:items-center"
              >
                <span className="flex items-center gap-2 text-sm font-medium text-white">
                  <span className="font-mono text-[10px] text-cyan-300">
                    0{index + 1}
                  </span>
                  {label}
                </span>
                <code className="overflow-x-auto text-xs text-slate-400">
                  {tools}
                </code>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="proof" className="py-24">
        <div className="mx-auto grid max-w-7xl gap-14 px-5 lg:grid-cols-2 lg:items-center lg:px-8">
          <div>
            <p className="section-kicker">Evidence, not adjectives</p>
            <h2 className="section-title">
              What is verified—and what is still open.
            </h2>
            <p className="section-copy">
              Local regression tests, public-source checks, and disposable
              browser/process tests provide different kinds of evidence. None
              replaces a complete successful research workflow through DSH.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <span className="proof-pill">176 local tests passed</span>
              <span className="proof-pill">Windows CI for delivered checkpoints</span>
              <span className="proof-pill">Schema 1.5</span>
              <span className="proof-pill">DB schema 3</span>
            </div>
            <p className="mt-6 text-sm leading-6 text-amber-200">
              The latest DSH workflow failed before search could run because of
              a DSH tools-package mismatch. That repair still needs approval.
              Real-world login and app-bound cookies, human challenges, optional
              provider routing, and full installation/stress acceptance remain open.
            </p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/[.025] p-6 sm:p-8">
            <div className="mb-6 flex items-center justify-between">
              <span className="font-mono text-xs text-slate-400">
                acceptance / live
              </span>
              <span className="flex items-center gap-2 text-sm text-amber-200">
                <span className="size-2 rounded-full bg-amber-300" />{' '}
                partial acceptance
              </span>
            </div>
            {[
              'MCP surface — 14 research tools',
              'Public pages, JavaScript, PDF, captions and community evidence',
              'Authenticated read-only GitHub adapter canary',
              'Disposable Chrome cookie-only login fixture',
              'Native research-job crash/restart fixture',
            ].map((line) => (
              <div
                key={line}
                className="flex items-center gap-3 border-t border-white/7 py-4 text-sm text-slate-300"
              >
                <CheckCircle2 className="size-4 text-emerald-300" />
                {line}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-y border-white/8 bg-gradient-to-b from-cyan-300/[.035] to-transparent py-24">
        <div className="mx-auto grid max-w-7xl gap-12 px-5 lg:grid-cols-2 lg:px-8">
          <div>
            <p className="section-kicker">Authority boundary</p>
            <h2 className="section-title">
              Find sources. Return evidence.
            </h2>
            <p className="section-copy">
              Models gather evidence across the public web and exact named local
              targets. Research login sessions help read restricted sources;
              they do not turn the Gateway into an account-operation system.
            </p>
          </div>
          <ol className="space-y-3">
            {[
              'Search for relevant sources.',
              'Read pages, documents, transcripts, and discussions.',
              'Compare evidence and disclose missing or partial results.',
              'Return usable citations to DSH.',
            ].map((step, index) => (
              <li
                key={step}
                className="flex gap-4 rounded-2xl border border-white/8 bg-black/15 p-4"
              >
                <span className="grid size-8 shrink-0 place-items-center rounded-full bg-cyan-300/10 font-mono text-xs text-cyan-200">
                  {index + 1}
                </span>
                <span className="pt-1 text-sm leading-6 text-slate-300">
                  {step}
                </span>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section id="start" className="py-24">
        <div className="mx-auto max-w-5xl px-5 text-center lg:px-8">
          <p className="section-kicker">Version 0.2.0</p>
          <h2 className="mx-auto max-w-3xl text-balance text-4xl font-semibold tracking-[-0.04em] text-white sm:text-5xl">
            Install the local Gateway, then verify your host connection.
          </h2>
          <div className="mx-auto mt-9 flex max-w-3xl items-center gap-4 rounded-2xl border border-white/10 bg-[#08131e] p-4 text-left shadow-xl shadow-black/20">
            <Terminal className="size-5 shrink-0 text-cyan-200" />
            <code className="min-w-0 flex-1 overflow-x-auto text-sm text-slate-300">
              .\scripts\Install-HaloResearch.ps1 -RegisterTask -RegisterHosts
              -Start
            </code>
          </div>
          <div className="mt-7 flex flex-wrap justify-center gap-3">
            <a
              href="https://github.com/scottconverse/halo-research-gateway"
              className={cn(
                buttonVariants({ size: 'lg' }),
                'h-11 bg-cyan-200 px-5 text-slate-950 hover:bg-cyan-100',
              )}
            >
              <Code2 /> Open repository <ExternalLink />
            </a>
            <a
              href="https://github.com/scottconverse/halo-research-gateway/blob/main/docs/USER-MANUAL.md"
              className={cn(
                buttonVariants({ variant: 'outline', size: 'lg' }),
                'h-11 border-white/15 bg-white/4 px-5 text-white hover:bg-white/9',
              )}
            >
              <BookOpen /> Read the manual
            </a>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/8 py-10">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-5 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <div className="flex items-center gap-3">
            <span className="grid size-8 place-items-center rounded-lg border border-cyan-300/20 bg-cyan-300/7 text-cyan-200">
              <Braces className="size-4" />
            </span>
            <span>Halo Research Gateway · v0.2.0</span>
          </div>
          <p>DSH-first. Local by default. Evidence all the way down.</p>
        </div>
      </footer>
    </main>
  );
}
