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
input,select{{box-sizing:border-box;width:100%;margin:5px 0;padding:9px;background:#071018;color:#dbeafe;border:1px solid #315477;border-radius:7px}}
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
<details><summary>OAuth Authorization Code + PKCE</summary><form id="oauth">
<input name="provider" placeholder="Provider" required><input name="label" placeholder="Account label" required>
<input name="authorization_endpoint" placeholder="https://provider.example/authorize" required>
<input name="token_endpoint" placeholder="https://provider.example/token" required><input name="client_id" placeholder="Client ID" required>
<input name="client_secret" type="password" placeholder="Client secret (only if provider requires it)">
<input name="scopes" placeholder="Scopes separated by spaces"><button>Open provider consent</button></form><pre id="oauthState"></pre></details>
<pre id="connections">Loading...</pre></section>
<section><h2>Chrome profile import</h2><p><small>Preview first. Chrome must be closed before execution. The source is copied into a gateway-owned profile; it is never used live.</small></p>
<form id="chromeImport"><input name="source_profile" placeholder="Full source profile path" required>
<input name="destination_name" placeholder="Gateway profile name" required>
<input name="categories" placeholder="bookmarks history cookies saved_passwords autofill payment_metadata extensions settings">
<label><input style="width:auto" name="complete" type="checkbox"> Complete profile, including saved passwords</label>
<select name="behavior"><option>replace</option><option>merge</option></select><button>Preview import</button></form></section>
<section><h2>Actions, imports, and receipts</h2><p>Review the immutable plan. Approval and execution are separate clicks.</p>
<div id="actionPlans">Loading...</div><pre id="receipts"></pre></section>
<section><h2>Jobs and provider budgets</h2><pre id="jobs">Loading...</pre></section>
</div><script>
window.HALO_CSRF={json.dumps(csrf)};const approvals={{}};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
async function approvePlan(id){{let r=await fetch('/operator/api/actions/'+encodeURIComponent(id)+'/approve',{{method:'POST',headers:{{'x-halo-csrf':HALO_CSRF}}}});let v=await r.json();if(!r.ok)return alert(v.error||'Plan unavailable');approvals[id]=v.approval_token;alert('Exact plan approved. Review once more, then execute or copy the token for the matching MCP execution.');loadState()}}
async function executeImport(id){{if(!approvals[id])return alert('Approve this exact plan first.');let key=crypto.randomUUID();let r=await fetch('/operator/api/imports/chrome/'+encodeURIComponent(id)+'/execute',{{method:'POST',headers:{{'content-type':'application/json','x-halo-csrf':HALO_CSRF}},body:JSON.stringify({{approval_token:approvals[id],idempotency_key:key}})}});let v=await r.json();alert(r.ok?'Import completed with a redacted receipt.':(v.error||'Import failed'));loadState()}}
function renderPlans(plans){{return plans.length?plans.map(p=>'<div class="plan"><pre>'+esc(JSON.stringify(p,null,2))+'</pre>'+(p.status==='awaiting_approval'?'<button onclick="approvePlan(\''+esc(p.plan_id)+'\')">Approve exact plan</button>':'')+(p.preview&&p.preview.action==='chrome_import'&&p.status!=='executed'?'<button onclick="executeImport(\''+esc(p.plan_id)+'\')">Execute approved import</button>':'')+'</div>').join(''):'No prepared plans.'}}
async function loadState(){{let s=await (await fetch('/operator/api/state')).json();health.textContent=JSON.stringify(s.health,null,2);connections.textContent=JSON.stringify(s.connections,null,2);actionPlans.innerHTML=renderPlans(s.actions);receipts.textContent=JSON.stringify(s.receipts,null,2);jobs.textContent=JSON.stringify({{jobs:s.jobs,providers:s.stats.providers,optional_providers:s.stats.optional_providers}},null,2)}}
connection.onsubmit=async e=>{{e.preventDefault();let f=new FormData(connection);let r=await fetch('/operator/api/connections',{{method:'POST',headers:{{'content-type':'application/json','x-halo-csrf':HALO_CSRF}},body:JSON.stringify({{provider:f.get('provider'),label:f.get('label'),type:f.get('type'),secret:{{value:f.get('secret')}}}})}});if(!r.ok)alert('Connection was not saved');connection.reset();loadState()}};
oauth.onsubmit=async e=>{{e.preventDefault();let f=new FormData(oauth);let body={{provider:f.get('provider'),label:f.get('label'),authorization_endpoint:f.get('authorization_endpoint'),token_endpoint:f.get('token_endpoint'),client_id:f.get('client_id'),client_secret:f.get('client_secret')||null,scopes:String(f.get('scopes')||'').split(/\s+/).filter(Boolean)}};let r=await fetch('/operator/api/oauth',{{method:'POST',headers:{{'content-type':'application/json','x-halo-csrf':HALO_CSRF}},body:JSON.stringify(body)}});let v=await r.json();if(!r.ok)return alert(v.error||'OAuth flow was not started');window.open(v.authorization_url,'_blank','noopener');oauthState.textContent='Waiting for provider consent: '+v.flow_id;let timer=setInterval(async()=>{{let s=await (await fetch('/operator/api/oauth/'+v.flow_id)).json();oauthState.textContent=JSON.stringify(s,null,2);if(s.state==='complete'||s.state==='failed'||s.state==='unavailable'){{clearInterval(timer);loadState()}}}},1500)}};
chromeImport.onsubmit=async e=>{{e.preventDefault();let f=new FormData(chromeImport);let body={{source_profile:f.get('source_profile'),destination_name:f.get('destination_name'),categories:String(f.get('categories')||'').split(/\s+/).filter(Boolean),complete:f.get('complete')==='on',behavior:f.get('behavior')}};let r=await fetch('/operator/api/imports/chrome',{{method:'POST',headers:{{'content-type':'application/json','x-halo-csrf':HALO_CSRF}},body:JSON.stringify(body)}});let v=await r.json();if(!r.ok)alert(v.error||'Import preview failed');else alert('Preview created. Review and approve it in Actions.');loadState()}};
loadState();setInterval(loadState,5000);
</script></main></body></html>"""
