# Check Translations

A GitHub Action that automatically validates Minecraft mod translation files against basic technical errors and also keeps track of translation progress.

## Installation

Create a workflow file at e.g. `.github/workflows/check_translations.yml`:

```yaml
name: Check Translations

on:
  push:
    paths:
    - "src/main/resources/assets/your_mod_id/lang/**.json"
    - "src/main/resources/intentionally_untranslated.json"
    tags-ignore:
    - "**"
  pull_request:
    paths:
    - "src/main/resources/assets/your_mod_id/lang/**.json"
    - "src/main/resources/intentionally_untranslated.json"
  workflow_dispatch:

jobs:
  check_translations:
    runs-on: ubuntu-latest
    steps:

    - name: Checkout repository
      uses: actions/checkout@v5

    - name: Check translations
      uses: Wurst-Imperium/check-translations@v1
      with:
        lang-dir: "src/main/resources/assets/your_mod_id/lang"
```

Replace `your_mod_id` with your actual mod ID, or adjust paths as needed if your translation files are in a different directory (as is the case for Wurst).

Next, create an `intentionally_untranslated.json` file in your `src/main/resources` directory:

```json
{}
```

Add this to your `build.gradle` to exclude the `intentionally_untranslated.json` file from your mod jar:

```gradle
jar {
    // ...existing jar settings remain unchanged...

    // Add this line:
	exclude("intentionally_untranslated.json")
}
```
