# ADR 0004: Multilingual Support with Text-Based Language Files

## Status
Proposed

## Date
2025-12-21

## Context

The Ans fact-checking platform is designed for Amsterdam youth, a diverse demographic requiring multilingual support. Currently, all UI text is hardcoded in English with no internationalization (i18n) infrastructure in place.

### Requirements
1. Support multiple languages (initially Dutch + English)
2. Text-based language files (user preference)
3. Easy for translators to contribute
4. Type-safe integration with TypeScript frontend
5. Consistent developer experience across frontend and backend
6. Works with existing Docker development workflow
7. Minimal runtime overhead

### Current Stack
- **Frontend**: SvelteKit 2.8 + Svelte 5 + TypeScript
- **Backend**: FastAPI (Python) + SQLAlchemy

## Decision

We will implement multilingual support using **JSON-based translation files** with the following architecture:

### 1. Frontend: svelte-i18n with JSON Files

**Library**: `svelte-i18n` - mature, well-documented, SvelteKit compatible

**File Structure**:
```
frontend/
├── src/
│   ├── lib/
│   │   ├── i18n/
│   │   │   ├── index.ts           # i18n initialization
│   │   │   ├── locales/
│   │   │   │   ├── en.json        # English translations
│   │   │   │   ├── nl.json        # Dutch translations
│   │   │   │   └── index.ts       # Locale exports
│   │   │   └── types.ts           # TypeScript types for translations
```

**Translation File Format** (JSON):
```json
{
  "common": {
    "welcome": "Welcome to Ans",
    "login": "Log in",
    "register": "Register",
    "submit": "Submit",
    "cancel": "Cancel"
  },
  "auth": {
    "email": "Email address",
    "password": "Password",
    "loginTitle": "Sign in to your account",
    "registerTitle": "Create an account",
    "forgotPassword": "Forgot password?"
  },
  "submissions": {
    "title": "Your Submissions",
    "newSubmission": "Submit for fact-checking",
    "status": {
      "pending": "Pending review",
      "processing": "Processing",
      "completed": "Completed",
      "failed": "Failed"
    }
  },
  "errors": {
    "required": "This field is required",
    "invalidEmail": "Please enter a valid email",
    "networkError": "Network error. Please try again."
  }
}
```

**Usage in Components**:
```svelte
<script lang="ts">
  import { t } from '$lib/i18n';
</script>

<h1>{$t('common.welcome')}</h1>
<button>{$t('auth.login')}</button>
```

### 2. Backend: JSON Files with Python Loader

**File Structure**:
```
backend/
├── app/
│   ├── i18n/
│   │   ├── __init__.py            # i18n initialization
│   │   ├── loader.py              # Translation loader
│   │   ├── locales/
│   │   │   ├── en.json            # English translations
│   │   │   └── nl.json            # Dutch translations
│   │   └── types.py               # Type definitions
```

**Backend Translation Loader**:
```python
# app/i18n/loader.py
import json
from pathlib import Path
from functools import lru_cache
from typing import Any

LOCALES_DIR = Path(__file__).parent / "locales"
DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = {"en", "nl"}

@lru_cache(maxsize=10)
def load_translations(locale: str) -> dict[str, Any]:
    """Load translations for a locale with caching."""
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE

    file_path = LOCALES_DIR / f"{locale}.json"
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)

def get_translation(key: str, locale: str = DEFAULT_LOCALE, **kwargs: Any) -> str:
    """Get a translation by dot-notation key with optional interpolation."""
    translations = load_translations(locale)

    # Navigate nested keys: "errors.required" -> translations["errors"]["required"]
    value = translations
    for part in key.split("."):
        value = value.get(part, key)
        if not isinstance(value, dict) and part != key.split(".")[-1]:
            return key  # Key not found

    # Interpolate variables: "Hello {name}" with name="World" -> "Hello World"
    if isinstance(value, str) and kwargs:
        return value.format(**kwargs)

    return value if isinstance(value, str) else key
```

