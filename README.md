# 🎲 KritFailer

**Generátor následků kritických neúspěchů pro Dungeons & Dragons a další stolní RPG.**

KritFailer pomáhá proměnit critfail v konkrétní herní následek doplněný krátkým roleplay popisem. Hráči si výsledky losují sami, zatímco Dungeon Master určuje jejich obtížnost a řídí hru. Všichni používají společnou místnost a výsledky se mezi hráčem a DM sdílejí v reálném čase.

**[Spustit aplikaci →](https://leechesen.github.io/dnd-crit-fail-generator/)**

## Jak probíhá hra

1. **DM vytvoří místnost** a nastaví obtížnost následků. Místnost může chránit heslem.
2. **Hráči se připojí pod svým jménem.** Nemusí se registrovat ani zadávat e-mail.
3. Když někomu padne critfail, **vybere typ útoku, obranu nebo konkrétní dovednost**.
4. Aplikace vylosuje výsledek podle aktuálního nastavení DM a **zobrazí ho hráči i DM**.
5. Výsledek zůstane v historii, takže se k němu můžete během hry vrátit.

Obtížnost platí pro celou místnost, dokud ji DM nezmění. **Její název se hráčům nezobrazuje**, takže se následek dozvědí až po vygenerování výsledku.

## Co může DM a co hráč

| Funkce | Dungeon Master | Hráč |
| --- | --- | --- |
| Nastavení obtížnosti | Nastavuje a mění | Nastavení nevidí |
| Generování výsledků | Vytváří soukromý náhled | Losuje výsledek pro sebe |
| Odeslání výsledku hráči | Vybere příjemce a odešle | Přijímá vlastní výsledky |
| Historie | Vidí výsledky všech hráčů | Vidí své výsledky |
| Správa místnosti | Spravuje hráče a může místnost smazat | Připojí se nebo odejde |

DM může výsledek připravit i sám. Nejprve ho uvidí ve **vlastním náhledu** a teprve tlačítkem **Poslat výsledek** ho odešle vybranému hráči. Hody ostatních hráčů připravený náhled nepřepíšou.

## Útoky, obrana a dovednosti

Generátor nabízí následky pro útoky na blízko i na dálku, obranu a dovednosti rozdělené podle vlastností postavy. Každý výsledek obsahuje herní efekt a může ho doplnit **jeden roleplay popis** pro odehrání situace u stolu.

Pokud pro některou volbu nejsou při nastavené obtížnosti dostupné výsledky, její tlačítko je neaktivní.

## Vlastní výsledky z Excelu

Obsah generátoru vychází ze souboru **`crit_fails.xlsx`**. V listech **Útok**, **Obrana** a **Skill** lze upravovat herní efekty, roleplay popisy, obtížnosti i váhy jednotlivých výsledků. Vyšší váha znamená větší šanci na vylosování v rámci zvolené obtížnosti.

Po nahrání upraveného Excelu do větve `main` proběhne automatický převod dat a publikování aplikace. Otevřená aplikace kontroluje nové výsledky každou minutu a při návratu na její kartu. Dříve uložené výsledky si ponechají původní znění.

Pro roleplay se používá sloupec `roleplay_1`. Pokud je prázdný, aplikace použije `roleplay_2`; oba najednou nezobrazuje.

## Overlay pro streamování

KritFailer obsahuje samostatný **overlay pro OBS**. DM zkopíruje jeho adresu tlačítkem **Overlay** a vloží ji do OBS jako zdroj prohlížeče.

Vlastní hod hráče nebo výsledek odeslaný DM se na overlay zobrazí na **60 sekund** spolu se jménem hráče. Obtížnost zůstává skrytá a soukromé náhledy DM se na stream neposílají.

## Použití u stolu

Aplikace běží v prohlížeči na počítači i mobilu. Každý hráč může používat vlastní zařízení a DM má přehled o celé místnosti. Pro společnou hru a okamžité sdílení výsledků je potřeba připojení k internetu.
