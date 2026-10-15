# Platform catalog — what attackers extract and how to protect it

Tool names, prices and maintenance status change. Before recommending a paid or niche tool, check it is still maintained. Prefer the free, built-in option when it's good enough.

Legend: **Free** / **Paid** / **OSS** (open source). Effort: S (hours) · M (days) · L (weeks).

---

## Universal first move: what can leave the client?

For every platform, ask first: does this logic, data or secret *need* to run on the user's device? If not, move it behind an authenticated API. Code that never ships cannot be decompiled. Typical candidates: pricing/scoring/ranking algorithms, recommendation logic, premium-feature checks, AI prompts and model calls, data processing, anything that uses an API key.

---

## Web front-end (React, Vue, Svelte, Angular, plain JS)

**What attackers get:** everything shipped to the browser. Minified JS is readable with a formatter; with source maps it's the original source, comments included. DevTools shows every API call.

| Measure | Tool / setting | Effort | Notes |
|---|---|---|---|
| Don't publish source maps | Vite `build.sourcemap: false` (default) or `'hidden'`; webpack `devtool: false` / `hidden-source-map`; Next.js `productionBrowserSourceMaps: false` (default); CRA `GENERATE_SOURCEMAP=false` | S | Upload maps privately to the error tracker (Sentry etc.) instead. |
| No secrets in the bundle | Anything prefixed `VITE_`, `NEXT_PUBLIC_`, `REACT_APP_`, `PUBLIC_`, `NUXT_PUBLIC_` is public | S | Move secret calls to a server route; rotate leaked keys. |
| Minification | Terser / esbuild (default in prod builds) | S | Strips names and comments. Weak alone. |
| Obfuscation | `javascript-obfuscator` (OSS, Free); Jscrambler (Paid, also does anti-tamper and RN) | S–M | Control-flow flattening and string encryption cost performance and bundle size; apply only to sensitive modules. |
| Move logic server-side | Next.js server actions / route handlers, SvelteKit server load, any API | M | The only strong option for web. |
| WebAssembly | Compile sensitive parts (Rust/C++) to WASM | M | Harder to read than JS but decompilable; a speed bump, not a vault. |
| Bot & abuse protection | Cloudflare Turnstile / Bot Management, rate limits, auth on every endpoint | S–M | Protects the API the front-end calls. |

## Node.js / server back-end

Server code isn't shipped, so extraction risk is low — **unless** the product is self-hosted or distributed (on-prem, Docker images, npm packages).

- Distributed images/packages: everything inside is readable. Options: keep the core as a hosted API; compile to a binary with Node SEA (single executable applications) or `pkg`-style bundlers (readable with effort); `bytenode` to ship V8 bytecode (raises effort, version-coupled).
- Licence checks for on-prem: signed licence files verified with a public key (Ed25519), plus periodic online check-in when allowed.
- Rate limiting: `express-rate-limit`, `@nestjs/throttler`, `rate-limiter-flexible`, Fastify `@fastify/rate-limit`.

## Android (Kotlin/Java)

**What attackers get:** the APK/AAB. `jadx` decompiles it to near-original Java/Kotlin in seconds; `apktool` unpacks resources; Frida hooks functions at runtime.

| Measure | Tool / setting | Effort | Notes |
|---|---|---|---|
| Shrink + obfuscate | R8 (Free, built in): `isMinifyEnabled = true`, `isShrinkResources = true` in `release` | S | Renames classes/methods. Keep the `mapping.txt` private for crash symbolication. |
| Don't ship debuggable | `debuggable false` in release (default) | S | Scanner checks. |
| Server verifies the device/app | Play Integrity API (Free) | M | Server checks a signed verdict before serving premium data. |
| Strong obfuscation + RASP | DexGuard (Guardsquare, Paid), Promon SHIELD (Paid), Appdome (Paid), freeRASP by Talsec (Free tier) | M | Detects root, hooks, emulators, repackaging. |
| Native code for secrets/algorithms | NDK (C/C++) | M | Harder than Java, still reversible with Ghidra/IDA. |
| Certificate pinning | Network Security Config pinning | S | Slows API traffic inspection; plan pin rotation. |