**API Error Messages**:
```python
# app/api/v1/endpoints/auth.py
from app.i18n import get_translation

@router.post("/login")
async def login(
    credentials: LoginRequest,
    accept_language: str = Header(default="en")
):
    locale = accept_language.split(",")[0].split("-")[0]  # "en-US,nl" -> "en"

    if not valid_credentials:
        raise HTTPException(
            status_code=401,
            detail=get_translation("errors.invalidCredentials", locale)
        )
```

### 3. Language Detection Strategy

**Priority Order**:
1. User preference (stored in database/localStorage)
2. `Accept-Language` HTTP header
3. URL parameter (`?lang=nl`)
4. Default to English

**Frontend Implementation**:
```typescript
// src/lib/i18n/index.ts
import { browser } from '$app/environment';
import { init, register, locale } from 'svelte-i18n';

register('en', () => import('./locales/en.json'));
register('nl', () => import('./locales/nl.json'));

function getInitialLocale(): string {
  if (browser) {
    // 1. Check localStorage for user preference
    const saved = localStorage.getItem('locale');
    if (saved && ['en', 'nl'].includes(saved)) return saved;

    // 2. Check browser language
    const browserLang = navigator.language.split('-')[0];
    if (['en', 'nl'].includes(browserLang)) return browserLang;
  }

  // 3. Default to English
  return 'en';
}

init({
  fallbackLocale: 'en',
  initialLocale: getInitialLocale()
});
```

### 4. User Language Preference

**Database Schema Extension**:
```sql
-- Add to users table
ALTER TABLE users ADD COLUMN preferred_language VARCHAR(5) DEFAULT 'en';
```

**User Settings Component**:
```svelte
<!-- LanguageSelector.svelte -->
<script lang="ts">
  import { locale, locales } from 'svelte-i18n';

  const languageNames: Record<string, string> = {
    en: 'English',
    nl: 'Nederlands'
  };

  function changeLanguage(newLocale: string) {
    locale.set(newLocale);
    localStorage.setItem('locale', newLocale);
    // Optionally sync to backend for authenticated users
  }
</script>

<select value={$locale} on:change={(e) => changeLanguage(e.target.value)}>
  {#each $locales as loc}
    <option value={loc}>{languageNames[loc]}</option>
  {/each}
</select>
```

### 5. Content Translation Strategy

**Static UI Text**: Translated via JSON files (this ADR)

**Dynamic Content** (user submissions, claims):
- Store in original language
- Future enhancement: integrate translation API for on-demand translation
- Out of scope for initial implementation

## Implementation Plan

### Phase 1: Frontend i18n Infrastructure
1. Install `svelte-i18n` package
2. Create `src/lib/i18n/` directory structure
3. Create initial `en.json` with all existing hardcoded strings
4. Create `nl.json` with Dutch translations
5. Initialize i18n in `+layout.svelte`
6. Add language selector component

### Phase 2: Component Migration
1. Migrate all hardcoded strings to translation keys
2. Update all components to use `$t()` function
3. Handle dynamic values with interpolation
4. Add RTL support placeholder for future languages

### Phase 3: Backend i18n
1. Create `app/i18n/` module
2. Create translation files for API messages
3. Update API endpoints to use translations
4. Add `Accept-Language` header handling

### Phase 4: Database & Persistence
1. Add `preferred_language` column to users table
2. Create Alembic migration
3. Update user schemas and endpoints
4. Sync language preference across sessions

## File Format Rationale

### Why JSON over alternatives?

| Format | Pros | Cons |
|--------|------|------|
| **JSON** | Universal, no dependencies, TypeScript-friendly | No comments, verbose for plurals |
| YAML | Human-readable, comments | Extra dependency, indentation sensitive |
| PO/MO | Industry standard, plural support | Binary MO files, tooling overhead |
| TypeScript | Full type safety | Requires compilation, not translator-friendly |
| ICU MessageFormat | Powerful pluralization | Complex syntax, learning curve |

