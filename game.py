"""
Textbasiertes Entscheidungs-Spiel inspiriert von Road 96.
Spieler reisen durch zufällige Stationen, treffen Entscheidungen und
steuern ihre Werte Richtung Freiheit. Fokus auf Konsequenzen und Flags.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class Player:
    """Spielerstatus mit einfachen Ressourcen."""

    health: int = 10
    money: int = 20
    freedom: int = 0
    trust: int = 5
    morale: int = 5
    heat: int = 0
    flags: Dict[str, bool] = field(default_factory=dict)

    def apply_effects(self, effects: Dict[str, int]) -> None:
        for key, change in effects.items():
            if hasattr(self, key):
                current = getattr(self, key)
                setattr(self, key, current + change)
        self._clamp()

    def is_alive(self) -> bool:
        return self.health > 0 and self.money >= 0 and self.morale > 0 and self.heat < 10

    def _clamp(self) -> None:
        self.health = max(0, min(10, self.health))
        self.trust = max(0, min(10, self.trust))
        self.morale = max(0, min(10, self.morale))
        self.heat = max(0, min(10, self.heat))
        self.money = max(0, self.money)


@dataclass
class Outcome:
    text: str
    effects: Dict[str, int]
    follow_up: Callable[[Player, random.Random], str] | None = None
    weight: int = 1


@dataclass
class Option:
    text: str
    outcomes: List[Outcome]

    def execute(self, player: Player, rng: random.Random) -> str:
        outcome = self._choose_outcome(rng)
        player.apply_effects(outcome.effects)
        result_text = outcome.text
        if outcome.follow_up:
            result_text += "\n" + outcome.follow_up(player, rng)
        return result_text

    def _choose_outcome(self, rng: random.Random) -> Outcome:
        weights = [max(1, getattr(o, "weight", 1)) for o in self.outcomes]
        total = sum(weights)
        pick = rng.randint(1, total)
        cumulative = 0
        for outcome, weight in zip(self.outcomes, weights):
            cumulative += weight
            if pick <= cumulative:
                return outcome
        return self.outcomes[-1]


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
    def __init__(self, max_stops: int = 6, seed: int | None = None) -> None:
        self.max_stops = max_stops
        self.player = Player()
        self.rng = random.Random(seed)
        self.events = self._build_events()
        self.visited_tags: set[str] = set()

    def _random_drift(self, value: int) -> int:
        return self.rng.randint(-value, value)

    def _build_events(self) -> List[Event]:
        def flag_follow_up(flag: str, text: str) -> Callable[[Player, random.Random], str]:
            def inner(player: Player, _: random.Random) -> str:
                player.flags[flag] = True
                return text

            return inner

        def convoy_follow_up(player: Player, rng: random.Random) -> str:
            drift = self._random_drift(2)
            player.apply_effects({"freedom": 1 + drift, "trust": -1})
            player.flags["helped_rebels"] = True
            return "Der Konvoi teilt geheime Routen, aber erwartet später Loyalität."

        def border_follow_up(player: Player, rng: random.Random) -> str:
            if rng.random() < 0.3:
                player.apply_effects({"health": -3, "trust": -2, "heat": +2})
                player.flags["exposed"] = True
                return "Wache misstraut dir, ein Scharmützel lässt deine Deckung fallen."
            player.apply_effects({"freedom": 2, "trust": 1})
            return "Du wirkst überzeugend und kommst ein gutes Stück voran."

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
                        outcomes=[
                            Outcome(
                                text="Du findest Bargeld zwischen den Sitzen.",
                                effects={"money": +10, "morale": -1},
                                weight=6,
                            ),
                            Outcome(
                                text="Eine Kamera erwischt dich, jemand ruft die Wache.",
                                effects={"money": +5, "morale": -1, "trust": -1, "heat": +1},
                                follow_up=flag_follow_up("exposed", "Du merkst, dass du nun gesucht werden könntest."),
                                weight=3,
                            ),
                            Outcome(
                                text="Alarmanlage geht los, du fliehst kopflos.",
                                effects={"freedom": -1, "heat": +2, "trust": -2},
                                follow_up=flag_follow_up("exposed", "Ein Zeuge beschrieb dich genau."),
                                weight=1,
                            ),
                        ],
                    ),
                    Option(
                        text="Weiterziehen, aber Benzin abzweigen",
                        outcomes=[
                            Outcome(
                                text="Du zapfst etwas Sprit, verbrennst dich leicht.",
                                effects={"money": +5, "trust": -2, "health": -1},
                                weight=5,
                            ),
                            Outcome(
                                text="Der Tank war fast leer. Kaum Gewinn, nur Stress.",
                                effects={"money": +2, "trust": -1, "morale": -1},
                                weight=3,
                            ),
                            Outcome(
                                text="Du wirst beobachtet, als du den Kanister füllst.",
                                effects={"money": +5, "heat": +2, "trust": -2},
                                follow_up=flag_follow_up("exposed", "Gerüchte verbreiten sich über einen verdächtigen Reisenden."),
                                weight=2,
                            ),
                        ],
                    ),
                    Option(
                        text="Nichts anrühren",
                        outcomes=[
                            Outcome(
                                text="Du gehst mit ruhigem Gewissen weiter.",
                                effects={"morale": +1, "trust": +1},
                                weight=8,
                            ),
                            Outcome(
                                text="Du zögerst zu lange, eine Patrouille zwingt dich zum Weitergehen.",
                                effects={"heat": +1, "freedom": -1, "trust": +1},
                                weight=2,
                            ),
                        ],
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
                        outcomes=[
                            Outcome(
                                text="Die Fahrt verläuft ruhig, du gewinnst Kilometer.",
                                effects={"freedom": +2, "trust": +1},
                                weight=7,
                            ),
                            Outcome(
                                text="Der Fahrer fragt aus, du gibst zu viel preis.",
                                effects={"freedom": +2, "trust": -1, "heat": +1},
                                weight=3,
                            ),
                        ],
                    ),
                    Option(
                        text="Einsteigen, aber wachsam bleiben",
                        outcomes=[
                            Outcome(
                                text="Du spürst Gefahr, hältst aber Distanz zum Fahrer.",
                                effects={"freedom": +2, "trust": -1},
                                weight=6,
                            ),
                            Outcome(
                                text="Du findest eine vergessene Brieftasche.",
                                effects={"freedom": +2, "money": +6, "trust": -2, "morale": -1},
                                weight=2,
                            ),
                            Outcome(
                                text="Ihr werdet an der Kontrolle angehalten; deine Vorsicht rettet dich.",
                                effects={"freedom": +1, "heat": +1},
                                follow_up=flag_follow_up("exposed", "Soldaten notieren dein Gesicht."),
                                weight=2,
                            ),
                        ],
                    ),
                    Option(
                        text="Ablehnen",
                        outcomes=[
                            Outcome(
                                text="Du gehst zu Fuß weiter und fühlst dich sicherer.",
                                effects={"morale": +1},
                                weight=7,
                            ),
                            Outcome(
                                text="Das Wetter schlägt um, du wirst durchnässt.",
                                effects={"health": -1, "freedom": -1},
                                weight=3,
                            ),
                        ],
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
                        outcomes=[
                            Outcome(
                                text="Der Soldat hört zu, du kommst durch, verlierst aber Zeit und Geld.",
                                effects={"trust": +1, "freedom": +1, "money": -3},
                                weight=7,
                            ),
                            Outcome(
                                text="Er glaubt dir nicht, ein kurzer Streit eskaliert.",
                                effects={"health": -2, "heat": +2, "trust": -1},
                                follow_up=flag_follow_up("exposed", "Dein Name landet auf einer Liste."),
                                weight=3,
                            ),
                        ],
                    ),
                    Option(
                        text="Schmieren mit Geld",
                        outcomes=[
                            Outcome(
                                text="Das Bestechungsgeld wirkt, aber es nagt an dir.",
                                effects={"money": -8, "freedom": +3, "morale": -1},
                                weight=6,
                            ),
                            Outcome(
                                text="Der Offizier nimmt dein Geld und will mehr.",
                                effects={"money": -10, "heat": +1, "freedom": +2, "morale": -2},
                                weight=4,
                            ),
                        ],
                    ),
                    Option(
                        text="Waldpfad nehmen",
                        outcomes=[
                            Outcome(
                                text="Stolpern, Dornen, aber du umgehst die Kontrolle.",
                                effects={"health": -2, "freedom": +2, "trust": -1},
                                weight=7,
                            ),
                            Outcome(
                                text="Du triffst einen Schmuggler, der dir kürzere Wege zeigt.",
                                effects={"health": -1, "freedom": +3, "trust": +1},
                                follow_up=flag_follow_up("forest_contact", "Er bietet später vielleicht Hilfe an."),
                                weight=3,
                            ),
                        ],
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
                        outcomes=[
                            Outcome(
                                text="Die Rebellen akzeptieren dich, du lernst Geheimrouten.",
                                effects={"trust": +2, "freedom": +1},
                                follow_up=convoy_follow_up,
                                weight=7,
                            ),
                            Outcome(
                                text="Du teilst zu viel, jemand zweifelt deine Loyalität an.",
                                effects={"trust": -1, "freedom": +1, "heat": +1},
                                follow_up=convoy_follow_up,
                                weight=3,
                            ),
                        ],
                    ),
                    Option(
                        text="Mitziehen, aber schweigen",
                        outcomes=[
                            Outcome(
                                text="Du hältst dich bedeckt, die Gruppe bleibt misstrauisch.",
                                effects={"trust": -1, "freedom": +1},
                                follow_up=convoy_follow_up,
                                weight=6,
                            ),
                            Outcome(
                                text="Du wirkst kühl, aber ein Rebell respektiert deine Vorsicht.",
                                effects={"trust": +1, "freedom": +1},
                                follow_up=convoy_follow_up,
                                weight=4,
                            ),
                        ],
                    ),
                    Option(
                        text="Alleine weiter",
                        outcomes=[
                            Outcome(
                                text="Du verzichtest auf Unterstützung, fühlst dich aber frei.",
                                effects={"morale": +1},
                                weight=8,
                            ),
                            Outcome(
                                text="Du verpasst ihre sichere Route und verlierst Zeit.",
                                effects={"freedom": -1, "morale": +1},
                                weight=2,
                            ),
                        ],
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
                        outcomes=[
                            Outcome(
                                text="Das Wasser ist kalt, aber du erreichst das andere Ufer.",
                                effects={"health": -3, "freedom": +3},
                                weight=7,
                            ),
                            Outcome(
                                text="Starker Strom zieht dich ab, du verlierst Kraft.",
                                effects={"health": -4, "freedom": +2, "heat": +1},
                                weight=3,
                            ),
                        ],
                    ),
                    Option(
                        text="Boot organisieren",
                        outcomes=[
                            Outcome(
                                text="Ein Fischer bringt dich gegen Bezahlung hinüber.",
                                effects={"money": -5, "freedom": +2, "trust": +1},
                                weight=7,
                            ),
                            Outcome(
                                text="Du verhandelst hart, der Preis steigt.",
                                effects={"money": -7, "freedom": +2, "trust": 0},
                                weight=3,
                            ),
                        ],
                    ),
                    Option(
                        text="Als Händler durchwinken lassen",
                        outcomes=[
                            Outcome(
                                text="Deine Lüge hält, doch du verlierst etwas Ansehen.",
                                effects={"trust": -1, "freedom": +2},
                                follow_up=border_follow_up,
                                weight=7,
                            ),
                            Outcome(
                                text="Du vergisst eine überzeugende Geschichte, jemand wird misstrauisch.",
                                effects={"trust": -2, "freedom": +1, "heat": +1},
                                follow_up=border_follow_up,
                                weight=3,
                            ),
                        ],
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
        weights = [self._event_weight(event) for event in available]
        choice_total = sum(weights)
        pick = self.rng.randint(1, choice_total)
        cumulative = 0
        for event, weight in zip(available, weights):
            cumulative += weight
            if pick <= cumulative:
                self.visited_tags.add(event.tag)
                return event
        chosen = available[-1]
        self.visited_tags.add(chosen.tag)
        return chosen

    def _event_weight(self, event: Event) -> int:
        weight = 1
        if event.tag == "checkpoint" and (self.player.flags.get("exposed") or self.player.heat >= 5):
            weight += 3
        if event.tag == "river" and self.player.freedom >= 8:
            weight += 2
        if event.tag == "fuel" and self.player.money <= 5:
            weight += 2
        if event.tag == "rebels" and self.player.flags.get("helped_rebels"):
            weight += 1
        return weight

    def _status_bar(self) -> str:
        return (
            f"Gesundheit: {self.player.health} | Geld: {self.player.money} | "
            f"Freiheit: {self.player.freedom} | Vertrauen: {self.player.trust} | "
            f"Moral: {self.player.morale} | Fahndungsdruck: {self.player.heat}"
        )

    def _check_end(self, step: int) -> Optional[str]:
        if not self.player.is_alive():
            return "collapse"
        if self.player.freedom >= 12:
            return "escaped"
        if step >= self.max_stops:
            return "time"
        return None

    def _ending(self, reason: Optional[str]) -> None:
        if reason is None:
            return
        print()
        if reason == "escaped":
            print("Du erreichst die Grenze rechtzeitig und findest ein neues Leben!")
            if self.player.trust >= 8:
                print("Ende: Netzwerk der Verbündeten hilft dir beim Neustart.")
            elif self.player.morale < 3:
                print("Ende: Du bist frei, aber innerlich zerrissen von zweifelhaften Entscheidungen.")
            else:
                print("Ende: Du bist frei und lernst, neu anzufangen.")
        elif reason == "collapse":
            print("Du brichst zusammen. Deine Reise endet hier.")
            if self.player.heat >= 8:
                print("Ende: Die Verfolger holen dich ein, während du schwächelst.")
            else:
                print("Ende: Körper und Geist geben auf, die Reise war zu hart.")
        elif reason == "time":
            print("Die Zeit läuft ab. Du erreichst einen Unterschlupf, aber die Grenze bleibt fern.")
            if self.player.flags.get("helped_rebels"):
                print("Ende: Rebellen verstecken dich, Freiheit bleibt Zukunftsmusik.")
            else:
                print("Ende: Du tauchst unter. Freiheit bleibt Hoffnung für morgen.")

    def _travel_tick(self) -> str:
        fatigue = self.rng.choice([0, 1])
        effects: Dict[str, int] = {"money": -1 if self.player.money > 0 else 0}
        if fatigue:
            effects["health"] = -1
        if self.player.flags.get("exposed") and self.rng.random() < 0.5:
            effects["heat"] = effects.get("heat", 0) + 1
        self.player.apply_effects(effects)
        parts = [f"{key}{'+' if val >=0 else ''}{val}" for key, val in effects.items() if val != 0]
        if not parts:
            return "Reisestrapazen bleiben gering."
        return "Reisestrapazen fordern Tribut: " + ", ".join(parts)

    def play(self) -> None:
        print("Willkommen zu 'Route 97' - ein Road-Trip voller Entscheidungen.\n")
        end_reason: Optional[str] = None
        for step in range(1, self.max_stops + 1):
            print(f"Station {step} | {self._status_bar()}")
            event = self._pick_event()
            event.display()
            option = event.choose()
            result_text = option.execute(self.player, self.rng)
            print(result_text)
            tick_text = self._travel_tick()
            print(tick_text)
            print(f"Neuer Status -> {self._status_bar()}")
            end_reason = self._check_end(step)
            if end_reason:
                break
        self._ending(end_reason)


def main() -> None:
    Journey().play()


if __name__ == "__main__":
    main()
