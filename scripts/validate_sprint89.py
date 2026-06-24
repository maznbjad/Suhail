from __future__ import annotations
import base64, hashlib, json, re, sqlite3, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
checks={}
def add(name,ok,detail=''):
    checks[name]={'ok':bool(ok),'detail':str(detail)}

def main():
    app=(ROOT/'app.py').read_text(encoding='utf-8')
    manifest=json.loads((ROOT/'config/project_manifest.json').read_text(encoding='utf-8'))
    q=json.loads((ROOT/'data/questions.json').read_text(encoding='utf-8'))
    summaries=json.loads((ROOT/'data/smart_summaries.json').read_text(encoding='utf-8'))
    s54=(ROOT/'src/ui/sprint54_experience.js').read_text(encoding='utf-8')
    s55=(ROOT/'src/ui/sprint55_account.js').read_text(encoding='utf-8')
    s71=(ROOT/'src/ui/sprint71_exam_summary_unification.js').read_text(encoding='utf-8')
    s89js=(ROOT/'src/ui/sprint89_identity_cleanup.js').read_text(encoding='utf-8')
    s89css=(ROOT/'src/ui/sprint89_identity_cleanup.css').read_text(encoding='utf-8')
    auth=(ROOT/'src/core/auth_repository.py').read_text(encoding='utf-8')
    server=(ROOT/'src/api/server.py').read_text(encoding='utf-8')

    add('release', manifest.get('version')=='1.0.89' and manifest.get('latest_sprint')==89 and manifest.get('sprint')==89, manifest.get('version'))
    add('s89_files', (ROOT/'src/ui/sprint89_identity_cleanup.js').exists() and (ROOT/'src/ui/sprint89_identity_cleanup.css').exists())
    add('s89_injected', 'sprint89_identity_cleanup.css' in app and 'sprint89_identity_cleanup.js' in app)
    add('registration_username', 'id="registerUsername"' in app and 'هذا اليوزر مستخدم' in app and '^[a-z0-9_]{3,20}$' in app)
    add('username_api', 'username TEXT UNIQUE' in auth and 'CREATE UNIQUE INDEX IF NOT EXISTS idx_auth_users_username' in auth and 'receiver_username' in server)
    add('canonical_identity', "const studentName=s.name||s.display_name||p.displayName" in s55 and "if(s.role==='student'&&s.name)p.displayName=s.name" in s54 and 'syncIdentity' in s89js)
    add('friends_by_username', 'إضافة صديق باليوزر' in s54 and 'accountByUsername(username)' in s54 and 'يوزرك:' in s54 and 'bdi dir="ltr"' in s54)
    add('account_grouping', 'الحساب والنشاط' in s55 and 's89-account-activity' in s55 and 's89-about-card' in s55 and s55.index('s89-account-activity') < s55.index('الأسئلة المحفوظة') < s55.index('s89-about-card'))
    add('summary_cleanup', 's71-header-icon' not in s71 and 'كل القوائم بنفس التصميم وطريقة الاستخدام' not in s71 and 'نفس البطاقة في جميع المستويات' not in s71)
    add('avatar_containment', 'object-fit:contain!important' in s89css and 'object-position:center bottom!important' in s89css)

    # Tower-free logo is identical across static runtime sources and embedded in splash.
    logo=(ROOT/'assets/brand/suhail_logo_current.png').read_bytes()
    logo2=(ROOT/'assets/images/suhail_logo_full_original.png').read_bytes()
    add('logo_assets_match', hashlib.sha256(logo).hexdigest()==hashlib.sha256(logo2).hexdigest(), hashlib.sha256(logo).hexdigest())
    svg=(ROOT/'assets/images/splash/suhail_intro_iphone_animated_v12.svg').read_text(encoding='utf-8')
    imgs=re.findall(r'<image\s+href="data:image/[^;]+;base64,([^"]+)"[^>]*>',svg)
    splash_logo=base64.b64decode(imgs[1]) if len(imgs)>1 else b''
    add('splash_logo_replaced', splash_logo==logo, f'embedded={len(splash_logo)} source={len(logo)}')

    add('question_bank', len(q)==5400, len(q))
    add('summaries', len(summaries)==72, len(summaries))
    tah=[x for x in q if x.get('exam')=='تحصيلي']
    linked=[x for x in tah if str(x.get('summary_block_id','')).strip()]
    add('physics_links_preserved', len(tah)==2400 and len(linked)==600, f'tahsili={len(tah)} linked={len(linked)}')

    for rel in ['app.py','src/api/server.py','src/core/auth_repository.py']:
        p=subprocess.run([sys.executable,'-m','py_compile',str(ROOT/rel)],capture_output=True,text=True)
        add('py_'+rel.replace('/','_'),p.returncode==0,p.stderr.strip())
    for rel in ['src/ui/sprint54_experience.js','src/ui/sprint55_account.js','src/ui/sprint71_exam_summary_unification.js','src/ui/sprint89_identity_cleanup.js']:
        p=subprocess.run(['node','--check',str(ROOT/rel)],capture_output=True,text=True)
        add('js_'+Path(rel).stem,p.returncode==0,p.stderr.strip())

    # Safe schema migration + unique username behavior on a temporary database.
    try:
        sys.path.insert(0,str(ROOT))
        from src.core.auth_repository import ensure_auth_schema, create_user, authenticate
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'auth.db'
            ensure_auth_schema(db)
            u=create_user(db,email='f@test.com',password='password123',display_name='f',role='student',username='f_student')
            ok=authenticate(db,'f@test.com','password123')
            duplicate=False
            try: create_user(db,email='g@test.com',password='password123',display_name='g',role='student',username='f_student')
            except Exception: duplicate=True
            cols=[r[1] for r in sqlite3.connect(db).execute('PRAGMA table_info(auth_users)').fetchall()]
            add('auth_runtime',u.get('username')=='f_student' and ok and ok.get('username')=='f_student' and duplicate and 'username' in cols)
    except Exception as exc:
        add('auth_runtime',False,repr(exc))

    ok=all(v['ok'] for v in checks.values())
    out={'sprint':89,'ok':ok,'checks':checks}
    report=ROOT/'docs/reports/SPRINT_89_CHECKS.json'
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
