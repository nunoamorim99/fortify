#!/usr/bin/env python3
"""
Fortify scanner — detects a project's stack and flags exposure issues
that make it easier to reverse engineer, crack, scrape or clone.

Usage:
    python3 scan.py <project-root> [--json out.json] [--max-files N]

Standard library only. Read-only: it never modifies the project.
Secrets found are masked in all output. Findings are heuristics — confirm each
one by opening the file before reporting it.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", ".idea",
    ".vscode", ".gradle", "Pods", "DerivedData", "Library", "Temp", "Obj",
    "obj", "bin", "target", ".dart_tool", ".pub-cache", "vendor", ".tox",
    ".mypy_cache", ".pytest_cache", ".cache", ".turbo", "coverage",
    ".expo", ".svelte-kit", "Logs", "UserSettings",
}
# Build-output folders: scanned only for shipped artefacts (maps, bundled secrets).
BUILD_DIRS = {"dist", "build", "out", ".next", ".output", "public", "www", "release"}
TEXT_LIMIT = 3_000_000
MAX_LOCATIONS = 8

SEV_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def mask(value: str) -> str:
    value = value.strip()
    return f"{value[:4]}… ({len(value)} chars)" if len(value) > 4 else "…"


def read_text(path: Path):
    try:
        if path.stat().st_size > TEXT_LIMIT:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data[:2048]:
        return None
    return data.decode("utf-8", errors="replace")


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


class Findings:
    def __init__(self):
        self.items = {}

    def add(self, fid, severity, vector, title, meaning, fix, location=None, detail=None):
        f = self.items.get(fid)
        if f is None:
            f = {
                "id": fid, "severity": severity, "vector": vector, "title": title,
                "meaning": meaning, "fix": fix, "locations": [], "details": [],
                "count": 0,
            }
            self.items[fid] = f
        elif SEV_ORDER[severity] < SEV_ORDER[f["severity"]]:
            f["severity"] = severity
        f["count"] += 1
        if location and len(f["locations"]) < MAX_LOCATIONS and location not in f["locations"]:
            f["locations"].append(location)
        if detail and len(f["details"]) < MAX_LOCATIONS and detail not in f["details"]:
            f["details"].append(detail)

    def sorted(self):
        return sorted(self.items.values(), key=lambda f: (SEV_ORDER[f["severity"]], f["id"]))


# --------------------------------------------------------------------------- #
# File inventory
# --------------------------------------------------------------------------- #

def inventory(root: Path, max_files: int):
    files, truncated = [], False
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".xcarchive")]
        for name in filenames:
            files.append(Path(dirpath) / name)
            if len(files) >= max_files:
                truncated = True
                return files, truncated
    return files, truncated


def in_build_dir(rel: Path) -> bool:
    return any(p in BUILD_DIRS for p in rel.parts[:-1])


# --------------------------------------------------------------------------- #
# Stack detection
# --------------------------------------------------------------------------- #

FRONTEND_DEPS = {"react", "react-dom", "vue", "svelte", "@angular/core", "next", "nuxt",
                 "solid-js", "preact", "@sveltejs/kit", "astro", "vite", "@remix-run/react"}
SERVER_DEPS = {"express", "fastify", "@nestjs/core", "koa", "hono", "@hapi/hapi",
               "next", "nuxt", "@sveltejs/kit", "@remix-run/node"}


def load_package_jsons(root, files):
    pkgs = []
    for f in files:
        if f.name == "package.json" and not in_build_dir(f.relative_to(root)):
            txt = read_text(f)
            if not txt:
                continue
            try:
                data = json.loads(txt)
            except ValueError:
                continue
            deps = {}
            for key in ("dependencies", "devDependencies", "optionalDependencies"):
                deps.update(data.get(key) or {})
            pkgs.append((f, data, deps))
    return pkgs


def detect_stack(root, files, pkgs):
    tags, evidence = set(), {}

    def tag(t, why):
        tags.add(t)
        evidence.setdefault(t, why)

    for f, data, deps in pkgs:
        rel = str(f.relative_to(root))
        names = set(deps)
        if names & FRONTEND_DEPS:
            tag("web-frontend", rel)
        if names & SERVER_DEPS:
            tag("node-server", rel)
        if "electron" in names:
            tag("electron", rel)
        if "react-native" in names or "expo" in names:
            tag("react-native", rel)
        if not names & (FRONTEND_DEPS | SERVER_DEPS | {"electron", "react-native", "expo"}) and (data.get("main") or data.get("exports")):
            tag("js-library", rel)

    for f in files:
        rel = f.relative_to(root)
        n = f.name
        s = str(rel)
        if n in ("build.gradle", "build.gradle.kts"):
            txt = read_text(f) or ""
            if "com.android.application" in txt or "com.android.library" in txt:
                tag("android", s)
            elif "java" in txt or "kotlin" in txt:
                tag("jvm", s)
        elif n == "AndroidManifest.xml":
            tag("android", s)
        elif n == "pom.xml":
            tag("jvm", s)
        elif n in ("Podfile", "Package.swift") or f.suffix == ".pbxproj":
            tag("ios", s)
        elif n == "pubspec.yaml":
            txt = read_text(f) or ""
            if "flutter" in txt:
                tag("flutter", s)
        elif f.suffix == ".csproj":
            txt = read_text(f) or ""
            if "Microsoft.NET.Sdk.Web" in txt:
                tag("dotnet-server", s)
            else:
                tag("dotnet-desktop", s)
        elif n == "Cargo.toml":
            tag("rust", s)
        elif n == "go.mod":
            tag("go", s)
        elif n in ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile"):
            tag("python", s)
        elif f.suffix == ".spec" and "pyinstaller" in (read_text(f) or "").lower():
            tag("pyinstaller", s)
        elif n == "ProjectSettings.asset":
            tag("unity", s)
        elif f.suffix == ".uproject":
            tag("unreal", s)
        elif n == "project.godot":
            tag("godot", s)
        elif n == "CMakeLists.txt":
            tag("native-c-cpp", s)

    for f in files:
        if f.name in ("requirements.txt", "pyproject.toml", "Pipfile"):
            txt = (read_text(f) or "").lower()
            if re.search(r"\b(django|flask|fastapi|starlette|aiohttp|sanic|tornado)\b", txt):
                tag("python-server", str(f.relative_to(root)))
            if "pyinstaller" in txt:
                tag("pyinstaller", str(f.relative_to(root)))
        if f.name == "Cargo.toml":
            txt = (read_text(f) or "").lower()
            if re.search(r"\b(axum|actix-web|rocket|warp|poem)\b", txt):
                tag("rust-server", str(f.relative_to(root)))
        if f.name == "go.mod":
            txt = (read_text(f) or "").lower()
            if re.search(r"(gin-gonic|labstack/echo|gofiber|go-chi|gorilla/mux)", txt):
                tag("go-server", str(f.relative_to(root)))
    return tags, evidence


CLIENT_EXT_TAGS = {
    ".js": {"web-frontend", "react-native", "electron"},
    ".jsx": {"web-frontend", "react-native", "electron"},
    ".ts": {"web-frontend", "react-native", "electron"},
    ".tsx": {"web-frontend", "react-native", "electron"},
    ".mjs": {"web-frontend", "electron"},
    ".vue": {"web-frontend"},
    ".svelte": {"web-frontend"},
    ".astro": {"web-frontend"},
    ".dart": {"flutter"},
    ".kt": {"android"},
    ".java": {"android"},
    ".swift": {"ios"},
    ".m": {"ios"},
    ".cs": {"unity", "dotnet-desktop"},
    ".gd": {"godot"},
}
SERVER_PATH_HINTS = {"server", "api", "backend", "functions", "lambda", "lambdas", "worker",
                     "workers", "routes", "controllers", "migrations", "scripts", "test",
                     "tests", "__tests__", "spec", "e2e", "cypress", "supabase", "prisma",
                     "seed", "seeds", "mocks", "__mocks__", "stories", "fixtures"}


def is_client_file(rel: Path, tags) -> bool:
    need = CLIENT_EXT_TAGS.get(rel.suffix.lower())
    if not need or not (need & tags):
        return False
    parts = {p.lower() for p in rel.parts[:-1]}
    if parts & SERVER_PATH_HINTS:
        return False
    name = rel.name.lower()
    if any(x in name for x in (".test.", ".spec.", ".config.", ".stories.", "server.", ".server.")):
        return False
    if name.startswith(("vite.config", "webpack.config", "next.config", "nuxt.config",
                        "tailwind.config", "postcss.config", "eslint", "jest.config")):
        return False
    return True


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

# (label, cheap substring hints, pattern). The regex only runs when a hint is present.
SECRET_PATTERNS = [
    ("AWS access key", ("AKIA",), re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
    ("Stripe secret key", ("_live_",), re.compile(r"\b((?:sk|rk)_live_[0-9A-Za-z]{16,})")),
    ("Private key block", ("PRIVATE KEY-----",),
     re.compile(r"(-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----)\s*\n\s*[A-Za-z0-9+/=]{40,}")),
    ("GitHub token", ("ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_"),
     re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})")),
    ("Anthropic API key", ("sk-ant-",), re.compile(r"\b(sk-ant-[A-Za-z0-9_\-]{20,})")),
    ("OpenAI API key", ("sk-",), re.compile(r"\b(sk-(?:proj-|svcacct-)?[A-Za-z0-9_\-]{32,})")),
    ("Google API key", ("AIza",), re.compile(r"\b(AIza[0-9A-Za-z_\-]{35})\b")),
    ("Slack token", ("xox",), re.compile(r"\b(xox[baprs]-[A-Za-z0-9\-]{10,})")),
    ("SendGrid key", ("SG.",), re.compile(r"\b(SG\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,})")),
]
PUBLIC_ENV_HINTS = ("VITE_", "NEXT_PUBLIC_", "REACT_APP_", "PUBLIC_", "EXPO_PUBLIC_", "GATSBY_", "STORYBOOK_")
SECRET_NAME_HINTS = ("key", "secret", "passw", "token")


def looks_random(val: str) -> bool:
    """Real secrets mix character classes; identifiers and enum values usually don't."""
    classes = sum(bool(re.search(p, val)) for p in (r"[a-z]", r"[A-Z]", r"[0-9]"))
    has_digit = bool(re.search(r"[0-9]", val))
    return classes >= 2 and has_digit and not re.fullmatch(r"[a-z]+(?:[_\-.][a-z0-9]+)+", val)