## iOS (Swift/Objective-C)

**What attackers get:** decrypted IPA (from jailbroken devices). Swift is harder to read than Objective-C; class and method names leak in symbols. Frida works here too.

- Strip symbols in release (default: `STRIP_INSTALLED_PRODUCT`, `DEPLOYMENT_POSTPROCESSING`), keep dSYMs private.
- App Attest (DeviceCheck framework, Free): server verifies requests come from the genuine app.
- iXGuard (Guardsquare, Paid), Promon, freeRASP (Free tier) for obfuscation and jailbreak/hook detection.
- Avoid Objective-C for sensitive logic (dynamic runtime is easy to hook).

## React Native

- Release builds use Hermes bytecode by default — not plain text, but decompilers exist (e.g. `hermes-dec`). Treat as readable.
- Jscrambler supports RN; plus the native-side tools above (R8, App Attest, Play Integrity).
- Keep logic and keys server-side. `react-native-config` values are bundled = public.

## Flutter

- Build with `--obfuscate --split-debug-info=<dir>` (Free). Keep the symbols dir private.
- Dart AOT snapshots are harder than JS but tools exist (e.g. `blutter`). Keep secrets out; `--dart-define` values end up in the binary.
- Pair with Play Integrity / App Attest and freeRASP (has a Flutter SDK).

## Electron

**What attackers get:** `app.asar` is just an archive — `npx asar extract` gives the full JS source.

- asar is packaging, not protection.
- Electron fuses (`@electron/fuses`): enable `EnableEmbeddedAsarIntegrityValidation` and `OnlyLoadAppFromAsar`, disable `RunAsNode` and `EnableNodeCliInspectArguments` — blocks easy tampering and debugger attach.
- `bytenode` to ship V8 bytecode for sensitive modules; obfuscate renderer bundles like web.
- Strongest: core logic as a server API or a native module.
- Code-sign the app (Apple notarization, Windows Authenticode).

## .NET (C#, desktop, Unity Mono, server distributables)

**What attackers get:** IL decompiles almost perfectly with ILSpy / dnSpy (dnSpyEx).

- Native AOT (`<PublishAot>true</PublishAot>`, .NET 7+) compiles to native machine code — much harder than IL. Check library compatibility (reflection).
- Obfuscators: Obfuscar (OSS), ConfuserEx forks (OSS, check maintenance), Dotfuscator (PreEmptive, Paid, Community edition exists), .NET Reactor (Paid), Eazfuscator.NET (Paid).
- Licensing: Cryptlex, LicenseSpring, Keygen.sh, or signed licence files.

## Java / JVM (desktop, plugins, distributables)

- Bytecode decompiles cleanly (CFR, Fernflower, JD-GUI).
- ProGuard (OSS) for shrinking/renaming; Zelix KlassMaster, Allatori (Paid) for stronger obfuscation and string encryption.
- GraalVM `native-image` compiles to native (reflection config needed).

## Native C / C++ / Rust / Go

**What attackers get:** machine code. Ghidra (Free) and IDA Pro decompile to C-like pseudocode; AI tools now speed this up a lot. Still the hardest common target.

- Strip symbols: Rust `[profile.release] strip = true`, `lto = true`, `panic = "abort"`, `--remap-path-prefix` to hide build paths; C/C++ `-s`, `-fvisibility=hidden`; Go `-ldflags="-s -w"` and `-trimpath` (Go keeps a lot of type/function metadata; `garble` (OSS) obfuscates Go builds).
- Compiler-level obfuscation: Obfuscator-LLVM and maintained forks (OSS).
- Virtualization / packers: VMProtect, Themida / Code Virtualizer (Oreans) — Paid, strongest commercial option on Windows; performance cost; antivirus false positives possible.
- Anti-debug and integrity checks; but keep them maintainable.

