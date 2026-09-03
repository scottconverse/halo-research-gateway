"""Focused loopback operator console. No model can access its CSRF or approval state."""

from __future__ import annotations

import json


def render_operator(csrf: str, health: dict) -> str:
    return rf"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Halo Research Gateway</title>
<style>
body{{font-family:system-ui;background:#071018;color:#dbeafe;margin:0}}main{{max-width:1300px;margin:auto;padding:28px}}
h1{{color:#67e8f9}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px}}
section{{background:#0d1b2a;border:1px solid #1e3a5f;border-radius:14px;padding:18px}}pre{{color:#a7f3d0;white-space:pre-wrap;overflow:auto;max-height:420px}}
.ok{{color:#6ee7b7}}button{{background:#0e7490;color:white;border:0;border-radius:8px;padding:9px 13px;margin:4px}}
button:disabled{{opacity:.45;cursor:not-allowed}}button:focus-visible{{outline:3px solid #67e8f9;outline-offset:3px}}
input,select,textarea{{box-sizing:border-box;width:100%;margin:5px 0;padding:9px;background:#071018;color:#dbeafe;border:1px solid #315477;border-radius:7px}}
label{{display:block;margin-top:7px}}small{{color:#93c5fd}}details{{margin:10px 0}}.plan{{border-top:1px solid #315477;padding-top:10px;margin-top:10px}}
</style></head><body><main><h1>Halo Research Gateway</h1>
<p class="ok">Loopback service is running. Models never receive vault secrets, CSRF state, OAuth verifiers, or approval authority.</p>
<div class="grid">
<section><h2>Health</h2><pre id="health">{json.dumps(health, indent=2)}</pre></section>
<section><h2>Connections</h2><p><small>Secrets are DPAPI-encrypted and never returned.</small></p>
<details open><summary>API key, token, or password</summary><form id="connection">
<input name="provider" placeholder="Provider" required><input name="label" placeholder="Account label" required>
<select name="type"><option>api_key</option><option>token</option><option>password</option></select>
<input name="secret" type="password" placeholder="Secret value" required><button>Save encrypted connection</button></form></details>
<details><summary>GitHub App (read-only research)</summary><form id="githubApp">
<input name="label" placeholder="Account label" required><input name="app_id" placeholder="GitHub App ID" required>
<input name="installation_id" placeholder="Installation ID" required>
<textarea name="private_key_pem" rows="7" placeholder="Paste the GitHub App private key PEM" required></textarea>
<small>Use a separate read-only Research App. The key is DPAPI-encrypted and installation tokens stay inside the Gateway.</small>
<button>Save encrypted GitHub App</button></form></details>
<details><summary>OAuth Authorization Code + PKCE</summary><form id="oauth">
<input name="provider" placeholder="Provider" required><input name="label" placeholder="Account label" required>
<input name="authorization_endpoint" placeholder="https://provider.example/authorize" required>
<input name="token_endpoint" placeholder="https://provider.example/token" required><input name="client_id" placeholder="Client ID" required>
<input name="client_secret" type="password" placeholder="Client secret (only if provider requires it)">
<input name="scopes" placeholder="Scopes separated by spaces"><button>Open provider consent</button></form><pre id="oauthState"></pre></details>
<pre id="connections">Loading...</pre></section>
<section><h2>Research login-session import</h2><p><small>Preview first. Chrome must be closed before execution. Only cookies and their encryption metadata are copied; not passwords or other personal profile data. Use a dedicated research source profile: cookie import is not filtered by site. The source is never used live.</small></p>
<form id="chromeImport"><input name="source_profile" placeholder="Full source profile path" required>
<input name="destination_name" placeholder="Gateway profile name" required>
<input name="categories" value="cookies" readonly aria-label="Only cookies can be imported">
<select name="behavior"><option>replace</option><option>merge</option></select><button>Preview import</button></form></section>
<section><h2>Sign in to a research source</h2>
<p>Open one public source in an isolated Gateway browser. You handle the login or challenge; the model cannot click or submit forms.</p>
<form id="researchLogin">
<label>Public research page<input name="url" type="url" placeholder="https://source.example/article" required></label>
<label>Existing Gateway research profile<input name="profile" maxlength="64" placeholder="Profile name used during cookie import" required></label>
<button id="researchOpen">Open research page</button></form>
<p><small>Two-minute limit, including startup. No personal browser is attached. Same-tab public login redirects are allowed; popups and private/local targets are not. Only cookies are retained in memory, until restart or another completed handoff. The imported profile is not changed.</small></p>
<button id="researchDone" type="button" disabled>Done — use temporary session</button>
<button id="researchCancel" type="button" disabled>Cancel handoff</button>
<p id="researchMessage" role="status" aria-live="polite">No handoff is active.</p>
<pre id="researchState"></pre></section>
<section><h2>Session import review and receipts</h2><p>Review the immutable plan. Approval and execution are separate clicks.</p>
<div id="importPlans">Loading...</div><pre id="receipts"></pre></section>
<section><h2>Jobs and provider budgets</h2><pre id="jobs">Loading...</pre></section>
</div><script>
window.HALO_CSRF={json.dumps(csrf)};const approvals={{}};let researchSessionId=null;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
async function approvePlan(id){{let r=await fetch('/operator/api/imports/chrome/'+encodeURIComponent(id)+'/approve',{{method:'POST',headers:{{'x-halo-csrf':HALO_CSRF}}}});let v=await r.json();if(!r.ok)return alert(v.error||'Plan unavailable');approvals[id]=v.approval_token;alert('Session import approved. Review once more, then execute the import.');loadState()}}
async function executeImport(id){{if(!approvals[id])return alert('Approve this exact plan first.');let key=crypto.randomUUID();let r=await fetch('/operator/api/imports/chrome/'+encodeURIComponent(id)+'/execute',{{method:'POST',headers:{{'content-type':'application/json','x-halo-csrf':HALO_CSRF}},body:JSON.stringify({{approval_token:approvals[id],idempotency_key:key}})}});let v=await r.json();alert(r.ok?'Import completed with a redacted receipt.':(v.error||'Import failed'));loadState()}}
function renderPlans(plans){{return plans.length?plans.map(p=>'<div class="plan"><pre>'+esc(JSON.stringify(p,null,2))+'</pre>'+(p.status==='awaiting_approval'?'<button onclick="approvePlan(\''+esc(p.plan_id)+'\')">Approve exact plan</button>':'')+(p.preview&&p.preview.action==='chrome_import'&&p.status!=='executed'?'<button onclick="executeImport(\''+esc(p.plan_id)+'\')">Execute approved import</button>':'')+'</div>').join(''):'No prepared plans.'}}
function showResearch(s){{researchSessionId=s.session_id||null;researchState.textContent=JSON.stringify(s,null,2);researchOpen.disabled=['opening','waiting_for_operator'].includes(s.state);researchDone.disabled=s.state!=='waiting_for_operator';researchCancel.disabled=!researchOpen.disabled;researchMessage.textContent=({{idle:'No handoff is active.',opening:'Opening the isolated browser. The two-minute clock has started.',waiting_for_operator:'Complete the human step in the Gateway browser, then choose Done here. Cancel discards this attempt.',ready_to_retry:'Temporary cookies are ready. Ask DSH to retry web_crawl with mode managed_profile and profile '+(s.profile||'')+'. This does not prove the login or challenge succeeded.',cancelled:'Handoff cancelled. No cookies from this attempt were retained.',timed_out:'Handoff timed out. No new cookies were retained. You can open the source again.',failed:'The handoff failed or its window was closed. No new cookies were retained. Check that Chrome and the research profile are available.'}})[s.state]||'Session status unavailable.'}}
async function researchRequest(path,body){{try{{let r=await fetch('/operator/api/research-session'+path,{{method:'POST',headers:{{'content-type':'application/json','x-halo-csrf':HALO_CSRF}},body:JSON.stringify(body)}});let s=await r.json();if(!r.ok){{researchMessage.textContent=s.error||'Research session request failed.';return}}showResearch(s)}}catch(e){{researchMessage.textContent='Cannot reach the Gateway. Session state is unknown; reconnect before retrying.'}}}}
researchLogin.onsubmit=async e=>{{e.preventDefault();let f=new FormData(researchLogin);await researchRequest('',{{url:f.get('url'),profile:f.get('profile')}})}};
researchDone.onclick=()=>researchRequest('/done',{{session_id:researchSessionId}});
researchCancel.onclick=()=>researchRequest('/cancel',{{session_id:researchSessionId}});
async function loadState(){{let s=await (await fetch('/operator/api/state')).json();health.textContent=JSON.stringify(s.health,null,2);connections.textContent=JSON.stringify(s.connections,null,2);importPlans.innerHTML=renderPlans(s.imports);receipts.textContent=JSON.stringify(s.receipts,null,2);jobs.textContent=JSON.stringify({{jobs:s.jobs,providers:s.stats.providers,optional_providers:s.stats.optional_providers}},null,2);showResearch(s.research_session)}}
connection.onsubmit=async e=>{{e.preventDefault();let f=new FormData(connection);let r=await fetch('/operator/api/connections',{{method:'POST',headers:{{'content-type':'application/json','x-halo-csrf':HALO_CSRF}},body:JSON.stringify({{provider:f.get('provider'),label:f.get('label'),type:f.get('type'),secret:{{value:f.get('secret')}}}})}});if(!r.ok)alert('Connection was not saved');connection.reset();loadState()}};
githubApp.onsubmit=async e=>{{e.preventDefault();let f=new FormData(githubApp);let body={{provider:'GitHub App',label:f.get('label'),type:'api_key',scopes:['metadata:read','contents:read','issues:read','pull_requests:read','discussions:read','actions:read','checks:read','commit_statuses:read'],secret:{{app_id:f.get('app_id'),installation_id:f.get('installation_id'),private_key_pem:f.get('private_key_pem')}}}};let r=await fetch('/operator/api/connections',{{method:'POST',headers:{{'content-type':'application/json','x-halo-csrf':HALO_CSRF}},body:JSON.stringify(body)}});if(!r.ok)return alert('GitHub App connection was not saved');githubApp.reset();loadState()}};
oauth.onsubmit=async e=>{{e.preventDefault();let f=new FormData(oauth);let body={{provider:f.get('provider'),label:f.get('label'),authorization_endpoint:f.get('authorization_endpoint'),token_endpoint:f.get('token_endpoint'),client_id:f.get('client_id'),client_secret:f.get('client_secret')||null,scopes:String(f.get('scopes')||'').split(/\s+/).filter(Boolean)}};let r=await fetch('/operator/api/oauth',{{method:'POST',headers:{{'content-type':'application/json','x-halo-csrf':HALO_CSRF}},body:JSON.stringify(body)}});let v=await r.json();if(!r.ok)return alert(v.error||'OAuth flow was not started');window.open(v.authorization_url,'_blank','noopener');oauthState.textContent='Waiting for provider consent: '+v.flow_id;let timer=setInterval(async()=>{{let s=await (await fetch('/operator/api/oauth/'+v.flow_id)).json();oauthState.textContent=JSON.stringify(s,null,2);if(s.state==='complete'||s.state==='failed'||s.state==='unavailable'){{clearInterval(timer);loadState()}}}},1500)}};
chromeImport.onsubmit=async e=>{{e.preventDefault();let f=new FormData(chromeImport);let body={{source_profile:f.get('source_profile'),destination_name:f.get('destination_name'),categories:String(f.get('categories')||'').split(/\s+/).filter(Boolean),behavior:f.get('behavior')}};let r=await fetch('/operator/api/imports/chrome',{{method:'POST',headers:{{'content-type':'application/json','x-halo-csrf':HALO_CSRF}},body:JSON.stringify(body)}});let v=await r.json();if(!r.ok)alert(v.error||'Import preview failed');else alert('Preview created. Review it in Session import review.');loadState()}};
loadState();setInterval(loadState,5000);
</script></main></body></html>"""
