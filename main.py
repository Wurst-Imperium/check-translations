import json
import os
from pathlib import Path
from argparse import ArgumentParser


def read_json_file(path: Path) -> dict:
	"""Read a JSON data file."""
	return json.loads(path.read_text(encoding="utf-8"))


def gh_summary(summary: str):
	"""Add a line to the GitHub Actions summary for the current step."""
	print(summary)
	if "GITHUB_STEP_SUMMARY" in os.environ:
		with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary_file:
			print(summary, file=summary_file)


def show_translation_stats(en_us: dict, translations: dict):
	"""Render a table of the current translation progress for each language."""
	gh_summary("| Language | Translated | % |")
	gh_summary("| --- | --- | --- |")
	gh_summary(f"| en_us | {len(en_us)} | 100.00% |")
	for lang, data in translations.items():
		gh_summary(f"| {lang} | {len(data)} | {len(data) / len(en_us) * 100:.2f}% |")
	gh_summary("")


def check_extra_keys(en_us: dict, translations: dict):
	"""Check if any translation files contain keys that don't exist in the original."""
	extra_keys_found = False
	for lang, data in translations.items():
		extra_keys = set(data.keys()) - set(en_us.keys())
		if extra_keys:
			extra_keys_found = True
			gh_summary(
				f"⚠ {lang}.json contains translations that don't exist in en_us.json ({len(extra_keys)} found):"
			)
			for key in extra_keys:
				gh_summary(f"- {key}")
	if extra_keys_found:
		raise Exception("Found extra keys in one or more translation files")
	gh_summary("✅ No extra keys found")


def check_untranslated_strings(en_us: dict, translations: dict):
	"""Check if any translation files contain untranslated strings."""
	untranslated_strings_found = False
	intentionally_untranslated = read_json_file(
		Path("src") / "main" / "resources" / "intentionally_untranslated.json"
	)

	for lang, data in translations.items():
		untranslated_strings = set()
		for key, value in data.items():
			if value == en_us[key]:
				if lang in intentionally_untranslated and key in intentionally_untranslated[lang]:
					continue
				untranslated_strings.add(key)
		if untranslated_strings:
			untranslated_strings_found = True
			gh_summary(
				f"⚠ {lang}.json contains strings that are identical to en_us.json ({len(untranslated_strings)} found):"
			)
			for key in untranslated_strings:
				gh_summary(f"- {key}: {en_us[key]}")
			gh_summary(
				"\nIf this is intentional, add the affected key(s) to intentionally_untranslated.json:"
			)
			gh_summary("```json")
			gh_summary(f'  "{lang}": [')
			for key in untranslated_strings:
				gh_summary(f'    "{key}"')
			gh_summary("  ]")
			gh_summary("```")

	if untranslated_strings_found:
		raise Exception("Found untranslated strings in one or more translation files")
	gh_summary("✅ No accidentally untranslated strings found")


def check_order_of_strings(en_us: dict, translations: dict):
	"""Check if the strings in each translation file are in the same order as in en_us.json."""
	for lang, data in translations.items():
		en_us_keys_present_in_translation = [key for key in en_us.keys() if key in data.keys()]
		translation_keys_present_in_en_us = [key for key in data.keys() if key in en_us.keys()]
		if en_us_keys_present_in_translation != translation_keys_present_in_en_us:
			raise Exception(f"⚠ The order of strings in {lang}.json is different from en_us.json")
	gh_summary("✅ The order of strings in each translation file matches en_us.json")


def check_known_issues(en_us: dict, translations: dict):
	"""Check if any translation files contain known issues."""
	issues_found = False

	# Typos
	known_typos = {
		"Anchoraura": "AnchorAura",
		"Autobuild": "AutoBuild",
		"Clickaura": "ClickAura",
		"KillAura": "Killaura",
		"LegitNuker": "Nuker",
		"LegitKillaura": "KillauraLegit",
		"Nofall": "NoFall",
		"Triggerbot": "TriggerBot",
	}
	for lang, data in translations.items():
		for key, value in data.items():
			for typo, correct in known_typos.items():
				if typo in value:
					issues_found = True
					gh_summary(
						f"⚠ In {lang}.json string {key}, the word '{correct}' is incorrectly translated as '{typo}':"
					)
					gh_summary("```json")
					gh_summary(f'  "{key}": "{value}"')
					gh_summary("```")

	# Difficult strings
	for lang, data in translations.items():
		# Boatfly
		boatfly_key = "description.wurst.hack.boatfly"
		if boatfly_key in data and "shift" in data[boatfly_key].lower():
			issues_found = True
			gh_summary(
				f"⚠ In {lang}.json, the translation for {boatfly_key} incorrectly suggests using the shift (sneak) key instead of ctrl (sprint) to descend"
			)
		# Radar
		radar_key = "description.wurst.hack.radar"
		if radar_key in data and (
			"§cred§r" in data[radar_key]
			# Not checking orange because it appears in the French translation
			or "§agreen§r" in data[radar_key]
			or "§7gray§r" in data[radar_key]
		):
			issues_found = True
			gh_summary(
				f"⚠ In {lang}.json, the translation for {radar_key} contains untranslated colors:"
			)
			gh_summary("```json")
			gh_summary(f'  "{radar_key}": "{data[radar_key]}"')
			gh_summary("```")

	if issues_found:
		raise Exception("Found known issues in one or more translation files")
	gh_summary("✅ No known issues found in any translation files")


def main(lang_dir: Path, wurst_mode: bool):
	en_us = read_json_file(lang_dir / "en_us.json")
	translations = {}
	for path in sorted(lang_dir.rglob("*.json"), key=lambda x: x.name):
		if path.is_file() and path.name != "en_us.json":
			lang = path.name.removesuffix(".json")
			data = read_json_file(path)
			data.pop("language.name", None)
			data.pop("language.region", None)
			data.pop("language.code", None)
			translations[lang] = data

	show_translation_stats(en_us, translations)
	check_extra_keys(en_us, translations)
	check_untranslated_strings(en_us, translations)
	check_order_of_strings(en_us, translations)
	if wurst_mode:
		check_known_issues(en_us, translations)


if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument("--lang-dir", type=Path)
	parser.add_argument("--wurst-mode", action="store_true")
	args = parser.parse_args()
	lang_dir = args.lang_dir
	main(lang_dir, args.wurst_mode)
