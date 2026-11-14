"""No third-party dependencies. In-memory, per-browser, sandboxed workflow demo."""
import json
import os
import secrets
import threading
from collections import OrderedDict
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from engine import Engine,WorkflowError
from quality import run_checks

STATIC=Path(__file__).parent/'static'
SESSIONS=OrderedDict()
LOCK=threading.RLock()
MAX_SESSIONS=400

def session_from(headers):
    cookie=SimpleCookie()
    try:cookie.load(headers.get('Cookie',''))
    except Exception:pass
    sid=cookie.get('planbridge_session')
    sid=sid.value if sid else None
    with LOCK:
        if sid not in SESSIONS:
            sid=secrets.token_urlsafe(32)
            SESSIONS[sid]={'engine':Engine(),'csrf':secrets.token_urlsafe(32)}
        SESSIONS.move_to_end(sid)
        while len(SESSIONS)>MAX_SESSIONS:SESSIONS.popitem(last=False)
        return sid, SESSIONS[sid]

class Handler(BaseHTTPRequestHandler):
    server_version='PlanBridge/1.0'
    def send_bytes(self,status,content,kind='application/json; charset=utf-8',cookie=None):
        self.send_response(status)
        self.send_header('Content-Type',kind)
        self.send_header('Cache-Control','no-store' if kind.startswith('application/json') else 'public, max-age=3600')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'")
        if cookie:
            secure='; Secure' if self.headers.get('X-Forwarded-Proto')=='https' else ''
            self.send_header('Set-Cookie',f'planbridge_session={cookie}; HttpOnly; SameSite=Lax; Path=/{secure}')
        self.send_header('Content-Length',str(len(content)))
        self.end_headers();self.wfile.write(content)

    def reply(self,status,payload,cookie=None):
        self.send_bytes(status,json.dumps(payload,allow_nan=False).encode('utf-8'),cookie=cookie)

    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/health':return self.reply(200,{'status':'healthy','service':'planbridge','live_ledger':False})
        if path=='/api/state':
            sid,s=session_from(self.headers)
            with LOCK:
                data=s['engine'].snapshot()
            return self.reply(200,{'data':data,'csrf':s['csrf']},sid)
        if path=='/' or path=='/index.html':path='/index.html'
        if path in ('/index.html','/app.js','/styles.css'):
            resource=STATIC/path.lstrip('/')
            kind={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'application/javascript; charset=utf-8'}[resource.suffix]
            return self.send_bytes(200,resource.read_bytes(),kind)
        return self.reply(404,{'error':'Not found'})

    def do_POST(self):
        path=urlparse(self.path).path
        if path not in ('/api/actor','/api/action','/api/reset','/api/tests'):
            return self.reply(404,{'error':'Not found'})
        sid,s=session_from(self.headers)
        if self.headers.get('X-Demo-CSRF')!=s['csrf']:
            return self.reply(403,{'error':'Missing or invalid demo CSRF token'},sid)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size>8192 or size<0: return self.reply(413,{'error':'Request too large'},sid)
            body=json.loads(self.rfile.read(size) or b'{}')
            if not isinstance(body,dict):return self.reply(400,{'error':'Expected JSON object'},sid)
            with LOCK:
                if path=='/api/actor':
                    state=s['engine'].switch(body.get('actor'))
                    return self.reply(200,{'message':'Persona switched','data':state},sid)
                if path=='/api/reset':
                    state=s['engine'].reset()
                    return self.reply(200,{'message':'Your scenario reset to the baseline','data':state},sid)
                if path=='/api/tests':
                    report=run_checks()
                    return self.reply(200,report,sid)
                result=s['engine'].apply(body.get('type'),body)
                return self.reply(200,{**result,'data':s['engine'].snapshot()},sid)
        except WorkflowError as err:
            return self.reply(err.code,{'error':str(err),'code':err.code},sid)
        except (json.JSONDecodeError,ValueError,TypeError):
            return self.reply(400,{'error':'Invalid request body'},sid)
        except Exception:
            self.log_error('Unhandled workflow request failure')
            return self.reply(500,{'error':'Unexpected simulator failure'},sid)

if __name__=='__main__':
    port=int(os.environ.get('PORT','8000'))
    print(f'PlanBridge listening on :{port}',flush=True)
    ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