**Decision**: JSON provides the best balance of simplicity, tooling support, and translator accessibility for our use case.

### Translation Key Conventions

1. **Namespace by feature**: `auth.`, `submissions.`, `common.`
2. **Use camelCase**: `loginTitle`, not `login_title` or `login-title`
3. **Be descriptive**: `submitForFactCheck`, not `submit`
4. **Group related keys**: All status values under `submissions.status.*`

### Interpolation Syntax

Use curly braces for variables:
```json
{
  "welcome": "Welcome, {name}!",
  "itemCount": "You have {count} items"
}
```

## Consequences

### Positive
- Clean separation of UI text from code
- Easy for translators (JSON is widely understood)
- Type-safe integration with TypeScript
- Lazy loading reduces initial bundle size
- Consistent pattern across frontend and backend
- Git-friendly diffs for translation changes
- No external service dependencies

### Negative
- Manual sync needed between en.json and nl.json
- No built-in plural forms (must use conditional keys)
- All developers must remember to use `$t()` for new text
- Initial migration effort to extract hardcoded strings

### Mitigations
- Add ESLint rule to detect hardcoded strings in components
- Create script to validate translation file parity
- Document key naming conventions
- Add translation coverage to CI checks

## Testing

### Frontend
```typescript
// Example test with i18n
import { render } from '@testing-library/svelte';
import { setupI18n } from '$lib/i18n/test-utils';

beforeEach(() => {
  setupI18n('en'); // Set test locale
});

test('shows translated login button', () => {
  const { getByText } = render(LoginPage);
  expect(getByText('Log in')).toBeInTheDocument();
});
```

### Backend
```python
def test_translation_loader():
    from app.i18n import get_translation

    assert get_translation("common.welcome", "en") == "Welcome to Ans"
    assert get_translation("common.welcome", "nl") == "Welkom bij Ans"
    assert get_translation("missing.key", "en") == "missing.key"  # Fallback
```

## Future Enhancements

1. **Additional Languages**: Add German, French, Arabic (with RTL support)
2. **Pluralization**: Implement ICU MessageFormat for complex plural rules
3. **Content Translation**: Integrate DeepL/Google Translate API
4. **Translation Management**: Consider Crowdin/Lokalise for community translations
5. **Date/Number Formatting**: Add Intl API wrappers for locale-aware formatting

## Alternatives Considered

### 1. Paraglide (Inlang)
- **Pros**: Zero runtime, compile-time type safety
- **Cons**: Newer ecosystem, different file format (.inlang)
- **Rejected**: Preference for established JSON format

### 2. typesafe-i18n
- **Pros**: Excellent TypeScript integration
- **Cons**: Uses TypeScript files, not pure text-based
- **Rejected**: User preference for text-based language files

### 3. Server-side only i18n
- **Pros**: Simpler architecture
- **Cons**: Requires page reload for language change, SSR complexity
- **Rejected**: Poor UX for language switching

### 4. gettext (.po files)
- **Pros**: Industry standard, powerful plural support
- **Cons**: Binary .mo files, additional tooling
- **Rejected**: More complex than needed for initial scope

## References

- [svelte-i18n Documentation](https://github.com/kaisermann/svelte-i18n)
- [SvelteKit i18n Guide](https://kit.svelte.dev/docs/i18n)
- [FastAPI Internationalization](https://fastapi.tiangolo.com/advanced/i18n/)
- [JSON-based i18n Best Practices](https://phrase.com/blog/posts/json-localization/)

## Related ADRs

- [ADR 0001: Docker Development Environment](./0001-docker-development-environment.md)
- [ADR 0003: Code Quality and Pre-Commit Workflow](./0003-code-quality-and-pre-commit-workflow.md)

## Author
System Architect (Claude)

## Revision History
- 2025-12-21: Initial proposal
