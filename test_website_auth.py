import unittest
import WebsiteAuth


class TestFreeSoundAuth(unittest.TestCase):
    def setUp(self):
        self.session = WebsiteAuth.FreeSound('brinkmansound@gmail.com', 'Ferrari578')

    def test_login(self):
        self.session.login()

    def test_set_token_id(self):
        html = "<input type=\'hidden\' name=\'csrfmiddlewaretoken\' value=\'" \
               "ZsrYhaWmCxs3XUnUMLZpsgebJLy1Pvdyeb7DkDnh9QhCLtGM5phmihcRS7qpNGiB\' />"
        self.session.set_token_id(html)
        self.assertIsInstance(self.session.login_data[self.session.token_id_form[0]], str)

    def test_find_sound(self):
        html = "<a href=\"/people/zagi2/sounds/330686/download/330686__zagi2__harpsichord-phrase.wav\" onclick=\"_gaq." \
               "push(['_trackEvent', 'Sound', 'Download', 'sound_id:330686']);afterDownloadModal('/after-download-" \
               "modal/','harpsichord phrase.wav');\" id=\"download_button\" title=\"download sound\"></a>"
        self.assertIn('http', self.session.find_sound_url(html))

    def test_get_sound_link(self):
        url = "https://freesound.org/people/zagi2/sounds/330686/"
        self.assertEqual("http://freesound.org/people/zagi2/sounds/330686/download/330686__"
                         "zagi2__harpsichord-phrase.wav", self.session.get_sound_link(url))


if __name__ == '__main__':
    unittest.main()
