# Devcisiongamepy

Kleines, textbasiertes Decision-Game inspiriert von Road 96. Du reist per Konsole durch mehrere Stationen, triffst Entscheidungen und beeinflusst Werte wie Gesundheit, Geld, Freiheit, Vertrauen, Moral und Fahndungsdruck.

## Spielstart

```bash
python game.py
```

## Regeln
- Jede Station präsentiert ein gewichtetes, zufälliges Event mit mehreren Optionen.
- Entscheidungen verändern deine Werte, können Flags setzen (z. B. "exposed") und Folgeeffekte auslösen.
- Reisestrapazen kosten dich nach jedem Event automatisch Ressourcen.
- Das Spiel endet, wenn du genug Freiheit sammelst, deine Ressourcen aufgebraucht sind oder die vorgegebenen Stationen vorbei sind.

## Erweiterungsideen
- Mehr Events mit Charakteren, die sich deine früheren Taten merken.
- Zusätzliche Ressourcen (z. B. Ausrüstung, Beziehungen zu Fraktionen).
- Persistente Weltkarten mit wiederkehrenden Orten.