# Linear-time: find string assignments first, then test the key name.
ASSIGNMENT = re.compile(r"""\b([A-Za-z_][A-Za-z0-9_]{2,60})['"]?\s*[:=]\s*['"]([^'"\s]{12,200})['"]""")
SECRET_NAME = re.compile(r"(?i)(api[_-]?key|secret|passwd|password|private[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret)")
PLACEHOLDER = re.compile(r"(?i)(your|example|sample|changeme|change_me|placeholder|xxxx|dummy|test|fake|<|\$\{|process\.env|import\.meta|todo|redacted|\*\*\*)")

PUBLIC_ENV = re.compile(
    r"\b((?:VITE|NEXT_PUBLIC|REACT_APP|PUBLIC|NUXT_PUBLIC|EXPO_PUBLIC|GATSBY|STORYBOOK)_[A-Z0-9_]*(SECRET|PRIVATE|PASSWORD|PASSWD|TOKEN|KEY)[A-Z0-9_]*)\b"
)
LIKELY_PUBLISHABLE = re.compile(r"(PUBLISHABLE|ANON|PUBLIC_KEY|MAPS|SITE_KEY|MEASUREMENT|SENTRY_DSN|POSTHOG|FIREBASE_API_KEY)")

ENTITLEMENT = re.compile(
    r"\b(?:is|has|user\.|account\.)(?:Premium|Pro|Paid|Subscribed|Subscriber|Vip|VIP|Licen[cs]ed|Unlocked|Purchased|Plus|Gold)\b"
    r"|\b(?:premium|pro|paid|plan|tier|subscription)\s*(?:===?|!==?)\s*['\"](?:premium|pro|paid|plus|gold|enterprise|business)['\"]"
)
AI_BROWSER = re.compile(r"dangerouslyAllowBrowser\s*:\s*true")
AI_SDK_IMPORT = re.compile(r"""(?:from\s+|require\()\s*['"](openai|@anthropic-ai/sdk|@google/generative-ai|@google/genai|@mistralai/mistralai|groq-sdk)['"]""")
LONG_PROMPT = re.compile(r"""(?is)['"`]\s*You are (?:a|an|the)\b.{200,}?['"`]""")

