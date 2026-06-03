import struct, os, json, glob, re, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG  = json.load(open(os.path.join(ROOT, 'config.json'), encoding='utf-8'))

def _resolve(p, default):
    return os.path.normpath(os.path.join(ROOT, CFG.get(p, default)))

BASE = _resolve('base_rui', os.path.join('..', 'index.bak.rui'))
OUT  = _resolve('out_rui',  os.path.join('..', 'index.rui'))
IMG_DIR = os.path.join(ROOT, 'assets', 'images')

if not os.path.exists(BASE):
    raise SystemExit(f"[!] base .rui not found: {BASE}\n"
                     f"    Put your launcher's original index.rui here as 'index.bak.rui' "
                     f"(or set 'base_rui' in config.json).")

HEADER_END  = 8488
TABLE2_BASE = 4240

def u32(d, o): return struct.unpack_from('<I', d, o)[0]

def load(path):
    data = bytearray(open(path, 'rb').read())
    files = []
    for k in range(132):
        files.append(dict(size_pos=(2*k+1)*16, off_pos=(2*k+2)*16,
                          size=u32(data,(2*k+1)*16), off=u32(data,(2*k+2)*16)))
    for k in range(133):
        sp = TABLE2_BASE+(2*k)*16; op = TABLE2_BASE+(2*k+1)*16
        files.append(dict(size_pos=sp, off_pos=op, size=u32(data,sp), off=u32(data,op)))
    files.sort(key=lambda f: f['off'])
    return data, files

def edit_text(blob, is_appjs):
    out = blob
    ac = CFG.get('auto_connect', {})
    if is_appjs and ac.get('enabled'):
        anchor = b'_.servers.refresh)}'
        inj = ('_.servers.refresh),setTimeout(()=>{rageApi.isALauncher&&this.launchGame({ip:"%s",port:%d,name:"%s"},!0)},%d)}'
               % (ac['ip'], int(ac['port']), ac.get('name','AutoConnect'), int(ac.get('delay_ms',2000)))).encode()
        c = out.count(anchor)
        if c != 1:
            raise RuntimeError(f"auto-connect anchor found {c} times (expected 1)")
        out = out.replace(anchor, inj)
        print(f"  [auto-connect] -> {ac['ip']}:{ac['port']} ({ac.get('delay_ms',2000)}ms)")
    sl = CFG.get('server_list', {})
    if is_appjs and sl.get('override'):
        srv = []
        for i, s in enumerate(sl.get('servers', [])):
            srv.append({
                "id": i, "name": s.get("name", f"Server {i}"),
                "ip": s.get("ip", "127.0.0.1"), "port": int(s.get("port", 22005)),
                "players": int(s.get("players", 0)), "maxplayers": int(s.get("maxplayers", 1000)),
                "ping": int(s.get("ping", 30)), "lang": s.get("lang", "en"),
                "gamemode": s.get("gamemode", "Freeroam"), "url": s.get("url", "")
            })
        arr = json.dumps(srv, ensure_ascii=True)
        mnt_anchor = b'async mounted(){this.loader("core",!0)'
        if out.count(mnt_anchor) != 1:
            raise RuntimeError("server-list mounted anchor not found")
        inj2 = (b'async mounted(){try{rageApi.getServers=function(_c){_c(null,'
                + arr.encode() + b')}}catch(e){}this.loader("core",!0)')
        out = out.replace(mnt_anchor, inj2)
        print(f"  [server-list] override: {len(srv)} server(s)")
    for old, new in CFG.get('colors', {}).items():
        cnt = out.count(old.encode())
        if cnt: out = out.replace(old.encode(), new.encode()); print(f"  [color] {old} -> {new} ({cnt}x)")
    for pair in CFG.get('texts', []):
        old, new = pair[0].encode(), pair[1].encode()
        cnt = out.count(old)
        if cnt: out = out.replace(old, new); print(f"  [text] {pair[0]!r} -> {pair[1]!r} ({cnt}x)")
    return out

def main():
    data, files = load(BASE)
    repl = {}

    title = CFG.get('title')
    for i, f in enumerate(files):
        head = bytes(data[f['off']:f['off']+8])
        if head == b'(functio':                    # app.js
            new = edit_text(bytes(data[f['off']:f['off']+f['size']]), True)
            if new != data[f['off']:f['off']+f['size']]: repl[i] = new
        elif head[:4] == b'<!DO':                   # index.html
            h = bytes(data[f['off']:f['off']+f['size']])
            orig = h
            h = edit_text(h, False)
            if title:
                h2 = re.sub(rb'<title>.*?</title>', ('<title>%s</title>' % title).encode(), h)
                if h2 != h: print(f"  [title] -> {title}"); h = h2
            if h != orig: repl[i] = h

    # images: assets/images/img_XXX.jpg -> sorted index XXX
    if CFG.get('use_images_folder', True):
        for path in sorted(glob.glob(os.path.join(IMG_DIR, 'img_*.jpg'))):
            m = re.search(r'img_(\d+)\.jpg$', os.path.basename(path))
            if not m: continue
            idx = int(m.group(1))
            b = open(path, 'rb').read()
            orig = bytes(data[files[idx]['off']:files[idx]['off']+files[idx]['size']])
            if b != orig:
                repl[idx] = b
                print(f"  [image] idx{idx} <- {os.path.basename(path)} ({len(b)}B, was {len(orig)}B)")

    # rebuild 
    trailing = bytes(data[files[-1]['off']+files[-1]['size']:])
    sizes, blobs = [], []
    for i, f in enumerate(files):
        b = repl[i] if i in repl else bytes(data[f['off']:f['off']+f['size']])
        blobs.append(b); sizes.append(len(b))
    offs = [HEADER_END]
    for i in range(1, len(files)): offs.append(offs[-1] + sizes[i-1])
    header = bytearray(data[:HEADER_END])
    for i, f in enumerate(files):
        struct.pack_into('<I', header, f['size_pos'], sizes[i])
        struct.pack_into('<I', header, f['off_pos'], offs[i])
    out = bytes(header) + b''.join(blobs) + trailing
    open(OUT, 'wb').write(out)

    print(f"\n[+] wrote {os.path.relpath(OUT)}  ({len(out)} bytes)  |  {len(repl)} file(s) changed")
    # integrity
    f2 = load(OUT)[1]
    ok = all(f2[i]['off']+f2[i]['size']==f2[i+1]['off'] for i in range(len(f2)-1))
    print(f"[i] integrity (contiguity): {'OK' if ok else 'FAILED!'}")

if __name__ == '__main__':
    main()
