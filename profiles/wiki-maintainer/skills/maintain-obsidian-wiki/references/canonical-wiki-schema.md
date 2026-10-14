# Šema kanonskih wiki stranica i prijema snimaka

Ovaj dokument je autoritativni ugovor za rad sa wiki sadržajem. Ne oslanjajte se
na `/workspace/SCHEMA.md`.

## Pitanje i definicija

Pitanje: Koja polja snimka, statusi, provera porekla i definicija bajtova za
`content_sha256` dozvoljavaju arhiviranje, a koji uslovi zahtevaju zadržavanje u
`Inbox`?

Kanonska stranica daje odluku ili postupak na osnovu evidentiranih izvora. Nije
sažetak članka. Sirovi snimak čuva izvorne bajtove i ne prepisuje se kao
kanonska stranica.

## Provera porekla i prijem snimka

### Trenutni snimak

Trenutni snimak mora da ima dostavljen i kanonski URL izvora, UTC
`retrieved_at`, važeći `capture_status` i `content_sha256` koji se podudara sa
sačuvanim bajtovima tela. Aktivni prijem koristi `supplied_url` kada je prisutan
i `canonical_url`. Stariji trenutni zapisi mogu imati `source_url` umesto
`supplied_url`. Ne menjajte naziv polja niti URL da biste zapis učinili
prihvatljivim. `canonical_url: unknown` ne dokazuje kanonski URL.

Važeći statusi trenutnog snimka su samo `complete`, `partial`, `shell` i
`failed`.

- `complete` može u arhivu tek kada su obavezna polja dokazana i
  `content_sha256` odgovara telu.
- `partial` ostaje u `Inbox`. Odložite ga dok novi dokaz ne promeni status.
- `shell` i `failed` ne idu u redovnu trijažu. Sačuvajte njihove originalne
  bajtove u `evidence-only/failed-sources/` zajedno sa URL-om izvora, razlogom
  neuspeha, vremenom preuzimanja i dokazom konačne dispozicije. Ne brišite ih i
  ne dodajte ih u rutinske liste za ponovni pokušaj. Ponovo ih proverite samo
  kada novi dokaz pokaže promenjen pristup ili stanje izvora.
- Status koji nije na ovoj listi nije važeći trenutni snimak. Zadržite ga u
  `Inbox`; ne normalizujte ga radi arhiviranja.

`complete` ne dokazuje da je svaka tvrdnja nezavisno proverena. On označava
potpun sačuvani snimak prema zapisu o preuzimanju. Nedostajuće slike,
nepristupačan izvor i druga neizvesnost ostaju zabeleženi u kanonskoj stranici.

### Stariji Markdown snimak

Stariji snimak može u pregledanu arhivu ako ima H1 naslov, `Source URL:` ili
`- Source:` red i `Captured:` ili `- Captured:` red. Ne odbijajte ga samo zato
što nema trenutno zaglavlje. Ako ne dokazuje naslov, izvor ili vreme snimanja,
zadržite ga u `Inbox`. Takođe zadržite prazan ili prekinut članak, na primer
onaj sa nezatvorenom ogradom za kod.

Za prihvaćen stariji snimak arhivska kopija dobija sledeća polja:

```yaml
legacy_capture: true
capture_status: legacy-reviewed
content_sha256: "<sha256>"
```

Dodajte izvor, UTC `captured_at`, `legacy_reviewed_at` i
`legacy_review_note`. Zadržite `capture_method`, `provider` i `model` samo kada
ih stari zapis navodi. `legacy-reviewed` ne dokazuje da je snimak potpun.
Izvorno Markdown telo ostaje neizmenjeno.

### Definicije bajtova za hash

Ne birajte novu granicu za hash zato što postojeći fajl ne prolazi proveru.
Granica mora biti eksplicitna i proverljiva.

- Za trenutni snimak koji koristi oznake tela, `content_sha256` je SHA-256 UTF-8
  bajtova između `<!-- SOURCE BODY START -->` i `<!-- SOURCE BODY END -->`.
  Početni novi red posle početne oznake i završni novi red pre završne oznake
  pripadaju telu. Oznake ne pripadaju telu.
- Ako trenutni zapis nema nedvosmislenu definiciju granice tela ili deklarisani
  hash ne odgovara njegovim sačuvanim bajtovima, ne može da prođe proveru
  porekla. Ostavite ga u `Inbox`; ne pretpostavljajte drugu granicu.
- Za arhivski snimak koji počinje YAML zaglavljem `---\n`, `content_sha256` je
  SHA-256 svih neizmenjenih sirovih bajtova posle zatvarajućeg razdelnika
  `\n---\n`. Zaglavlje i sam razdelnik nisu deo tela. Ne dekodirajte i ne
  ponovo kodirajte telo pre provere.

Pokrenite kanonsku proveru arhivskih tela komandom:

```text
python3 /workspace/.hermes-maintenance/wiki-audit.py --root /workspace
```