RATE_LIMIT_MARKERS = re.compile(
    r"(express-rate-limit|rate-limiter-flexible|@nestjs/throttler|@fastify/rate-limit|hono-rate-limiter|"
    r"@upstash/ratelimit|slowapi|django[-_]ratelimit|flask[-_]limiter|fastapi[-_]limiter|rack-attack|"
    r"tower_governor|governor|actix-governor|golang\.org/x/time/rate|ulule/limiter|AddRateLimiter|"
    r"AspNetCoreRateLimit|RateLimiter|ratelimit|rateLimit|throttle)"
)


def check_secrets_and_client(root, files, tags, fs: Findings):
    any_ai_server = False
    for f in files:
        rel = f.relative_to(root)
        suffix = f.suffix.lower()
        name = f.name
        if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".mp3", ".mp4",
                      ".wav", ".ogg", ".ttf", ".otf", ".woff", ".woff2", ".pdf", ".zip", ".lock"} \
                or name in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock", "poetry.lock"):
            continue
        build = in_build_dir(rel)

        if suffix == ".map" and build:
            fs.add("published-source-maps", "high", "Code extraction",
                   "Source maps in build output",
                   "Source maps turn your minified bundle back into the original source code, comments included. If they are deployed, anyone can read your code in the browser.",
                   "Disable public source maps in the production build (Vite build.sourcemap false/'hidden', webpack devtool false/hidden-source-map, Next.js productionBrowserSourceMaps false, CRA GENERATE_SOURCEMAP=false). Upload them privately to your error tracker instead. Then check the live site for *.map files.",
                   str(rel))
            continue

        text = read_text(f)
        if text is None:
            continue

        # Specific secret patterns (source and build output).
        for label, hints, pat in SECRET_PATTERNS:
            if not any(h in text for h in hints):
                continue
            for m in pat.finditer(text):
                val = m.group(1)
                if label == "OpenAI API key" and val.startswith("sk-ant-"):
                    continue
                where = "shipped build output" if build else ("client code" if is_client_file(rel, tags) else "repository")
                fs.add("hardcoded-secret", "high", "Secret & asset leakage",
                       "Secrets written into code or build output",
                       "A real credential is stored in the code. Anyone with the repository or the shipped app can extract and abuse it, and it can be used to read your data or run up your bills.",
                       "Move it to server-side environment variables or a secret manager, keep it out of client code, and ROTATE the key now — assume the old one is leaked. Add a secret scanner (e.g. gitleaks) to CI.",
                       f"{rel}:{line_of(text, m.start())}", f"{label} {mask(val)} in {where}")

        if build:
            continue

        # Generic secret assignments in source.
        lower = text.lower()
        if suffix not in {".md", ".txt", ".rst", ".html"} and ".example" not in name and ".sample" not in name \
                and any(h in lower for h in SECRET_NAME_HINTS):
            for m in ASSIGNMENT.finditer(text):
                key, val = m.group(1), m.group(2)
                if not SECRET_NAME.search(key):
                    continue
                if PLACEHOLDER.search(val) or PLACEHOLDER.search(key) and "test" in key.lower():
                    continue
                if not looks_random(val):
                    continue  # looks like an identifier, enum value or placeholder
                client = is_client_file(rel, tags)
                fs.add("possible-hardcoded-secret", "high" if client else "medium", "Secret & asset leakage",
                       "Possible secrets assigned in code",
                       "A variable named like a key, token or password is set to a literal value. If it's real, it is exposed to anyone who can read this code" + (" — and this file ships to users' devices." if client else "."),
                       "Confirm whether the value is real. If so, move it to server-side configuration and rotate it.",
                       f"{rel}:{line_of(text, m.start())}", f"{key} = {mask(val)}")

        # Public-prefixed env vars that look secret (skip docs).
        scan_env = suffix not in {".md", ".txt", ".rst", ".html", ".py"} and any(h in text for h in PUBLIC_ENV_HINTS)
        for m in (PUBLIC_ENV.finditer(text) if scan_env else ()):
            var = m.group(1)
            if LIKELY_PUBLISHABLE.search(var):
                fs.add("public-env-publishable", "info", "Secret & asset leakage",
                       "Publishable keys exposed to the client (usually fine)",
                       "These variables are bundled into the client. Names suggest publishable keys designed to be public — make sure they are restricted (allowed domains/apps, row-level security, quotas).",
                       "Restrict each key in the provider's console (HTTP referrers, bundle IDs, RLS policies, quotas).",
                       f"{rel}:{line_of(text, m.start())}", var)
            else:
                fs.add("public-env-secret", "high", "Secret & asset leakage",
                       "Secret-looking variables exposed through a public env prefix",
                       "Variables with prefixes like VITE_, NEXT_PUBLIC_ or REACT_APP_ are copied into the code sent to every user. Anything secret here is public.",
                       "Rename without the public prefix and use it only in server code (API route, server action, backend). Rotate the value if it was ever deployed.",
                       f"{rel}:{line_of(text, m.start())}", var)

        client = is_client_file(rel, tags)
        if client:
            for m in ENTITLEMENT.finditer(text):
                fs.add("client-entitlement", "medium", "Piracy & tampering",
                       "Paid-feature checks happen in the client",
                       "The decision 'is this user allowed to use the paid feature?' is made in code running on the user's device. It can be patched or hooked to always say yes.",
                       "Make the server the source of truth: paid data and actions should only be returned by the server after it verifies the subscription. Client checks can stay for UI only.",
                       f"{rel}:{line_of(text, m.start())}", m.group(0))
            for m in AI_BROWSER.finditer(text):
                fs.add("ai-key-in-browser", "high", "Secret & asset leakage",
                       "AI provider called directly from the browser",
                       "dangerouslyAllowBrowser means the AI provider's API key is sent to every user's browser. Anyone can copy it and use your account, and your prompts are visible.",
                       "Call the AI provider from your server only; the browser calls your server.",
                       f"{rel}:{line_of(text, m.start())}")
            for m in AI_SDK_IMPORT.finditer(text):
                fs.add("ai-sdk-in-client", "medium", "Secret & asset leakage",
                       "AI SDK imported in client code",
                       "An AI provider SDK is used in code that likely ships to users, which usually means the key and prompts ship too.",
                       "Confirm the file runs only on the server (e.g. a Next.js server component/route). If it runs in the client, move the call server-side.",
                       f"{rel}:{line_of(text, m.start())}", m.group(1))
            for m in LONG_PROMPT.finditer(text):
                fs.add("prompt-in-client", "medium", "Code extraction",
                       "AI prompts embedded in client code",
                       "Long system prompts are often a product's secret sauce. In client code they can be read by anyone.",
                       "Keep prompts on the server and expose only the result.",
                       f"{rel}:{line_of(text, m.start())}")
        else:
            if AI_SDK_IMPORT.search(text):
                any_ai_server = True
    return any_ai_server


