import os
import time
import threading
import random
import requests
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
STARTING_CASH = 10000.0
state_lock = threading.Lock()
state = {
    "cash": STARTING_CASH,
    "starting_cash": STARTING_CASH,
    "positions": [],
    "trades": [],
    "prices": {"BTC": 65000.0, "ETH": 3200.0, "SOL": 150.0},
    "updated": time.time(),
    "running": True,
}
offset = 0

HTML = r"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ROXYU SIM — Paper Trading</title>
<style>
:root{--bg:#080b0d;--panel:#101719;--line:#243136;--green:#7dff9b;--muted:#9aabad;--red:#ff6b79}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top right,#123021 0,transparent 30%),var(--bg);color:#eff8f1;font:15px system-ui,Arial}
header{padding:22px 18px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap}
.brand{font-weight:900;letter-spacing:2px}.brand span{color:var(--green)}.pill{border:1px solid #285c3a;border-radius:30px;padding:7px 10px;color:var(--green);font-size:12px}
main{max-width:1100px;margin:auto;padding:18px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.panel{background:linear-gradient(145deg,#121b1d,#0d1214);border:1px solid var(--line);border-radius:16px;padding:16px;margin-bottom:14px}
.label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:1px}.value{font-size:24px;font-weight:800;margin-top:8px}.green{color:var(--green)}.muted{color:var(--muted)}h2{font-size:16px;margin:0 0 14px}
.row{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:12px 0;border-bottom:1px solid #1b292d}.row:last-child{border:0}
button{background:var(--green);color:#07100a;border:0;border-radius:10px;padding:10px 14px;font-weight:800;cursor:pointer}button.secondary{background:#1a282b;color:#eff8f1;border:1px solid #304347}button.danger{background:#3a171c;color:#ff9ba4;border:1px solid #70313a}
.actions{display:flex;gap:8px;flex-wrap:wrap}.tradeform{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}select,input{background:#081012;color:#eff8f1;border:1px solid #304347;border-radius:9px;padding:10px;min-width:100px}
.note{font-size:12px;color:var(--muted);line-height:1.5}.tablewrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:500px}td,th{text-align:left;padding:10px;border-bottom:1px solid #1b292d;font-size:13px}th{color:var(--muted);font-weight:600}
@media(max-width:700px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.value{font-size:20px}main{padding:12px}}
</style></head><body>
<header><div class="brand">ROXYU <span>SIM</span><div class="muted" style="font-size:11px;font-weight:500;letter-spacing:1px">PAPER TRADING LAB</div></div><div class="pill">● SIMULASI • UANG VIRTUAL</div></header>
<main>
<div class="grid">
 <div class="panel"><div class="label">Saldo virtual</div><div class="value" id="cash">—</div></div>
 <div class="panel"><div class="label">Nilai posisi</div><div class="value" id="positionsValue">—</div></div>
 <div class="panel"><div class="label">Ekuitas</div><div class="value" id="equity">—</div></div>
 <div class="panel"><div class="label">Untung/rugi total</div><div class="value" id="pnl">—</div></div>
</div>
<div class="panel"><h2>Market watch <span class="muted">/ harga simulasi</span></h2><div id="markets"></div><div class="note">Harga bergerak secara acak untuk latihan. Ini bukan harga pasar langsung dan bukan saran investasi.</div></div>
<div class="panel"><h2>Quick trade</h2>
<div class="tradeform"><select id="asset"><option>BTC</option><option>ETH</option><option>SOL</option></select><input id="amount" type="number" min="1" step="1" value="250" aria-label="Nominal virtual USD"><button onclick="trade('buy')">BUY / Beli</button><button class="danger" onclick="trade('sell')">SELL / Jual</button></div>
<div class="note">Masukkan nominal USD virtual. BUY membeli aset; SELL menjual seluruh posisi pada aset terpilih.</div>
<div id="message" class="note" style="margin-top:10px"></div></div>
<div class="panel"><h2>Open positions</h2><div class="tablewrap"><table><thead><tr><th>Aset</th><th>Jumlah</th><th>Harga masuk</th><th>Harga kini</th><th>Untung/rugi</th></tr></thead><tbody id="positions"></tbody></table></div></div>
<div class="panel"><h2>Trade history</h2><div class="tablewrap"><table><thead><tr><th>Waktu</th><th>Aksi</th><th>Aset</th><th>Nominal</th><th>Harga</th><th>Status</th></tr></thead><tbody id="history"></tbody></table></div><div class="actions"><button class="secondary" onclick="resetSim()">Reset simulasi</button></div></div>
<div class="panel"><h2>Telegram commands</h2><div class="note">/start · /status · /prices · /positions · /buy BTC 250 · /sell BTC · /reset</div><div class="note" style="margin-top:8px">Dashboard ini memakai saldo virtual. Jangan masukkan token bot ke halaman ini atau membagikannya ke orang lain.</div></div>
</main>
<script>
const money=n=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2}).format(n);
async function load(){try{let r=await fetch('/api/state');let s=await r.json();
document.getElementById('cash').textContent=money(s.cash);
document.getElementById('positionsValue').textContent=money(s.positions_value);
document.getElementById('equity').textContent=money(s.equity);
let p=document.getElementById('pnl');p.textContent=(s.pnl>=0?'+':'')+money(s.pnl);p.className='value '+(s.pnl>=0?'green':''); 
document.getElementById('markets').innerHTML=Object.entries(s.prices).map(([a,v])=>`<div class="row"><b>${a}/USD</b><span>${money(v)}</span></div>`).join('');
document.getElementById('positions').innerHTML=s.positions.length?s.positions.map(x=>`<tr><td>${x.asset}</td><td>${x.qty.toFixed(6)}</td><td>${money(x.entry)}</td><td>${money(s.prices[x.asset])}</td><td class="${x.pnl>=0?'green':''}">${money(x.pnl)}</td></tr>`).join(''):'<tr><td colspan="5" class="muted">Belum ada posisi terbuka.</td></tr>';
document.getElementById('history').innerHTML=s.trades.slice().reverse().map(x=>`<tr><td>${x.time}</td><td>${x.side}</td><td>${x.asset}</td><td>${money(x.amount)}</td><td>${money(x.price)}</td><td>${x.status}</td></tr>`).join('')||'<tr><td colspan="6" class="muted">Belum ada transaksi.</td></tr>';
}catch(e){}}
async function trade(side){let asset=document.getElementById('asset').value,amount=Number(document.getElementById('amount').value||0);let r=await fetch('/api/trade',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({side,asset,amount})});let d=await r.json();document.getElementById('message').textContent=d.message;load();}
async function resetSim(){if(!confirm('Reset saldo dan semua transaksi simulasi?'))return;let r=await fetch('/api/reset',{method:'POST'});let d=await r.json();document.getElementById('message').textContent=d.message;load();}
load();setInterval(load,4000);
</script></body></html>"""

def snapshot():
    with state_lock:
        positions = []
        positions_value = 0.0
        unrealized = 0.0
        for p in state["positions"]:
            price = state["prices"][p["asset"]]
            value = p["qty"] * price
            pnl = (price - p["entry"]) * p["qty"]
            positions_value += value
            unrealized += pnl
            positions.append({**p, "pnl": pnl, "value": value})
        equity = state["cash"] + positions_value
        return {
            "cash": round(state["cash"], 2),
            "positions_value": round(positions_value, 2),
            "equity": round(equity, 2),
            "pnl": round(equity - state["starting_cash"], 2),
            "prices": dict(state["prices"]),
            "positions": positions,
            "trades": list(state["trades"][-50:]),
            "running": state["running"],
        }

def execute_trade(side, asset, amount=0):
    asset = asset.upper()
    if asset not in state["prices"]:
        return False, "Aset tidak dikenal. Pilih BTC, ETH, atau SOL."
    with state_lock:
        price = state["prices"][asset]
        if side == "BUY":
            amount = float(amount)
            if amount <= 0:
                return False, "Nominal harus lebih dari 0."
            if amount > state["cash"]:
                return False, "Saldo virtual tidak cukup."
            qty = amount / price
            state["cash"] -= amount
            state["positions"].append({"asset": asset, "qty": qty, "entry": price})
            status = "FILLED (SIM)"
        elif side == "SELL":
            matching = [p for p in state["positions"] if p["asset"] == asset]
            if not matching:
                return False, f"Tidak ada posisi {asset} untuk dijual."
            amount = sum(p["qty"] * price for p in matching)
            state["cash"] += amount
            state["positions"] = [p for p in state["positions"] if p["asset"] != asset]
            status = "CLOSED (SIM)"
        else:
            return False, "Aksi tidak dikenal."
        state["trades"].append({
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + " UTC",
            "side": side, "asset": asset, "amount": round(amount, 2),
            "price": round(price, 2), "status": status
        })
        state["updated"] = time.time()
    return True, f"{side} {asset} berhasil (SIMULASI) senilai ${amount:,.2f} pada ${price:,.2f}. Tidak ada uang asli."

def reset_state():
    with state_lock:
        state["cash"] = STARTING_CASH
        state["positions"] = []
        state["trades"] = []
        state["prices"] = {"BTC": 65000.0, "ETH": 3200.0, "SOL": 150.0}
        state["running"] = True

@app.get("/")
def home():
    return render_template_string(HTML)

@app.get("/api/state")
def api_state():
    # Random walk prices, solely for simulation.
    with state_lock:
        for a, p in state["prices"].items():
            state["prices"][a] = max(0.01, p * (1 + random.uniform(-0.002, 0.002)))
    return jsonify(snapshot())

@app.post("/api/trade")
def api_trade():
    data = request.get_json(silent=True) or {}
    ok, message = execute_trade(str(data.get("side", "")).upper(), str(data.get("asset", "")), data.get("amount", 0))
    return jsonify({"ok": ok, "message": message}), (200 if ok else 400)

@app.post("/api/reset")
def api_reset():
    reset_state()
    return jsonify({"ok": True, "message": "Simulasi direset. Saldo kembali $10,000 virtual."})

def telegram_send(chat_id, text):
    if not BOT_TOKEN:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": chat_id, "text": text}, timeout=15)
    except requests.RequestException:
        pass

def telegram_handle(msg):
    chat_id = msg.get("chat", {}).get("id")
    text = (msg.get("text") or "").strip()
    if not chat_id or not text.startswith("/"):
        return
    parts = text.split()
    cmd = parts[0].split("@")[0].lower()
    if cmd in ("/start", "/help"):
        telegram_send(chat_id, "ROXYU SIM — PAPER TRADING\\nPerintah:\\n/status - saldo & P/L\\n/prices - harga simulasi\\n/positions - posisi terbuka\\n/buy BTC 250 - beli $250 virtual\\n/sell BTC - tutup posisi aset\\n/reset - reset saldo virtual\\n/dashboard - URL dashboard (lihat host deployment).\\n\\nSemua transaksi hanya simulasi; bukan trading sungguhan.")
    elif cmd == "/status":
        s = snapshot()
        telegram_send(chat_id, f"ROXYU SIM STATUS\\nSaldo: ${s['cash']:,.2f}\\nNilai posisi: ${s['positions_value']:,.2f}\\nEkuitas: ${s['equity']:,.2f}\\nP/L: ${s['pnl']:,.2f}\\nMode: PAPER TRADING")
    elif cmd == "/prices":
        s = snapshot()
        telegram_send(chat_id, "Harga SIMULASI (bukan harga live):\\n" + "\\n".join(f"{a}: ${p:,.2f}" for a,p in s["prices"].items()))
    elif cmd == "/positions":
        s = snapshot()
        if not s["positions"]:
            telegram_send(chat_id, "Belum ada posisi terbuka.")
        else:
            telegram_send(chat_id, "Posisi terbuka:\\n" + "\\n".join(f"{p['asset']} qty {p['qty']:.6f} | entry ${p['entry']:,.2f} | P/L ${p['pnl']:,.2f}" for p in s["positions"]))
    elif cmd == "/buy":
        if len(parts) != 3:
            telegram_send(chat_id, "Format: /buy BTC 250 (nominal USD virtual)")
        else:
            try:
                ok, answer = execute_trade("BUY", parts[1], float(parts[2]))
                telegram_send(chat_id, answer)
            except ValueError:
                telegram_send(chat_id, "Nominal harus berupa angka. Contoh: /buy BTC 250")
    elif cmd == "/sell":
        if len(parts) != 2:
            telegram_send(chat_id, "Format: /sell BTC")
        else:
            ok, answer = execute_trade("SELL", parts[1])
            telegram_send(chat_id, answer)
    elif cmd == "/reset":
        reset_state()
        telegram_send(chat_id, "Simulasi direset. Saldo kembali $10,000 virtual; posisi dan riwayat dihapus.")
    elif cmd == "/dashboard":
        url = os.environ.get("PUBLIC_URL", "").strip()
        telegram_send(chat_id, ("Dashboard: " + url) if url else "URL dashboard belum diatur. Buka URL web service tempat aplikasi ini di-deploy.")
    else:
        telegram_send(chat_id, "Perintah tidak dikenal. Ketik /help.")

def telegram_polling():
    global offset
    if not BOT_TOKEN:
        print("BOT_TOKEN belum diatur; bot Telegram tidak berjalan.")
        return
    print("Telegram polling started.")
    while True:
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params={"timeout": 25, "offset": offset},
                timeout=35
            )
            payload = response.json()
            if payload.get("ok"):
                for update in payload.get("result", []):
                    offset = update["update_id"] + 1
                    if "message" in update:
                        telegram_handle(update["message"])
        except Exception as exc:
            print("Telegram polling error:", type(exc).__name__)
            time.sleep(5)

if BOT_TOKEN:
    threading.Thread(target=telegram_polling, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
