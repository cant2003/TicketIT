import os, sqlite3, subprocess, io, smtplib
from datetime import datetime
from pathlib import Path
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY','cambia-esta-clave')
DB_PATH = Path(os.getenv('TICKETIT_DB', str(BASE_DIR / 'tickets.db')))
TICKET_TABLE_HINTS = ['tickets','ticket','incidencias','solicitudes']
USER_TABLE_HINTS = ['usuarios_ti','ti_users','usuarios','users','admins','autorizados']
SERVICE_CMDS = {
    'webhook': os.getenv('WEBHOOK_CMD','python webhook_app.py'),
    'worker': os.getenv('WORKER_CMD','python run_worker.py'),
    'ngrok': os.getenv('NGROK_CMD','ngrok http 5000')
}
PROCS = {}


def q(name): return '"' + str(name).replace('"','""') + '"'
def con():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def tables():
    try:
        with con() as c:
            return [r[0] for r in c.execute("select name from sqlite_master where type='table' order by name")]
    except Exception: return []

def cols(table):
    with con() as c: return [r['name'] for r in c.execute(f'pragma table_info({q(table)})')]

def pick_table(hints):
    ts = tables(); lower = {t.lower(): t for t in ts}
    for h in hints:
        if h in lower: return lower[h]
    for t in ts:
        if any(h in t.lower() for h in hints): return t
    return ts[0] if ts else None

def ticket_table(): return pick_table(TICKET_TABLE_HINTS)
def user_table(): return pick_table(USER_TABLE_HINTS)

def find_col(names, possible):
    low = {c.lower(): c for c in names}
    for p in possible:
        if p.lower() in low: return low[p.lower()]
    for c in names:
        if any(p.lower() in c.lower() for p in possible): return c
    return None

def status_class(value):
    s = str(value or '').lower()
    if any(x in s for x in ['abiert','open','nuevo']): return 'abierto'
    if any(x in s for x in ['proceso','pend']): return 'proceso'
    if any(x in s for x in ['cerr','closed','resuelto','cancel']): return 'cerrado'
    return ''

def require_login(): return 'telegram_id' in session

@app.before_request
def guard():
    if request.endpoint in ['login','static']: return
    if request.path.startswith('/api/') and request.endpoint == 'api_login_status': return
    if not require_login(): return redirect(url_for('login'))

@app.route('/', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        telegram_id = request.form.get('telegram_id','').strip()
        ok, username = validate_telegram_id(telegram_id)
        if ok:
            session['telegram_id'] = telegram_id
            session['username'] = username or f'TI {telegram_id}'
            return redirect(url_for('home'))
        error = 'ID de Telegram no autorizado'
    return render_template('login.html', error=error)

def validate_telegram_id(tid):
    if not tid or not DB_PATH.exists(): return False, None
    try:
        ut = user_table(); cs = cols(ut) if ut else []
        idc = find_col(cs, ['telegram_id','chat_id','id_telegram','telegram','user_id'])
        namec = find_col(cs, ['nombre','name','usuario','username'])
        if not idc: return False, None
        with con() as c:
            row = c.execute(f'select * from {q(ut)} where cast({q(idc)} as text)=? limit 1', (tid,)).fetchone()
            return bool(row), (row[namec] if row and namec else None)
    except Exception: return False, None

@app.route('/home')
def home(): return render_template('home.html', user=session.get('username'))
@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))
@app.route('/tickets')
def tickets(): return render_template('tickets.html', table=ticket_table(), db_path=str(DB_PATH))
@app.route('/gestion-ti')
def gestion_ti(): return render_template('gestion_ti.html', table=user_table(), db_path=str(DB_PATH))
@app.route('/launcher')
def launcher(): return render_template('launcher.html')

@app.route('/api/stats')
def api_stats():
    out = {'tickets_new':0,'total':0,'abiertos':0,'proceso':0,'cerrados':0}
    tt = ticket_table()
    if not tt: return jsonify(out)
    try:
        cs = cols(tt); state = find_col(cs,['estado','status','state'])
        with con() as c:
            out['total'] = c.execute(f'select count(*) from {q(tt)}').fetchone()[0]
            if state:
                rows = c.execute(f'select lower(cast({q(state)} as text)) s, count(*) n from {q(tt)} group by s').fetchall()
                for r in rows:
                    cl = status_class(r['s'])
                    if cl == 'abierto': out['abiertos'] += r['n']
                    elif cl == 'proceso': out['proceso'] += r['n']
                    elif cl == 'cerrado': out['cerrados'] += r['n']
                out['tickets_new'] = out['abiertos']
    except Exception as e: out['error_msg'] = str(e)
    return jsonify(out)

