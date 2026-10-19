# KritFailer

Generátor critfailů s místnostmi pro DM a hráče. Web zachovává původní barevnost, karty, typografii a rozložení ovládání.

## Jak se hraje

1. DM vytvoří místnost a zvolí její obtížnost.
2. Hráč se připojí a klikne na typ útoku, obranu nebo dovednost, kde mu padl critfail.
3. Jeden vylosovaný výsledek se uloží a zobrazí hráči i DM. Zároveň se odešle do streamového overlaye.
4. DM může obtížnost kdykoliv změnit. Vlastní generování mu ukáže soukromý náhled; tlačítkem **Poslat výsledek** ho odešle vybranému hráči i do overlaye.

Obtížnost platí pro celou místnost do další změny DM. Její název vidí jen DM; hráčský panel, historie hráče ani overlay jej nezobrazují. Při souběžné změně nastavení se výsledek se starou verzí obtížnosti odmítne a hráč může kliknout znovu. Hráči vidí své výsledky, DM výsledky všech hráčů. Nové hráčské výsledky se dál ukládají do historie i během soukromého náhledu DM, ale jeho náhled nepřepíšou.

DM je vlastníkem místnosti podle anonymního účtu Firebase. Vrací se ve stejném prohlížeči, kde místnost vytvořil. Vymazání dat prohlížeče znamená ztrátu této anonymní identity. Odhlášení z místnosti samotný účet nemaže.

## Jednorázové nastavení

### Firebase

1. V projektu `ktit-fail-generator` otevři **Authentication → Sign-in method** a zapni **Anonymous**.
2. V **Realtime Database → Rules** vlož obsah `database.rules.json` a publikuj pravidla.
3. `firebase-config.js` obsahuje veřejnou konfiguraci nalezenou v původním repozitáři. Pokud byl klíč mezitím změněn, zkopíruj aktuální konfiguraci webové aplikace z **Project settings → Your apps**. Konfigurace Firebase patří do veřejného webu; přístup řídí databázová pravidla.

Anonymní přihlášení probíhá na pozadí, hráči nepotřebují vytvářet účet ani zadávat e-mail.

Nová verze používá větve `roomsV2` a `lobbyV2`. Po aktualizaci vytvoř novou místnost. Původní místnosti se automaticky nemigrují a nová pravidla k nim nepovolují přístup.

### GitHub Pages

1. Nahraj upravené soubory do repozitáře.
2. V **Settings → Pages → Build and deployment → Source** zvol **GitHub Actions**.
3. V **Actions** spusť workflow **Build and publish KritFailer**, případně udělej commit do `main`.

Workflow nejprve otestuje převod, sestaví JSON z aktuálního Excelu a publikuje hotový web. Při chybě se nová verze nenasadí a předchozí publikovaný web zůstane dostupný. Publikace probíhá přímo z jednoho workflow, takže nečeká na další workflow vyvolané automatickým commitem.

## Další aktualizace výsledků

Stačí nahradit **`crit_fails.xlsx`** v kořeni repozitáře a potvrdit commit do `main`. Převod a publikace proběhnou automaticky. Otevřená aplikace kontroluje nová data každou minutu a při návratu na její kartu. Výsledky již uložené v historii si ponechají původní znění.

JSON a jeho metadata jsou výstup sestavení. Při nasazení vznikají vždy z Excelu, ne z ručně upraveného JSONu v repozitáři.

### Formát Excelu

| List | Povinné sloupce |
| --- | --- |
| Útok | `attack_type`, `severity`, `effect` |
| Obrana | `severity`, `effect` |
| Skill | `skill`, `skill_category`, `severity`, `effect` |

V každém listu mohou být také `roleplay_1`, `roleplay_2` a `weight`. Váha je kladné číslo, při nevyplnění se použije 1. Větší váha znamená častější výběr **uvnitř obtížnosti zvolené DM**. Názvy obtížností se převezmou přímo z Excelu, takže je možné přidat další.

Každý výsledek zobrazí nejvýše jeden roleplay: `roleplay_1`, případně `roleplay_2`, pokud je první prázdný. Excel není třeba měnit. Stejné zobrazení platí i pro starší výsledky v historii.

Úplně prázdné řádky se přeskočí. Opakovaná hlavička uvnitř listu se přeskočí s upozorněním. Ostatní chyby uvádějí list a číslo řádku. Neplatná váha nebo neúplný výsledek zastaví sestavení před přepsáním výstupů.

Pokud pro dovednost a vybranou obtížnost nejsou výsledky, její tlačítko je neaktivní. Aktuální zdrojový Excel má 1619 výsledků; přepis obsahu jednotlivých critfailů je samostatná úprava.

## Overlay

DM má v horní liště tlačítko **Overlay**, které zkopíruje adresu pro Browser Source v OBS. Vlastní hod hráče nebo výsledek odeslaný DM se zobrazí na 60 sekund, bez názvu obtížnosti a s jednotným barevným motivem. Soukromý náhled DM se do overlaye neposílá. Při opětovném načtení overlay nepřehrává dávno prošlé výsledky.

## Lokální vývoj a ověření

Statický web je `index.html`, `app.js`, `critfail-core.mjs`, `firebase-client.mjs`, `firebase-config.js` a `overlay.html`. `app.py` je starší samostatná Streamlit varianta, nikoliv server tohoto webu.

```sh
pip install openpyxl
python excel_to_json.py
python -m http.server 8000
```

Základní kontroly:

```sh
python -m unittest discover -s tests -p 'test_*.py'
npm test
```

Testy skutečných pravidel Firebase a obou prohlížečových pohledů potřebují Node.js 22+, Javu 17+ a lokální emulátor:

```sh
npm ci
npx playwright install chromium
npx firebase-tools@13.35.1 emulators:exec --project demo-kritfailer --only database "npm run test:rules && npm run test:browser"
```

Emulátor používá demonstrační projekt. Testy nemění živou databázi. Losování běží v prohlížeči, oprávnění k nastavení, zápisu výsledků a vlastnictví místnosti ověřují databázová pravidla.
