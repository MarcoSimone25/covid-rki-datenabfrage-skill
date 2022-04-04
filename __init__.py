from mycroft import MycroftSkill, intent_file_handler


class CovidRkiDatenabfrage(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('datenabfrage.rki.covid.intent')
    def handle_datenabfrage_rki_covid(self, message):
        self.speak_dialog('datenabfrage.rki.covid')


def create_skill():
    return CovidRkiDatenabfrage()