@app.route('/api/table/<kind>')
def api_table(kind):
    table = ticket_table() if kind == 'tickets' else user_table()
    if not table: return jsonify({'columns':[], 'rows':[]})
    search = request.args.get('search','').strip().lower(); status = request.args.get('status','').strip().lower()
    try:
        cs = cols(table); stc = find_col(cs,['estado','status','state'])
        with con() as c:
            rows = [dict(r) for r in c.execute(f'select rowid as _rowid, * from {q(table)} order by rowid desc limit 500').fetchall()]
        if search:
            rows = [r for r in rows if search in ' '.join(str(v or '') for k,v in r.items() if k != '_rowid').lower()]
        if status and stc:
            rows = [r for r in rows if status_class(r.get(stc)) == status]
        return jsonify({'columns':cs, 'rows':rows})
    except Exception as e: return jsonify({'columns':['Error'], 'rows':[{'Error':str(e)}]})

@app.route('/api/tickets/<int:rowid>', methods=['PUT'])
def api_ticket_update(rowid):
    tt = ticket_table()
    if not tt: return jsonify({'ok':False,'msg':'No existe tabla de tickets'}), 400
    data = request.json or {}; cs = cols(tt)
    allowed = {k:v for k,v in data.items() if k in cs}
    if not allowed: return jsonify({'ok':False,'msg':'No hay campos válidos para actualizar'}), 400
    try:
        sets = ', '.join(f'{q(k)}=?' for k in allowed)
        params = list(allowed.values()) + [rowid]
        with con() as c:
            c.execute(f'update {q(tt)} set {sets} where rowid=?', params); c.commit()
        return jsonify({'ok':True})
    except Exception as e: return jsonify({'ok':False,'msg':str(e)}), 400

@app.route('/api/users', methods=['POST','DELETE'])
def api_users():
    ut = user_table()
    if not ut: return jsonify({'ok':False,'msg':'No existe tabla de usuarios'}), 400
    cs = cols(ut); idc = find_col(cs,['telegram_id','chat_id','id_telegram','telegram','user_id'])
    namec = find_col(cs,['nombre','name','usuario','username'])
    if not idc: return jsonify({'ok':False,'msg':'No encuentro columna telegram_id/chat_id'}), 400
    try:
        with con() as c:
            if request.method == 'POST':
                tid = (request.json or {}).get('telegram_id','').strip(); name = (request.json or {}).get('nombre','').strip()
                if not tid: return jsonify({'ok':False,'msg':'ID vacío'}), 400
                if namec and name:
                    c.execute(f'insert into {q(ut)} ({q(idc)}, {q(namec)}) values (?, ?)', (tid, name))
                else:
                    c.execute(f'insert into {q(ut)} ({q(idc)}) values (?)', (tid,))
                c.commit(); return jsonify({'ok':True})
            tid = (request.json or {}).get('telegram_id','').strip()
            c.execute(f'delete from {q(ut)} where cast({q(idc)} as text)=?', (tid,)); c.commit(); return jsonify({'ok':True})
    except Exception as e: return jsonify({'ok':False,'msg':str(e)}), 400

@app.route('/api/launcher/status')
def api_launcher_status():
    data = {name: bool(PROCS.get(name) and PROCS[name].poll() is None) for name in SERVICE_CMDS}
    data['all'] = all(data.values())
    return jsonify(data)

@app.route('/api/launcher/<service>/<action>', methods=['POST'])
def api_launcher(service, action):
    if service == 'all':
        for s in SERVICE_CMDS: service_action(s, action)
    else: service_action(service, action)
    return jsonify({'ok':True})

def service_action(service, action):
    if service not in SERVICE_CMDS: return
    p = PROCS.get(service)
    if action == 'start' and not (p and p.poll() is None):
        PROCS[service] = subprocess.Popen(SERVICE_CMDS[service], shell=True, cwd=os.getenv('PROJECT_DIR', str(BASE_DIR.parent)))
    if action == 'stop' and p and p.poll() is None:
        try: p.terminate()
        except Exception: pass