def check_source_map_config(root, files, fs):
    for f in files:
        n = f.name
        rel = f.relative_to(root)
        if in_build_dir(rel):
            continue
        if n.startswith("vite.config"):
            txt = read_text(f) or ""
            m = re.search(r"sourcemap\s*:\s*(true|['\"]inline['\"])", txt)
            if m:
                fs.add("sourcemap-config", "high", "Code extraction", "Build configured to publish source maps",
                       "The production build generates public source maps, which reveal your original source code.",
                       "Set build.sourcemap to false or 'hidden' and upload maps privately to your error tracker.",
                       f"{rel}:{line_of(txt, m.start())}")
        elif n.startswith("webpack") and n.endswith((".js", ".ts", ".cjs", ".mjs")):
            txt = read_text(f) or ""
            for m in re.finditer(r"devtool\s*:\s*['\"]([^'\"]+)['\"]", txt):
                if "hidden" not in m.group(1) and "nosources" not in m.group(1):
                    fs.add("sourcemap-config", "medium", "Code extraction", "Build configured to publish source maps",
                           "webpack devtool emits source maps linked from the bundle; if this is the production config, your source is public.",
                           "Use devtool: false or 'hidden-source-map' for production.",
                           f"{rel}:{line_of(txt, m.start())}", m.group(1))
        elif n.startswith("next.config"):
            txt = read_text(f) or ""
            m = re.search(r"productionBrowserSourceMaps\s*:\s*true", txt)
            if m:
                fs.add("sourcemap-config", "high", "Code extraction", "Build configured to publish source maps",
                       "Next.js is set to ship browser source maps in production.",
                       "Remove productionBrowserSourceMaps or set it to false.",
                       f"{rel}:{line_of(txt, m.start())}")
        elif n.startswith(".env"):
            txt = read_text(f) or ""
            m = re.search(r"GENERATE_SOURCEMAP\s*=\s*true", txt)
            if m:
                fs.add("sourcemap-config", "high", "Code extraction", "Build configured to publish source maps",
                       "Create React App will publish source maps.", "Set GENERATE_SOURCEMAP=false for production builds.",
                       f"{rel}:{line_of(txt, m.start())}")


