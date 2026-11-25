"""Push rule files from this repo back to the router, with MD5 verification."""
import hashlib, json, os, paramiko

HOST = '192.168.31.1'
USER = 'root'
# Password is NEVER stored in this public repo.
# Set ROUTER_PASSWORD in your environment, or put it in a local .env file
# (which is gitignored) as: ROUTER_PASSWORD=your_password
def _password():
    p = os.environ.get('ROUTER_PASSWORD')
    if p:
        return p
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        for line in open(env_file, encoding='utf-8'):
            line = line.strip()
            if line.startswith('ROUTER_PASSWORD='):
                return line.split('=', 1)[1].strip().strip('\'"')
    raise SystemExit('ROUTER_PASSWORD not set. Export it or create a local .env file.')

DRY_RUN = False  # set True to preview without writing

RULES_DIR = os.path.join(os.path.dirname(__file__), 'rules')
MANIFEST  = os.path.join(os.path.dirname(__file__), 'manifest.json')


def md5(data):
    return hashlib.md5(data).hexdigest()


def main():
    manifest = json.load(open(MANIFEST, encoding='utf-8'))
    pwd = _password()
    cl = paramiko.SSHClient()
    cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cl.connect(HOST, username=USER, password=pwd, timeout=20,
               allow_agent=False, look_for_keys=False)

    ok = 0
    for item in manifest:
        fn = item['file']
        remote = item['source']
        # backups are archived only, never written back to production
        if 'converted_backup' in fn:
            print('SKIP (archive only):', fn)
            continue
        local = open(os.path.join(RULES_DIR, fn), 'rb').read()
        if DRY_RUN:
            print('DRY RUN:', fn, '->', remote, 'md5', md5(local))
            continue

        # upload
        ch = cl.get_transport().open_session()
        ch.exec_command("cat > '%s'" % remote)
        ch.sendall(local)
        ch.shutdown_write()
        rc = ch.recv_exit_status()
        ch.close()
        assert rc == 0, (remote, rc)

        # verify by reading back
        ch = cl.get_transport().open_session()
        ch.exec_command("cat '%s'" % remote)
        rb = b''
        while True:
            b = ch.recv(65536)
            if not b:
                break
            rb += b
        ch.close()
        assert md5(rb) == md5(local), ('MD5 mismatch', remote)
        print('OK %-30s md5=%s' % (fn, md5(local)[:12]))
        ok += 1

    cl.close()
    print('\n%d files verified. NOW run on router: /data/other/ShellCrash/start.sh restart' % ok)


if __name__ == '__main__':
    main()
