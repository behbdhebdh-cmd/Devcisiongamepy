"""
Textbasiertes Entscheidungs-Spiel inspiriert von Road 96.
Spieler reisen durch zufällige Stationen, treffen Entscheidungen und
steuern ihre Werte Richtung Freiheit.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List


@dataclass
class Player:
    """Spielerstatus mit einfachen Ressourcen."""

    health: int = 10
    money: int = 20
    freedom: int = 0
    trust: int = 5
    morale: int = 5

    def apply_effects(self, effects: Dict[str, int]) -> None:
        for key, change in effects.items():
            if hasattr(self, key):
                current = getattr(self, key)
                setattr(self, key, current + change)

    def is_alive(self) -> bool:
        return self.health > 0 and self.money > -10 and self.morale > 0


@dataclass
class Option:
    text: str
    effects: Dict[str, int]
    outcome: str
    follow_up: Callable[[Player], None] | None = None

    def execute(self, player: Player) -> None:
        player.apply_effects(self.effects)
        if self.follow_up:
            self.follow_up(player)


@dataclass
class Event:
    title: str
    description: str
    options: List[Option]
    tag: str = field(default_factory=str)

    def display(self) -> None:
        print(f"\n--- {self.title} ---")
        print(self.description)
        for idx, option in enumerate(self.options, start=1):
            print(f"  {idx}. {option.text}")

    def choose(self) -> Option:
        while True:
            choice = input("Deine Wahl: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(self.options):
                    return self.options[idx]
            print("Ungültige Eingabe, bitte erneut wählen.")


class Journey:
    def __init__(self, max_stops: int = 6) -> None:
        self.max_stops = max_stops
        self.player = Player()
        self.events = self._build_events()
        self.visited_tags: set[str] = set()

    def _random_drift(self, value: int) -> int:
        return random.randint(-value, value)

    def _build_events(self) -> List[Event]:
        def convoy_follow_up(player: Player) -> None:
            drift = self._random_drift(2)
            player.apply_effects({"freedom": 1 + drift, "trust": -1})

        def border_follow_up(player: Player) -> None:
            if random.random() < 0.3:
                player.apply_effects({"health": -3, "trust": -2})
                print("Wache misstraut dir, es eskaliert kurz.")
            else:
                player.apply_effects({"freedom": 2, "trust": 1})
                print("Du wirkst überzeugend und kommst ein Stück voran.")

        return [
            Event(
                title="Verlassene Tankstelle",
                description=(
                    "Ein Auto steht verlassen, der Besitzer ist nirgends zu sehen."
                    " Du brauchst Vorräte, aber jede Wahl hat ihren Preis."
                ),
                options=[
                    Option(
                        text="Auto durchsuchen",
                        effects={"money": +10, "trust": -1, "morale": -1},
                        outcome="Du findest Bargeld, aber fühlst dich mies dabei.",
                    ),
                    Option(
                        text="Weiterziehen, aber Benzin abzweigen",
                        effects={"money": +5, "trust": -2, "health": -1},
                        outcome="Du zapfst etwas Sprit, verbrennst dich leicht.",
                    ),
                    Option(
                        text="Nichts anrühren",
                        effects={"morale": +1, "trust": +1},
                        outcome="Du gehst mit ruhigem Gewissen weiter.",
                    ),
                ],
                tag="fuel",
            ),
            Event(
                title="Mitfahrgelegenheit",
                description=(
                    "Ein alter Lieferwagen hält an. Der Fahrer bietet dir eine Fahrt an,"
                    " wirkt aber nervös."
                ),
                options=[
                    Option(
                        text="Einsteigen und Smalltalk",
                        effects={"freedom": +2, "trust": +1},
                        outcome="Die Fahrt verläuft ruhig, du gewinnst Kilometer.",
                    ),
                    Option(
                        text="Einsteigen, aber wachsam bleiben",
                        effects={"freedom": +2, "trust": -1},
                        outcome="Du spürst Gefahr, hältst aber Distanz zum Fahrer.",
                    ),
                    Option(
                        text="Ablehnen",
                        effects={"freedom": 0, "morale": +1},
                        outcome="Du gehst zu Fuß weiter und fühlst dich sicherer.",
                    ),
                ],
                tag="ride",
            ),
            Event(
                title="Straßensperre",
                description=(
                    "Soldaten kontrollieren alle Papiere. Du kannst versuchen,"
                    " zu überzeugen, dich zu verstecken oder zu spenden."
                ),
                options=[
                    Option(
                        text="Überzeugen mit ehrlicher Geschichte",
                        effects={"trust": +1, "freedom": +1, "money": -3},
                        outcome="Der Soldat hört zu, du kommst durch, verlierst aber Zeit und Geld.",
                    ),
                    Option(
                        text="Schmieren mit Geld",
                        effects={"money": -8, "freedom": +3, "morale": -1},
                        outcome="Das Bestechungsgeld wirkt, aber es nagt an dir.",
                    ),
                    Option(
                        text="Waldpfad nehmen",
                        effects={"health": -2, "freedom": +2, "trust": -1},
                        outcome="Stolpern, Dornen, aber du umgehst die Kontrolle.",
                    ),
                ],
                tag="checkpoint",
            ),
            Event(
                title="Konvoi der Rebellen",
                description=(
                    "Eine Gruppe Rebellen bietet dir Schutz an, fordert aber Loyalität."
                    " Du musst Stellung beziehen."
                ),
                options=[
                    Option(
                        text="Mitziehen und Informationen teilen",
                        effects={"trust": +2, "freedom": +1},
                        outcome="Die Rebellen akzeptieren dich, du lernst Geheimrouten.",
                        follow_up=convoy_follow_up,
                    ),
                    Option(
                        text="Mitziehen, aber schweigen",
                        effects={"trust": -1, "freedom": +1},
                        outcome="Du hältst dich bedeckt, die Gruppe bleibt misstrauisch.",
                        follow_up=convoy_follow_up,
                    ),
                    Option(
                        text="Alleine weiter",
                        effects={"morale": +1},
                        outcome="Du verzichtest auf Unterstützung, fühlst dich aber frei."
                    ),
                ],
                tag="rebels",
            ),
            Event(
                title="Grenzfluss bei Nacht",
                description=(
                    "Der letzte Fluss vor der Grenze. Du kannst schwimmen, ein Boot suchen"
                    " oder dich als Händler ausgeben."
                ),
                options=[
                    Option(
                        text="Schwimmen",
                        effects={"health": -3, "freedom": +3},
                        outcome="Das Wasser ist kalt, aber du erreichst das andere Ufer.",
                    ),
                    Option(
                        text="Boot organisieren",
                        effects={"money": -5, "freedom": +2, "trust": +1},
                        outcome="Ein Fischer bringt dich gegen Bezahlung hinüber.",
                    ),
                    Option(
                        text="Als Händler durchwinken lassen",
                        effects={"trust": -1, "freedom": +2},
                        outcome="Deine Lüge hält, doch du verlierst etwas Ansehen.",
                        follow_up=border_follow_up,
                    ),
                ],
                tag="river",
            ),
        ]

    def _pick_event(self) -> Event:
        available = [event for event in self.events if event.tag not in self.visited_tags]
        if not available:
            self.visited_tags.clear()
            available = self.events
        event = random.choice(available)
        self.visited_tags.add(event.tag)
        return event

    def _status_bar(self) -> str:
        return (
            f"Gesundheit: {self.player.health} | Geld: {self.player.money} | "
            f"Freiheit: {self.player.freedom} | Vertrauen: {self.player.trust} | "
            f"Moral: {self.player.morale}"
        )

    def _check_end(self, step: int) -> bool:
        if not self.player.is_alive():
            print("\nDu brichst zusammen. Deine Reise endet hier.")
            return True
        if self.player.freedom >= 12:
            print("\nDu erreichst die Grenze rechtzeitig und findest ein neues Leben!")
            return True
        if step >= self.max_stops:
            print("\nDie Zeit läuft ab. Du erreichst einen sicheren Unterschlupf, aber die Grenze bleibt fern.")
            return True
        return False

    def _ending(self) -> None:
        if self.player.freedom >= 12:
            if self.player.trust >= 8:
                print("Ende: Netzwerk der Verbündeten hilft dir beim Neustart.")
            elif self.player.morale < 3:
                print("Ende: Du bist frei, aber innerlich zerrissen von zweifelhaften Entscheidungen.")
            else:
                print("Ende: Du bist frei und lernst, neu anzufangen.")
        elif not self.player.is_alive():
            print("Ende: Körper und Geist geben auf, die Reise war zu hart.")
        else:
            print("Ende: Du tauchst unter. Freiheit bleibt Hoffnung für morgen.")

    def play(self) -> None:
        print("Willkommen zu 'Route 97' - ein Road-Trip voller Entscheidungen.\n")
        for step in range(1, self.max_stops + 1):
            print(f"Station {step} | {self._status_bar()}")
            event = self._pick_event()
            event.display()
            option = event.choose()
            option.execute(self.player)
            print(option.outcome)
            print(f"Neuer Status -> {self._status_bar()}")
            if self._check_end(step):
                break
        self._ending()


def main() -> None:
    random.seed()
    Journey().play()


if __name__ == "__main__":
    main()
