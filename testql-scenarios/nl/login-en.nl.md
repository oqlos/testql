# SCENARIO: User login
TYPE: gui
LANG: en
VERSION: 1.0

1. Open `/login`
2. Type "admin@example.com" into `[name='email']`
3. Type "password123" into `[name='password']`
4. Click `[data-testid='submit']`
5. Check that URL contains "/dashboard"
