"""Re-pull all local rule files from the router and refresh manifest.json."""
import json, os, paramiko

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

PWD = None  # resolved in main()
CFG_LOCAL = os.path.join(os.path.dirname(__file__), '..', 'cfg_after_qh.json')

RULES_DIR = os.path.join(os.path.dirname(__file__), 'rules')
MANIFEST  = os.path.join(os.path.dirname(__file__), 'manifest.json')


def main():
    cfg = json.load(open(CFG_LOCAL, encoding='utf-8'))
    pwd = _password()
    cl = paramiko.SSHClient()
    cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cl.connect(HOST, username=USER, password=pwd, timeout=20,
               allow_agent=False, look_for_keys=False)
    os.makedirs(RULES_DIR, exist_ok=True)
    manifest = []

    def fetch(remote, tag, fmt):
        ch = cl.get_transport().open_session()
        ch.exec_command("cat '%s'" % remote)
        data = b''
        while True:
            b = ch.recv(65536)
            if not b:
                break
            data += b
        rc = ch.recv_exit_status()
        ch.close()
        assert rc == 0, (remote, rc)
        ext = '.srs' if fmt == 'binary' else '.json'
        fn = tag.replace('/', '_') + ext
        open(os.path.join(RULES_DIR, fn), 'wb').write(data)
        manifest.append({'tag': tag, 'file': fn, 'type': fmt,
                         'source': remote, 'bytes': len(data)})
        print('%-34s %8d' % (fn, len(data)))

    for r in cfg['route']['rule_set']:
        if r['type'] == 'local':
            fetch(r['path'], r['tag'], r.get('format', 'source'))
    # archived originals of converted sets
    for tag, path in [
        ('Google FCM_converted_backup', '/data/other/ShellCrash/ruleset_sb/Google FCM.json'),
        ('Steam_converted_backup', '/data/other/ShellCrash/ruleset_sb/Steam.json'),
    ]:
        fetch(path, tag, 'source')

    cl.close()
    json.dump(manifest, open(MANIFEST, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('\n%d files, %d bytes' % (len(manifest), sum(x['bytes'] for x in manifest)))
    print('Remember: git add rules/ manifest.json && git commit')


if __name__ == '__main__':
    main()
