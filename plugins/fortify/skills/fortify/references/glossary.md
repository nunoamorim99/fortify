# Glossary — plain language

Use these one-line explanations the first time a term appears in a report. Add an everyday analogy when it helps.

**Reverse engineering** — Working out how a product works by studying the finished product instead of its blueprints. Like tasting a dish to figure out the recipe.

**Decompiler** — A tool that turns shipped machine code or bytecode back into human-readable code. Examples: jadx (Android), ILSpy (.NET), Ghidra (native).

**Disassembler** — Shows the raw machine instructions of a program; lower level than a decompiler.

**Bytecode** — An in-between form of code (Java, .NET, Python, Hermes) that is easy to decompile back to near-original source.

**Minification** — Squeezing code by removing spaces, comments and long names. Makes it smaller, a little harder to read.

**Obfuscation** — Deliberately scrambling code so it still works but is very hard for a human to understand. Like rewriting a recipe with every ingredient renamed and the steps shuffled into a maze. Slows people down; doesn't stop a determined expert.

**String encryption** — Hiding readable text (URLs, messages, keys) inside the code so it can't be found by simple search.

**Control-flow flattening** — An obfuscation that turns the natural order of a program into a confusing state machine.

**Code virtualization** — The strongest common obfuscation: the code is converted into a private instruction set run by a mini-machine embedded in the app. An attacker must first understand the mini-machine.

**Source map** — A file that maps minified web code back to the original source. Great for debugging; if published, it hands out your source code.

**Symbols / stripping** — Symbols are the names of functions and variables kept in a build. Stripping removes them so the code reveals less.

**Native code** — Code compiled directly to processor instructions (C, C++, Rust, Go, Swift). Harder to read than bytecode.

**AOT (ahead-of-time) compilation** — Compiling to native code before shipping (e.g. .NET Native AOT, GraalVM native-image), instead of shipping bytecode.

**Packer** — A wrapper that compresses or encrypts a program and unpacks it at runtime.

**Anti-tamper / integrity check** — Code that detects whether the app has been modified and reacts (stops, reports, disables features).

**Anti-debugging** — Techniques that detect when someone is inspecting the running app with a debugger.

**Hooking / Frida** — Intercepting an app's functions while it runs to change their behaviour (e.g. make "isPremium" always return true). Frida is the popular tool.

**RASP (runtime application self-protection)** — A security layer inside the app that watches for rooting, jailbreaks, hooking, emulators and tampering while it runs.

**Root / jailbreak** — Removing the phone's built-in restrictions; gives an attacker full control of the device.

**App attestation** — The phone's operating system vouches to *your server* that a request comes from your genuine, unmodified app. Play Integrity (Android) and App Attest (iOS).

**Certificate pinning** — The app only trusts your server's specific certificate, making it harder to spy on its network traffic.

**Server-side logic** — Keeping the valuable part of the product on your own servers. Users get the results, never the code.

**Entitlement check** — The check that decides whether a user has paid for a feature. In the client it can be patched; on the server it can't.

**Licence key / signed licence** — Proof of purchase. A signed licence is created with a private key only you hold, so it can't be forged.

**DRM** — Digital rights management: technology that restricts copying or use of a product.

**Watermarking / fingerprinting** — Hiding an invisible, unique mark in each copy so a leak can be traced to its source.

**Trap record / copyright trap / honeytoken** — A fake but harmless entry planted in your data or code. If it appears in someone else's product, it proves they copied you.

**Rate limiting** — Capping how many requests someone can make in a given time; stops bulk scraping and abuse.

**Scraping** — Automatically harvesting data from a website or API.

**Distillation** — Training a copy of an AI model on the answers of the original.

**Clean-room reimplementation** — Rebuilding a product from its public behaviour and documentation, by people who never saw the original code. Generally legal.

**Behavioural cloning** — Copying what a product *does* (features, UX, flows) rather than its code. AI makes this fast.

**Moat** — Whatever makes a product hard to replace even if it's copied: data, network effects, integrations, brand, contracts.

**Trade secret** — Valuable confidential information protected by law as long as you keep it secret with reasonable measures.

**EULA / ToS** — End-user licence agreement / terms of service: the contract users accept, which can forbid certain uses.

**Takedown (DMCA / notice-and-action)** — A formal request to a platform (GitHub, app store, host) to remove infringing material.