def check_env_committed(root, files, fs):
    env_files = [f for f in files if f.name.startswith(".env") and not any(
        x in f.name for x in (".example", ".sample", ".template", ".dist", ".defaults"))]
    if not env_files:
        return
    gitignore = ""
    gi = root / ".gitignore"
    if gi.exists():
        gitignore = read_text(gi) or ""
    ignored = re.search(r"(?m)^\s*\.env(\*|\..*|\s*$)", gitignore)
    if not ignored:
        for f in env_files:
            fs.add("env-not-ignored", "medium", "Secret & asset leakage", ".env files may be committed",
                   "Environment files usually hold secrets. .gitignore doesn't exclude them, so they may be in the repository history.",
                   "Add .env* to .gitignore (keep a .env.example without values), check git history, and rotate anything that was committed.",
                   str(f.relative_to(root)))


def check_android(root, files, fs):
    for f in files:
        rel = f.relative_to(root)
        if f.name in ("build.gradle", "build.gradle.kts"):
            txt = read_text(f) or ""
            if "com.android.application" not in txt:
                continue
            rel_block = re.search(r"release\s*\{(.*?)\n\s*\}", txt, re.S)
            body = rel_block.group(1) if rel_block else ""
            if not re.search(r"(isMinifyEnabled\s*=\s*true|minifyEnabled\s*\(?\s*true)", body):
                fs.add("android-no-minify", "high", "Code extraction", "Android release build is not shrunk or obfuscated",
                       "Without R8 minification, anyone can open your APK with a decompiler (jadx) and read near-original code with real class and method names.",
                       "In the release build type set isMinifyEnabled = true and isShrinkResources = true, add proguard-rules for reflection-based libraries, test the release build, and keep mapping.txt private for crash reports.",
                       str(rel))
            if re.search(r"(isDebuggable\s*=\s*true|debuggable\s*\(?\s*true)", body):
                fs.add("android-debuggable", "high", "Piracy & tampering", "Android release build is debuggable",
                       "A debuggable release lets anyone attach a debugger and inspect or change the app while it runs.",
                       "Remove debuggable true from the release build type.", str(rel))
        elif f.name == "AndroidManifest.xml":
            txt = read_text(f) or ""
            m = re.search(r'android:debuggable\s*=\s*"true"', txt)
            if m:
                fs.add("android-debuggable", "high", "Piracy & tampering", "Android release build is debuggable",
                       "android:debuggable=\"true\" in the manifest makes the app debuggable.",
                       "Remove the attribute; Gradle sets it correctly per build type.",
                       f"{rel}:{line_of(txt, m.start())}")
            m = re.search(r'android:allowBackup\s*=\s*"true"', txt)
            if m:
                fs.add("android-allow-backup", "low", "Secret & asset leakage", "Android app data can be backed up and extracted",
                       "allowBackup lets app data be copied off the device, including tokens or cached premium content.",
                       "Set allowBackup=\"false\" or define backup rules that exclude sensitive files.",
                       f"{rel}:{line_of(txt, m.start())}")