Ona proverava UTF-8 čitljivost, zaglavlja, Obsidian veze, inventar arhiva,
duplikate `content_sha256` i hash arhivskog tela. Ne dokazuje da izvor podržava
neku tvrdnju.

## Dispozicija, tema i pretraga

Pre QMD pretrage pronađite srodnu kanonsku stranicu. Za tačnu putanju koristite
pretragu fajlova. Izaberite jednu primarnu temu po sadržaju, ne po domenu
izvora. Za više tema ili nejasan sadržaj izaberite najjaču temu i zabeležite je
u zaglavlju. Sirovi snimak ima jednog vlasnika. Druge teme mogu da navedu
arhivski izvor.

Arhivski fajl ide u `<primary>/raw/clippings/<filename>.md`. Telo i detalji
izvora ostaju isti. Dodajte `triaged_to` i `triaged_at` samo kada su potrebni.
Zadržite svaku datiranu kopiju. Proverite `content_sha256` prema arhivama. Ne
ponavljajte iste tvrdnje u kanonskim stranicama.

Normalna QMD pretraga koristi kanonske stranice. Sirovi snimci i
`evidence-only` fajlovi su u opcionalnoj kolekciji `wiki-evidence`. Pretražujte
je samo kada zadatak traži dokaz izvora ili kada proveravate citat.

## Struktura kanonske stranice

Kanonske stranice pripadaju tematskim folderima `entities/`, `concepts/`,
`comparisons/`, `queries/` ili `hubs/`. `hubs/` prikazuje mapu teme i povezuje
kanonske stranice. Ne koristi se za sažetke članaka. Svaka tema ima ulaznu
stranicu `hubs/index.md`. Ponovo je koristite kada postoji. Ako dodate,
pomerite ili izmenite kanonsku stranicu ili ključni odnos, ažurirajte veze u
hub-u.

Validator proverava YAML i veze za `hubs/`. Za `entities/`, `concepts/`,
`comparisons/` i `queries/` proverava i zahteve u nastavku. Hub ne mora da ima
evidencioni registar tvrdnji.

### Obavezna zaglavlja i izvor

Zadržite postojeću taksonomiju i zaglavlje. Dodajte nedostajuća polja bez
brisanja sadašnjih metapodataka.

- `last_reviewed` je ISO datum.
- `review_after` je ISO datum ili pozitivan interval, na primer `90 days`.
- `sources` je neprazna YAML lista. Svaki izvor ima apsolutni HTTP(S) `url`,
  `published_at` datum ili `unknown` i ISO `retrieved_at` datum. Dodajte
  `provider` i `model` kada objašnjavaju kako je dokaz dobijen.

```yaml
title: "Naziv kanonske stranice"
last_reviewed: 2026-10-02
review_after: 90 days
sources:
  - url: https://example.com/documentation
    published_at: unknown
    retrieved_at: 2026-10-02
```

### Pitanje, tvrdnje i postupak

Stranica jasno navodi pitanje i definiše glavni pojam jednostavnim rečima.
Odvaja proverene činjenice, tvrdnje autora, zaključke i sukobe. Uz svaku
materijalnu tvrdnju stoji blizak citat i status. Navodi gde savet važi,
preduslove, ograničenja, poznate sukobe, otvorena pitanja i svežinu izvora.

Daje korisnu odluku ili uređene korake. Svaki postupak je `tested` ili
`untested`. Za `tested` navedite gde je testiran i koju verziju je test
obuhvatio. Povežite nekoliko srodnih pojmova.

### `Evidence ledger`

Dodajte naslov `## Evidence ledger` i tabelu sa kolonama tačno ovim redom:

```markdown
| Claim | Source / inspected passage | Published / updated | Retrieved | Scope / version | Status | Affected / updated page |
| --- | --- | --- | --- | --- | --- | --- |
```

Svaki red podataka ima URL izvora ili wiki vezu, datum objavljivanja ili
`unknown`, datum preuzimanja, opseg, status i izmenjenu stranicu. Kada je
potrebno, koristite `this page`. Status je jedan od `verified`, `author-claim`,
`inference`, `unverified` ili `conflict`.

Validator proverava strukturu tabele i vrednosti. Ne može da dokaže da izvor
zaista podržava tvrdnju.

## Pilot i kontrolna pitanja

Pre široke migracije proverite ove stranice prema šemi:

- `local-llm-capacity-planning`
- `tailscale-remote-local-model-access`
- `model-api-pricing-and-capability-claims`

Zatim evidentirajte upite koji proveravaju odluke, ne prisećanje članka:

1. Koliko RAM-a ili VRAM-a zahteva ovaj lokalni model?
2. Kako bezbedno dosežem lokalni model preko Tailscale-a?
3. Koji model API odgovara ovom zadatku i budžetu? Koje tvrdnje o ceni i
   sposobnosti imaju dokaz?

Podrazumevani rezultati treba da pokažu kanonske stranice. Za jedan upit
izaberite `wiki-evidence` i proverite da samo taj upit vraća sirove izvore.