## Python

**What attackers get:** `.py` or `.pyc` — `.pyc` decompiles easily (e.g. pycdc, decompyle3). PyInstaller executables unpack with `pyinstxtractor`.

- PyInstaller alone = no protection.
- Nuitka (OSS, commercial tier adds protection) compiles to C → native binary; Cython for sensitive modules.
- PyArmor (Paid for most uses) — obfuscation + licence binding.
- For SaaS, keep it on the server.

## Games (Unity, Unreal, Godot, custom)

- Unity: use **IL2CPP** scripting backend, not Mono (Mono ships readable DLLs). IL2CPP is still dumpable (Il2CppDumper) — add an obfuscator asset for sensitive code. Encrypt AssetBundles if art is the jewel.
- Unreal: pak file encryption and signing (project settings); C++ is native.
- Godot: export with PCK encryption (requires custom export templates built with the encryption key).
- Multiplayer: **server-authoritative** logic beats every client-side anti-cheat.
- Commercial anti-tamper (Denuvo) is expensive and aimed at the launch window of big releases; rarely proportional for indies.

## APIs and SaaS

The code is safe on the server; the risks are behavioural cloning, scraping and abuse.

- Authentication on every endpoint, per-key rate limits and quotas, anomaly detection on bulk access.
- Don't over-expose: return only fields the UI needs; paginate with limits; avoid enumerable sequential IDs (use UUIDs).
- Public docs: document what customers need, not internals that make cloning trivial.
- Terms of service forbidding scraping, bulk extraction and building competing products.
- Canary/honeytoken records to detect leaks (see data products).

## Data products (datasets, maps, timetables, catalogues)

- **Trap records** ("copyright traps", like mapmakers' trap streets): insert a few fictitious but harmless entries; if they show up elsewhere, you have proof of copying. Make sure they can't mislead real users in a harmful way (e.g. never fake a real-world safety-relevant record).
- Per-customer watermarking of exports (unique ordering, tiny controlled variations, hidden fields).
- EU **sui generis database right** may protect substantial investment in a database (see `legal.md`).
- Licence the data explicitly; deliver through authenticated, rate-limited APIs rather than bulk dumps.

## AI / LLM products

- Keep system prompts, prompt chains, retrieval logic and model calls server-side; assume anything in the client is public.
- Prompt-extraction defences reduce leakage but don't guarantee it — don't put real secrets in prompts.
- Model weights: serve via API; if weights must ship (on-device), accept they can be extracted.
- **Distillation** (training a copy on your outputs): rate limits, quotas, ToS clauses, monitoring for systematic querying, output watermarking where available.
- The moat is usually proprietary data, evaluation, integrations and feedback loops — invest there.

## Licensing and anti-piracy (any distributed software)

- Signed licence keys/files: sign on server with a private key (Ed25519), verify in the app with the public key — can't be forged, but the check can be patched out, so pair with obfuscation/integrity checks.
- Licensing services: Keygen.sh, Cryptlex, LicenseSpring; payment platforms like Lemon Squeezy, Paddle and Gumroad offer basic licence keys.
- Online activation + periodic check-in, with an offline grace period to avoid punishing legitimate users.
- **Per-customer build watermarking**: embed an invisible customer ID in each build so a leaked copy can be traced.
- Value that only exists online (sync, cloud features, updates, support) makes cracked copies less attractive than any DRM.

## Clone monitoring (all products)

- Google Alerts / brand monitoring for the product name and distinctive phrases.
- GitHub code search for unique strings, canary tokens or distinctive identifiers from your code.
- App store searches for look-alike names and icons.
- Trap records and honeytokens (above) for data.
- Keep a dated evidence trail (repository history, design files, releases) — it proves authorship if you need a takedown.
