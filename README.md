## ASU Projekt - Porządkowanie plików

Sebastian Abramowski, 325142

---

### Opis

Skrypt służy do automatycznego porządkowania plików w katalogu głównym X poprzez przenoszenie lub kopiowanie plików z katalogów Y1, Y2, ... oraz opcjonalne czyszczenie zbędnych plików. Pozwala na:

- Przenoszenie lub kopiowanie plików z podanych katalogów do katalogu głównego
- Usuwanie duplikatów – zachowanie jednej kopii plików o tej samej zawartości
- Usuwanie zbędnych plików, takich jak puste pliki i pliki tymczasowe (.tmp, .log itp.)
- Standaryzację nazw plików – zamiana niedozwolonych znaków na `_`
- Zmianę uprawnień plików, jeśli są nietypowe lub niezgodne z konfiguracją
- Obsługę plików o tej samej nazwie lub tej samej zawartości – możliwość wyboru, który plik zachować (np. nowszy, starszy lub jakiś konkretny)

### Ogólny sposób użycia

```
python3 ./clean_files.py <katalog_X> <katalog_Y1> [<katalog_Y2> ...] -c <plik_konfiguracyjny> [opcje]
```

### Przykładowy sposób użycia

```bash
python3 ./clean_files.py ./X ./Y1 ./Y2 -c ./.clean_files.json --empty --temporary --problematic-characters --unusual-attributes --repeated-names --find-duplicate-content --move-files-to-main-dir
```

### Dostępne opcje

- `--empty`
- `--temporary`
- `--problematic-characters`
- `--unusual-attributes`
- `--repeated-names`
- `--find-duplicate-content`
- `--copy-files-to-main-dir`
- `--move-files-to-main-dir`

### Przykładowy plik konfiguracyjny

Program wczytuje plik konfiguracyjny podany jako argument `-c` podczas wywołania lub korzysta z domyślnej konfiguracji, która jest przedstawiona poniżej

```json
{
  "suggested_file_permissions": "rw-r--r--",
  "problematic_characters": ["'", ",", "*", "#", "@", ":", "$", "?"],
  "replacement_character": "_",
  "temporary_file_extensions": [".tmp", ".log"]
}
```

### Uwagi do zadania

Przydałaby się opcja, w której program zadaje mniej pytań - np. `--batch-processing`. W tym trybie, program podejmowałby pewne decyzje automatycznie, ograniczając interaktywność i przyśpieszając jego działanie.
