# SCENARIO: Logowanie użytkownika
TYPE: gui
LANG: pl
VERSION: 1.0

1. Otwórz `/login`
2. Wprowadź "admin@example.com" do pola email
3. Wprowadź "password123" do pola hasło
4. Kliknij `[data-testid='submit']`
5. Sprawdź że widoczny jest element `[data-testid='dashboard']`
6. Sprawdź że URL zawiera "/dashboard"