def has_marker(files, root, pattern, names=None, suffixes=None):
    rx = re.compile(pattern)
    for f in files:
        if names or suffixes:
            wanted = (names and f.name in names) or (suffixes and f.suffix in suffixes)
            if not wanted:
                continue
        if in_build_dir(f.relative_to(root)):
            continue
        txt = read_text(f)
        if txt and rx.search(txt):
            return True
    return False


def check_mobile_attestation(root, files, tags, fs):
    if not tags & {"android", "ios", "flutter", "react-native"}:
        return
    found = has_marker(files, root,
                       r"(play:integrity|IntegrityManager|DCAppAttestService|AppAttest|freerasp|talsec|app-check|AppCheck|react-native-device-check|DexGuard|iXGuard|promon|appdome)",
                       suffixes={".gradle", ".kts", ".swift", ".m", ".dart", ".ts", ".tsx", ".js", ".json", ".yaml", ".lock", ".xml"})
    if not found:
        fs.add("mobile-no-attestation", "low", "Piracy & tampering", "No app attestation or runtime protection found",
               "Your server can't tell whether requests come from your genuine app or from a modified copy or a script.",
               "Add Play Integrity (Android) and App Attest (iOS) — or Firebase App Check, which wraps both — and verify the verdict on your server before serving paid or sensitive data. Consider freeRASP for root/hook detection.")


def check_flutter(root, files, tags, fs):
    if "flutter" not in tags:
        return
    builds = []
    for f in files:
        if f.suffix in (".yml", ".yaml", ".sh", ".ps1", ".bat") or f.name in ("Makefile", "Fastfile", "codemagic.yaml"):
            txt = read_text(f) or ""
            for m in re.finditer(r"flutter\s+build\s+[^\n]*", txt):
                builds.append((f, txt, m))
    if not builds:
        fs.add("flutter-obfuscate-unknown", "info", "Code extraction", "Check Flutter release builds are obfuscated",
               "No build script found, so the scanner can't tell whether releases use Dart obfuscation.",
               "Build releases with --obfuscate --split-debug-info=<private dir>.")
    for f, txt, m in builds:
        if "--obfuscate" not in m.group(0):
            fs.add("flutter-no-obfuscate", "medium", "Code extraction", "Flutter release build without obfuscation",
                   "Without --obfuscate, class and function names stay readable in the compiled app.",
                   "Add --obfuscate --split-debug-info=<private dir> to release builds and keep the symbols private.",
                   f"{f.relative_to(root)}:{line_of(txt, m.start())}", m.group(0).strip()[:80])


def check_electron(root, pkgs, tags, files, fs):
    if "electron" not in tags:
        return
    names = set()
    for f, data, deps in pkgs:
        names |= set(deps)
        build = data.get("build") or {}
        if isinstance(build, dict) and build.get("asar") is False:
            fs.add("electron-no-asar", "medium", "Code extraction", "Electron app ships unpacked source",
                   "With asar disabled, your app's source files ship as plain files.",
                   "Enable asar (it's packaging, not protection) and combine it with fuses and integrity validation.",
                   str(f.relative_to(root)))
    if "@electron/fuses" not in names and not has_marker(files, root, r"(FuseV1Options|flipFuses|electronFuses)", suffixes={".js", ".ts", ".cjs", ".mjs", ".json"}):
        fs.add("electron-no-fuses", "medium", "Piracy & tampering", "Electron fuses not configured",
               "The app's code in app.asar can be extracted with one command (npx asar extract) and modified; by default the app may also run as plain Node or accept debugger flags.",
               "Use @electron/fuses: enable EnableEmbeddedAsarIntegrityValidation and OnlyLoadAppFromAsar, disable RunAsNode and EnableNodeCliInspectArguments. Move sensitive logic to a server or native module; consider bytenode for key modules.")


