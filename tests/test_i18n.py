import string
import unittest
from distroflash.i18n import LANGUAGES, MESSAGES, detect_language, tr


class LanguageTests(unittest.TestCase):
    def test_default_is_english(self):
        self.assertEqual(detect_language({}), "en")
        self.assertEqual(detect_language({"LANG": "nl_NL.UTF-8"}), "en")

    def test_all_five_locales(self):
        for language in ("en", "it", "fr", "de", "es"):
            self.assertEqual(detect_language({"LANG": language + "_XX.UTF-8"}), language)

    def test_lc_all_overrides_lang(self):
        self.assertEqual(detect_language({"LC_ALL": "de_DE.UTF-8", "LANG": "it_IT.UTF-8"}), "de")

    def test_language_preference_list(self):
        self.assertEqual(detect_language({"LANGUAGE": "nl:fr:it", "LANG": "en_US.UTF-8"}), "fr")

    def test_c_locale_is_english(self):
        self.assertEqual(detect_language({"LC_ALL": "C", "LANGUAGE": "it"}), "en")

    def test_catalogs_are_complete_and_keep_format_fields(self):
        fields = lambda text: sorted((name, spec, conv) for _, name, spec, conv
                                     in string.Formatter().parse(text) if name is not None)
        self.assertGreater(len(MESSAGES), 70)
        for english, translations in MESSAGES.items():
            self.assertEqual(set(translations), set(LANGUAGES))
            for language, text in translations.items():
                self.assertTrue(text, (english, language))
                self.assertEqual(fields(english), fields(text), (english, language))

    def test_unknown_message_falls_back_to_source(self):
        self.assertEqual(tr("external error", "es"), "external error")
