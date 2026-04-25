"""Planfile integration hook for TestQL — individual tickets per error."""

from __future__ import annotations

from typing import List


try:
    from planfile import Planfile, TicketSource
    PLANFILE_AVAILABLE = True
except ImportError:
    PLANFILE_AVAILABLE = False


def create_test_failure_ticket(errors: List[str], file_path: str = "") -> bool:
    """Create a single consolidated ticket in planfile for test failures."""
    if not PLANFILE_AVAILABLE:
        print("[TestQL] planfile package not installed. Cannot auto-create ticket.")
        return False

    if not errors:
        return False

    try:
        pf = Planfile.auto_discover(".")

        title = f"[TestQL] Błędy w {file_path}" if file_path else "[TestQL] Błędy automatycznego testowania"

        description = "Wykryto następujące błędy podczas uruchamiania testów:\n\n"
        for idx, err in enumerate(errors, 1):
            description += f"{idx}. {err}\n"

        description += "\nProszę zweryfikować i naprawić błędy."

        ticket = pf.create_ticket(
            name=title,
            description=description,
            priority="high",
            labels=["testql", "bug", "auto-generated"],
            source=TicketSource(tool="testql", context={"file": file_path}),
        )

        print(f"\n[TestQL] ✅ Utworzono zgłoszenie: {ticket.id} — '{ticket.name}'")
        return True
    except Exception as e:
        print(f"\n[TestQL] ⚠️ Nie udało się utworzyć zgłoszenia Planfile: {e}")
        return False


def create_individual_button_tickets(
    broken_buttons: list[dict],
    project_path: str = ".",
) -> int:
    """Create one planfile ticket per broken/dead button.

    Each entry in broken_buttons should be a dict with keys:
        url, selector, name, status, details
    Returns the number of tickets created.
    """
    if not PLANFILE_AVAILABLE:
        print("[TestQL] planfile package not installed. Cannot auto-create tickets.")
        return 0

    if not broken_buttons:
        return 0

    try:
        pf = Planfile.auto_discover(project_path)
    except Exception as e:
        print(f"[TestQL] ⚠️ Planfile init error: {e}")
        return 0

    created = 0
    for btn in broken_buttons:
        status = btn.get("status", "BROKEN")
        name = btn.get("name", "(brak nazwy)").strip() or "(brak nazwy)"
        selector = btn.get("selector", "?")
        url = btn.get("url", "/")
        details = btn.get("details", "")

        icon = "☠️" if status == "DEAD" else "💥"
        title = f"[TestQL] {icon} {status} button: {name} na {url}"

        description = (
            f"## Opis\n"
            f"Automatyczny audyt UI (Chaos Monkey) wykrył niedziałający przycisk.\n\n"
            f"- **Strona:** `{url}`\n"
            f"- **Nazwa przycisku:** {name}\n"
            f"- **Selektor CSS:** `{selector}`\n"
            f"- **Status:** {status}\n"
            f"- **Szczegóły:** {details}\n\n"
            f"## Kryteria akceptacji\n"
            f"- [ ] Przycisk `{selector}` na stronie `{url}` reaguje na kliknięcie.\n"
            f"- [ ] Brak błędów JS w konsoli po kliknięciu.\n"
            f"- [ ] Ponowny audyt (`gui_auditor.py`) klasyfikuje przycisk jako OK.\n"
        )

        try:
            ticket = pf.create_ticket(
                name=title,
                description=description,
                priority="high" if status == "BROKEN" else "normal",
                labels=["testql", "ui-audit", f"status:{status.lower()}", "auto-generated"],
                source=TicketSource(
                    tool="testql-dom-audit",
                    context={"url": url, "selector": selector, "status": status},
                ),
            )
            print(f"  🎫 {ticket.id}: {title[:60]}")
            created += 1
        except Exception as e:
            print(f"  ⚠️ Ticket creation failed for '{name}': {e}")

    print(f"\n[TestQL] Utworzono {created}/{len(broken_buttons)} biletów w Planfile.")
    return created