def check_rust(root, files, tags, fs):
    for f in files:
        if f.name != "Cargo.toml":
            continue
        txt = read_text(f) or ""
        if "[package]" not in txt and "[workspace]" not in txt:
            continue
        block = re.search(r"\[profile\.release\](.*?)(?:\n\[|\Z)", txt, re.S)
        body = block.group(1) if block else ""
        if not re.search(r"strip\s*=\s*(true|\"symbols\")", body) and "rust-server" not in tags:
            fs.add("rust-not-stripped", "low", "Code extraction", "Rust release binary keeps symbols",
                   "Function names left in the binary make decompiling much easier.",
                   "In [profile.release] set strip = true, lto = true, panic = \"abort\"; build with --remap-path-prefix to hide local paths.",
                   str(f.relative_to(root)))


def check_python(root, files, tags, fs):
    if "pyinstaller" in tags and not has_marker(
            files, root, r"(?i)(pyarmor|nuitka|cython)",
            names={"requirements.txt", "pyproject.toml", "Pipfile", "setup.py"}, suffixes={".spec", ".yml", ".yaml", ".sh"}):
        fs.add("python-pyinstaller-only", "medium", "Code extraction", "Python app packaged with PyInstaller only",
               "PyInstaller bundles .pyc files that can be extracted and decompiled back to readable Python in minutes.",
               "Compile sensitive modules with Nuitka or Cython, or use PyArmor; better, keep the core logic behind an API.")


def check_unity(root, files, fs):
    for f in files:
        if f.name != "ProjectSettings.asset":
            continue
        txt = read_text(f) or ""
        m = re.search(r"scriptingBackend:\s*(\{\}|\n((?:\s{4,}\S.*\n)+))", txt)
        if not m:
            continue
        entries = re.findall(r"^\s{4,}(\w+):\s*(\d)", m.group(2) or "", re.M)
        mono = [p for p, v in entries if v == "0"]
        if m.group(1).strip() == "{}" or not entries:
            fs.add("unity-mono", "medium", "Code extraction", "Unity uses the Mono scripting backend (default)",
                   "With Mono, your game's C# ships as DLLs that decompile almost perfectly (dnSpy/ILSpy).",
                   "Switch Player Settings > Scripting Backend to IL2CPP for release platforms; add an obfuscator for sensitive code.",
                   str(f.relative_to(root)), "default (no platform set)")
        elif mono:
            fs.add("unity-mono", "medium", "Code extraction", "Unity uses the Mono scripting backend",
                   "With Mono, your game's C# ships as DLLs that decompile almost perfectly (dnSpy/ILSpy).",
                   "Switch Player Settings > Scripting Backend to IL2CPP for these platforms; add an obfuscator for sensitive code.",
                   str(f.relative_to(root)), ", ".join(mono))


def check_dotnet(root, files, fs):
    for f in files:
        if f.suffix != ".csproj":
            continue
        txt = read_text(f) or ""
        if "Microsoft.NET.Sdk.Web" in txt:
            continue
        if not re.search(r"<OutputType>\s*(WinExe|Exe)\s*</OutputType>", txt) and "UseWPF" not in txt and "UseWindowsForms" not in txt and "UseMaui" not in txt:
            continue
        if re.search(r"(PublishAot>\s*true|Obfuscar|Dotfuscator|ConfuserEx|Eazfuscator|NETReactor|Babel\.Obfuscator|SmartAssembly)", txt):
            continue
        fs.add("dotnet-plain-il", "medium", "Code extraction", ".NET app ships plain IL",
               ".NET assemblies decompile back to near-original C# with free tools (ILSpy, dnSpyEx).",
               "Publish with Native AOT where libraries allow (<PublishAot>true</PublishAot>), or add an obfuscator (Obfuscar is free; Dotfuscator, .NET Reactor, Eazfuscator are commercial).",
               str(f.relative_to(root)))


