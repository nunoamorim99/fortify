# Legal & business protection primer

**Always tell the user:** this is general information, not legal advice; laws differ by country and change; for real disputes or registrations, consult a lawyer specialised in IP/technology. Verify any specific article or case before quoting it in a report.

## What the law does and doesn't protect

| Protection | What it covers | What it doesn't | How to get it |
|---|---|---|---|
| **Copyright** | The code itself (literal source and object code), written docs, artwork, audio, UI graphics, text | Ideas, features, functionality, algorithms as such, programming languages, data formats. A clean-room clone that only reproduces behaviour usually isn't infringement. | Automatic on creation. Keep dated evidence (commits, releases). |
| **Trademark** | Product name, logo, distinctive branding | Features or code | Register (national office, EUIPO for the EU, USPTO for US). Cheap relative to its value — clones can't use your name. |
| **Design rights** | Visual appearance, potentially including GUI elements and icons | Underlying functionality | EU registered/unregistered Community design; national registrations. |
| **Patents** | Novel, inventive technical solutions — can cover a method regardless of how the code is written | In Europe, software "as such" isn't patentable; needs a technical character/effect. Expensive and slow. | Patent office filing (EPO, INPI-PT, USPTO). |
| **Trade secrets** | Confidential know-how: server-side algorithms, data, processes — as long as reasonable secrecy measures exist | Anything shipped to users is not secret; reverse engineering a lawfully obtained product is generally lawful | NDAs, access control, keeping the secret off the client. |
| **Database right (EU)** | Substantial investment in obtaining, verifying or presenting a database — protects against extraction of substantial parts | Individual facts; databases without substantial investment | Automatic in the EU (Database Directive 96/9/EC). Very relevant for data products. |
| **Contract (EULA / ToS / API terms)** | Can forbid scraping, bulk extraction, competitive use, redistribution | Can't override rights the law makes mandatory (see EU decompilation below); only binds people who accepted it | Clear terms accepted at sign-up / install. |

## European Union and Portugal

- **Computer Programs Directive 2009/24/EC** (in Portugal, transposed by Decreto-Lei n.º 252/94 and later amendments):
  - Protects programs as literary works; ideas and principles underlying them are not protected.
  - A lawful user may **observe, study and test** the program to determine the ideas behind it (Art. 5(3)).
  - **Decompilation is allowed for interoperability** under conditions (Art. 6).
  - Contract clauses contrary to Arts. 5(3) and 6 are void (Art. 8). So an EU EULA can't fully ban this.
- **Trade Secrets Directive (EU) 2016/943**: reverse engineering of a product that was lawfully acquired is a lawful way to obtain information (Art. 3), unless a valid contractual duty restricts it.
- **Database Directive 96/9/EC**: sui generis right for databases with substantial investment.
- **Anti-circumvention** (InfoSoc Directive 2001/29/EC, Art. 6; and Art. 7 of 2009/24/EC for means to remove program protection): circumventing or distributing tools to circumvent technical protection can be unlawful.
- **Digital Services Act**: platforms must provide notice-and-action mechanisms to report illegal content, including IP infringement.
- **GDPR**: any tamper/licence telemetry that processes personal data needs a lawful basis and disclosure.

## United States (for products sold there)

- Copyright protects code, not functionality; clean-room and interoperability reverse engineering has been held to be fair use in cases such as Sega v. Accolade (1992) and Sony v. Connectix (2000).
- **DMCA §1201** prohibits circumventing technical protection measures, with exemptions (including for interoperability and security research).
- EULA anti-reverse-engineering clauses have often been enforced as contract terms (e.g. Bowers v. Baystate, 2003).
- **DMCA takedowns (§512)** are the standard way to remove infringing copies from GitHub, hosts and stores.
- Software patents are more available than in Europe, though narrowed after Alice v. CLS Bank (2014).

## Practical playbook

1. **Register the trademark** for the product name and logo in the markets you sell in.
2. **Keep evidence of authorship**: version control history, dated releases, design files, trap records.
3. **Write clear terms**: forbid scraping, bulk extraction, automated access beyond quotas, model distillation, competitive use, redistribution.
4. **Keep trade secrets secret**: server-side, access-controlled, NDAs with staff and contractors.
5. **Know the takedown routes**: GitHub DMCA form, Apple and Google app store IP complaint forms, hosting providers' abuse/notice-and-action channels, EU DSA notice mechanisms.
6. **Patents** only when there's a genuinely novel technical invention and budget — talk to a patent attorney first.
7. **Open-source compliance**: obfuscation doesn't remove obligations. GPL/AGPL code may require providing source; separate proprietary components cleanly.

## The honest bottom line

Law protects your *expression* (code, assets, brand) and certain investments (databases, secrets you actually keep secret). It does not stop a competitor from building the same features independently. Against behavioural cloning, the defences are brand, data, network effects, integrations, speed and customer trust.