def build_ticket_excel():
    tt = ticket_table()
    if not tt: raise RuntimeError('No existe tabla de tickets')
    with con() as c:
        rows = [dict(r) for r in c.execute(f'select * from {q(tt)}').fetchall()]
    headers = list(rows[0].keys()) if rows else cols(tt)
    wb = Workbook(); ws = wb.active; ws.title = 'Reporte Tickets'
    last_col = max(1, len(headers)); dark = '1F4E79'; head = '4F81BD'
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
    ws.cell(1,1,'Reporte de Tickets').fill = PatternFill('solid', fgColor=dark)
    ws.cell(1,1).font = Font(color='FFFFFF', bold=True, size=14)
    ws.cell(1,1).alignment = Alignment(horizontal='center')
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=last_col)
    ws.cell(2,1, f'Última sincronización: {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}')
    ws.cell(2,1).font = Font(italic=True, size=10)
    ws.cell(2,1).alignment = Alignment(horizontal='center')
    thin = Side(style='thin', color='000000')
    for i,h in enumerate(headers, 1):
        cell = ws.cell(3,i,h); cell.fill = PatternFill('solid', fgColor=head); cell.font = Font(color='FFFFFF', bold=True); cell.border = Border(top=thin,bottom=thin,left=thin,right=thin); cell.alignment = Alignment(horizontal='center')
    state_col = find_col(headers, ['estado','status','state'])
    for r_idx,row in enumerate(rows,4):
        cl = status_class(row.get(state_col)) if state_col else ''
        color = 'C6EFCE' if cl=='abierto' else 'FFEB9C' if cl=='proceso' else 'FFC7CE' if cl=='cerrado' else 'FFFFFF'
        for c_idx,h in enumerate(headers,1):
            cell=ws.cell(r_idx,c_idx,row.get(h,'')); cell.fill=PatternFill('solid', fgColor=color); cell.border=Border(top=thin,bottom=thin,left=thin,right=thin); cell.alignment=Alignment(vertical='center', wrap_text=True)
    ws.auto_filter.ref = f'A3:{get_column_letter(last_col)}{max(3, len(rows)+3)}'
    ws.freeze_panes = 'A4'
    for i,h in enumerate(headers,1):
        width = min(max(len(str(h))+2, *(len(str(r.get(h,'')))+2 for r in rows[:100])) if rows else len(str(h))+2, 42)
        ws.column_dimensions[get_column_letter(i)].width = width
    bio = io.BytesIO(); wb.save(bio); bio.seek(0); return bio

@app.route('/api/export/tickets')
def export_tickets():
    return send_file(build_ticket_excel(), as_attachment=True, download_name=f'reporte_tickets_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route('/api/email/tickets', methods=['POST'])
def email_tickets():
    to = os.getenv('EMAIL_TO','').strip(); smtp_host = os.getenv('SMTP_HOST','').strip(); smtp_user = os.getenv('SMTP_USER','').strip(); smtp_pass = os.getenv('SMTP_PASS','').strip(); smtp_port=int(os.getenv('SMTP_PORT','587'))
    if not all([to, smtp_host, smtp_user, smtp_pass]):
        return jsonify({'ok':False,'msg':'Configura EMAIL_TO, SMTP_HOST, SMTP_USER y SMTP_PASS en .env'}), 400
    bio = build_ticket_excel(); data = bio.getvalue()
    msg = EmailMessage(); msg['Subject']='Reporte de Tickets TicketIT'; msg['From']=smtp_user; msg['To']=to
    msg.set_content('Se adjunta reporte de tickets generado desde TicketIT.')
    msg.add_attachment(data, maintype='application', subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename='reporte_tickets.xlsx')
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.starttls(); s.login(smtp_user, smtp_pass); s.send_message(msg)
        return jsonify({'ok':True})
    except Exception as e: return jsonify({'ok':False,'msg':str(e)}), 400

if __name__ == '__main__':
    app.run(host=os.getenv('HOST','0.0.0.0'), port=int(os.getenv('PORT','8080')), debug=os.getenv('DEBUG','1')=='1')