def check_rate_limit(root, files, tags, fs):
    server = tags & {"node-server", "python-server", "dotnet-server", "rust-server", "go-server"}
    if not server:
        return
    found = has_marker(files, root, RATE_LIMIT_MARKERS.pattern,
                       suffixes={".json", ".js", ".ts", ".mjs", ".cjs", ".py", ".toml", ".txt", ".cs", ".rs", ".go", ".mod", ".rb", ".yaml", ".yml"})
    if not found:
        fs.add("no-rate-limit", "medium", "Data & API harvesting", "No rate limiting found in the server code",
               "Without request limits, a script can call your API thousands of times to scrape your data, map your behaviour for a clone, or distil your AI outputs.",
               "Add per-user/per-key rate limits and quotas on the API (or confirm they exist at the gateway/CDN, e.g. Cloudflare), and monitor for bulk access.")


def check_license(root, fs):
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "LICENCE"):
        p = root / name
        if p.exists():
            txt = (read_text(p) or "")[:4000]
            if re.search(r"GNU AFFERO|AGPL", txt):
                kind = "AGPL"
            elif re.search(r"GNU (GENERAL|LESSER) PUBLIC|GPL", txt):
                kind = "GPL/LGPL"
            elif "MIT License" in txt or "Permission is hereby granted, free of charge" in txt:
                kind = "MIT"
            elif "Apache License" in txt:
                kind = "Apache-2.0"
            elif "Redistribution and use in source and binary forms" in txt:
                kind = "BSD"
            else:
                kind = "custom/proprietary"
            sev = "medium" if kind in ("AGPL", "GPL/LGPL") else "info"
            fs.add("license", sev, "Legal", f"Project licence: {kind}",
                   "Open-source licences let others legally copy and reuse the code under their terms; copyleft licences (GPL/AGPL) can also oblige you to provide source, which conflicts with obfuscation."
                   if kind != "custom/proprietary" else "A custom licence file exists — check it states your rights and restrictions clearly.",
                   "Make sure the licence matches your intent. Keep proprietary parts in separate, clearly licensed components.",
                   name)
            return


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def exposure_score(findings):
    weights = {"high": 3, "medium": 2, "low": 1, "info": 0}
    score = sum(weights[f["severity"]] for f in findings)
    if any(f["severity"] == "high" for f in findings) and score >= 9:
        return "High"
    if score >= 6 or any(f["severity"] == "high" for f in findings):
        return "Medium-High"
    if score >= 3 or any(f["severity"] == "medium" for f in findings):
        return "Medium"
    return "Low"


def main():
    ap = argparse.ArgumentParser(description="Scan a project for clone/reverse-engineering exposure.")
    ap.add_argument("root", help="Project root folder")
    ap.add_argument("--json", help="Write findings to this JSON file")
    ap.add_argument("--max-files", type=int, default=40000)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Not a folder: {root}", file=sys.stderr)
        sys.exit(2)

    files, truncated = inventory(root, args.max_files)
    pkgs = load_package_jsons(root, files)
    tags, evidence = detect_stack(root, files, pkgs)

    fs = Findings()
    check_secrets_and_client(root, files, tags, fs)
    check_source_map_config(root, files, fs)
    check_env_committed(root, files, fs)
    check_android(root, files, fs)
    check_mobile_attestation(root, files, tags, fs)
    check_flutter(root, files, tags, fs)
    check_electron(root, pkgs, tags, files, fs)
    check_rust(root, files, tags, fs)
    check_python(root, files, tags, fs)
    check_unity(root, files, fs)
    check_dotnet(root, files, fs)
    check_rate_limit(root, files, tags, fs)
    check_license(root, fs)

    findings = fs.sorted()
    real = [f for f in findings if f["vector"] != "Legal"]
    result = {
        "root": str(root),
        "files_scanned": len(files),
        "truncated": truncated,
        "stack": sorted(tags),
        "stack_evidence": evidence,
        "scanner_exposure_hint": exposure_score(real),
        "findings": findings,
        "note": "Heuristic scan. Confirm each finding in the code before reporting. Behavioural cloning and moat are not measurable by scanning — assess them separately.",
    }

    print(f"Fortify scan — {root}")
    print(f"Files scanned: {len(files)}{' (truncated)' if truncated else ''}")
    print(f"Stack detected: {', '.join(sorted(tags)) or 'unknown'}")
    print(f"Exposure hint (code-level only): {result['scanner_exposure_hint']}\n")
    if not findings:
        print("No issues flagged by the scanner. Still assess behavioural cloning, API exposure and moat manually.")
    for f in findings:
        print(f"[{f['severity'].upper()}] {f['title']}  ({f['vector']}, {f['count']} hit{'s' if f['count'] != 1 else ''})")
        print(f"    What it means: {f['meaning']}")
        print(f"    Fix: {f['fix']}")
        for loc in f["locations"]:
            print(f"    - {loc}")
        for d in f["details"]:
            print(f"      · {d}")
        print()

    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"JSON written to {args.json}")


if __name__ == "__main__":
    main()
