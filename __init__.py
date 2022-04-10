"""
corona-daten-abfrageskill
"""
import json
import datetime
from adapt.intent import IntentBuilder
import requests
from mycroft import MycroftSkill, intent_handler
from mycroft.util.parse import extract_number


class CovidRkiDatenabfrage(MycroftSkill):
    """
    Klasse für den Corona-Daten-Abfrageskill. Dieser Skill liefert mit Hilfe der
    RKI Schnittstelle aktuelle und historische Corona-Daten.
    """
    def __init__(self):
        MycroftSkill.__init__(self)
        self.maximalwerte_options = ['Infektionen', 'Impfungen']
        self.api_endpoint = 'https://api.corona-zahlen.org'

    @intent_handler(
        IntentBuilder('Impfungen.intent').require('ImpfungenKeyword'))
    def handle_impfungen_intent(self, message): # parameter message nicht relevant pylint: disable=unused-argument
        """
        Behandelt den Intent der aktuellen Zahl der Corona-Imfpungen
        (Meldung für den gestrigen Tag). \n
        Achtung: Kann aufgrund von am Wochenende fehlenden Daten
        Fehlermeldung auswerfen.
        """
        number_of_vaccinations = self.get_vaccinations('1')
        if number_of_vaccinations > 0:
            self.speak('Gestern gab es {} neue Impfungen.'.format(# pylint: disable=consider-using-f-string
                number_of_vaccinations))
        else:
            self.speak_dialog('Fehler')

    @intent_handler(
        IntentBuilder('Inzidenz').require('InzidenzKeyword').require(
            'AktuellKeyword'))
    def handle_inzidenz_aktuell_intent(self, message): # parameter message nicht relevant pylint: disable=unused-argument
        """
        Behandelt den Intent der aktuellen 7-Tage-Inzidenz
        (Meldung für den gestrigen Tag).
        """
        incidence = round(self.get_incidence())
        self.speak(
            'Die Inzidenz beträgt deutschlandweit aktuell {} Neuinfektionen je 100000 Einwohner.'.format(# pylint: disable=consider-using-f-string, line-too-long
                incidence))

    @intent_handler(IntentBuilder('Hospitalisierungsrate').require(
        'Hospitalisierungsrate').require('AktuellKeyword'))
    def handle_hospitalisierungsrate_aktuell_intent(self, message):# parameter message nicht relevant pylint: disable=unused-argument
        """
        Behandelt den Intent der aktuellen Hospitalisierungsrate
        (Meldung für den gestrigen Tag).
        """
        number_of_hospitalization = self.get_hospitalization()
        self.speak(
            'Die Hospitalisierungsrate beträgt aktuell {} je 100000 Einwohner.'.format(# pylint: disable=consider-using-f-string, line-too-long
                number_of_hospitalization))

    @intent_handler(
        IntentBuilder('InfektionenAktuell').require('Infektionen').require(
            'AktuellKeyword'))
    def handle_infektionen_aktuell_intent(self, message):# parameter message nicht relevant pylint: disable=unused-argument
        """
        Behandelt den Intent der aktuellen Zahl der neuen Infektionen
        (Meldung für den gestrigen Tag).
        """
        number_of_infections = self.get_infections('1')
        self.speak('Es gab gestern {} gemeldete Infektionen.'.format(# pylint: disable=consider-using-f-string
            number_of_infections))

    @intent_handler(
        IntentBuilder('InfektionenZeitraum.intent').require('Infektionen'))
    def handle_infektionen_x_tage_intent(self, message):
        """
        Behandelt den Intent der Infektionen in den letzten X Tagen.
        Sollte kein passender Zahlenwert erkannt werden wird der gestrige Wert
        verwendet.
        Die Werte der einzelnen Tage werden aufsummiert.
        """
        anzahl_tage = extract_number(message.data.get('utterance')) or 1
        neue_infektionen = self.get_infections(str(anzahl_tage))
        self.speak(
            'Es gab in den letzten {} Tagen insgesamt {} gemeldete Infektionen.'.format(# pylint: disable=consider-using-f-string
                round(anzahl_tage),
                neue_infektionen))

    @intent_handler(
        IntentBuilder('MaximalwerteDialog.intent').require('Corona').require(
            'Maximalwerte'))
    def handle_maximalwerte_dialog_intent(self, message):# parameter message nicht relevant pylint: disable=unused-argument
        """
        Behandelt den Intent zur Abfrage der Maximalwerte, die dieser Skill
        zurückgeben kann. Ruft je nach Dialog den Maximalwert für Impfungen
        oder Infektionen ab.
        """
        self.speak('Ich kann dir folgende Maximalwerte anbieten:')
        auswahl = self.ask_selection(self.maximalwerte_options)
        if auswahl == 'Infektionen':
            max_infections, date_of_max = self.get_max_infections()
            self.speak(
                'Der Rekord liegt bei {} gemeldeten Infektionen an einem Tag und wurde am {} erzielt.'.format(# pylint: disable=consider-using-f-string, line-too-long
                    max_infections, date_of_max.strftime("%d.%m.%Y")))
        elif auswahl == 'Impfungen':
            max_vaccinations, date_of_max = self.get_max_vaccinations()
            self.speak(
                'Der Rekord liegt bei {} durchgeführten Impfungen an einem Tag und wurde am {} erzielt.'.format(# pylint: disable=consider-using-f-string, line-too-long
                    max_vaccinations, date_of_max.strftime("%d.%m.%Y")))
        else:
            self.speak_dialog('Fehler')
            return

    @intent_handler(IntentBuilder('MaximalwertImpfungen.intent').require(
        'Maximalwerte').require('ImpfungenKeyword'))
    def handle_maximalwert_impfungen_intent(self, message):# parameter message nicht relevant pylint: disable=unused-argument
        """
        Behandelt den Intent zur Abfrage des Maximalwerts der täglichen
        Impfungen.
        """
        max_vaccinations, date_of_max = self.get_max_vaccinations()
        self.speak(
            'Der Rekord liegt bei {} durchgeführten Impfungen an einem Tag und wurde am {} erzielt.'.format(# pylint: disable=consider-using-f-string, line-too-long
                max_vaccinations, date_of_max.strftime("%d.%m.%Y")))

    @intent_handler(IntentBuilder('MaximalwertInfektionen.intent').require(
        'Maximalwerte').require('Infektionen'))
    def handle_maximalwert_infektionen_intent(self, message):# parameter message nicht relevant pylint: disable=unused-argument
        """
        Behandelt den Intent zur Abfrage des Maximalwerts der täglichen
        Infektionen.
        """
        max_infections, date_of_max = self.get_max_infections()
        self.speak(
            'Der Rekord liegt bei {} gemeldeten Infektionen an einem Tag und wurde am {} erzielt.'.format(# pylint: disable=consider-using-f-string, line-too-long
                max_infections, date_of_max.strftime("%d.%m.%Y")))

    @intent_handler(IntentBuilder('DurchschnittImpfungen.intent').require(
        'ImpfungenKeyword').require('Durchschnitt'))
    def handle_durchschnitt_impfungen_letzte_x_monate_intent(self, message):
        """
        Behandelt den Intent zur Abfrage des Durchschnittswerts der täglichen
        Impfungen in einem Zeitraum der letzten X Monate (ein Monat entspricht
        hier 30 Tagen). Ohne Anzahl der Monate wird der Durchschnitt für die
        letzten 30 Tage ausgegeben.
        """
        anzahl_monate = extract_number(message.data.get('utterance'))
        if anzahl_monate is not None and anzahl_monate > 0:
            average_vaccinations_last_month = round(
                self.get_average_vaccinations_last_x_months(anzahl_monate))
            self.speak(
                'Im Durchschnitt wurden in den letzten {} Monaten etwa {} Menschen pro Tag geimpft.'.format(# pylint: disable=consider-using-f-string, line-too-long
                    round(anzahl_monate),
                    average_vaccinations_last_month))
        else:
            average_vaccinations_last_month = round(
                self.get_average_vaccinations_last_x_months(1))
            self.speak(
                'Im Durchschnitt wurden im letzten Monat etwa {} Menschen pro Tag geimpft.'.format(# pylint: disable=consider-using-f-string
                    average_vaccinations_last_month))

    @intent_handler(IntentBuilder('ErsterFall.intent').require('Corona'))
    def handle_first_case_intent(self, message):# parameter message nicht relevant pylint: disable=unused-argument
        """
        Behandelt den Intent zur Abfrage des ersten registrierten Coronafalls
        in Deutschland.
        """
        self.speak(
            'Die erste Corona-Infektion in Deutschland wurde am 27.01.2020 in Bayern gemeldet.')  # Fester Wert, deshalb kein API-Aufruf notwendig. pylint: disable=line-too-long

    @intent_handler(IntentBuilder('InzidenzBundesland.intent').require(
        'InzidenzKeyword').require('Bundesland'))
    def handle_inzidenz_bundesland_intent(self, message):
        """
        Behandelt den Intent der aktuellen 7-Tage-Inzidenz je nach Bundesland
        (Meldung für den gestrigen Tag).
        """
        bundesland = message.data.get('Bundesland')  # Beispiel: 'Baden-Württemberg'
        inzidenz = self.get_inzidenz_in_bundesland(bundesland)
        if inzidenz >= 0:
            self.speak(
                'In {} beträgt die Inzidenz aktuell {}'.format(bundesland,# pylint: disable=consider-using-f-string
                                                               inzidenz))
        else:
            self.speak_dialog('Fehler')

    def get_vaccinations(self, number_of_days):
        """
        Gibt die Anzahl/Summe  der Impfungen der letzten X Tage zurück.

        :param number_of_days: str
        Anzahl der Tage zurückgehend von heute, von denen
        die Zahlen der Impfungen aufsummiert werden sollen.
        :return: Summe der Impfungen der letzten X Tage.
        """
        response = requests.get(
            self.api_endpoint + "/vaccinations/history/" + number_of_days)
        data = json.loads(response.text)
        history_data = data['data']['history']
        total_number_of_vaccinated_people = 0
        for i in history_data:
            total_number_of_vaccinated_people += i['vaccinated']

        return total_number_of_vaccinated_people

    def get_infections(self, number_of_days):
        """
        Gibt die Anzahl/Summe der neuen Infektionen der letzten X Tage zurück.
        :param number_of_days: str
        Anzahl der Tage zurückgehend von heute, von denen
        die Zahlen der Infektionen aufsummiert werden sollen.
        :return: Summe der Infektionen der letzten X Tage.
        """
        response = requests.get(
            self.api_endpoint + "/germany/history/cases/" + number_of_days)
        data = json.loads(response.text)
        data_array = data['data']
        total_number_of_new_infections = 0
        for i in data_array:
            total_number_of_new_infections += i['cases']

        return total_number_of_new_infections

    def get_hospitalization(self):
        """
        Gibt den aktuellen/gestrigen Wert für die Hospitalisierungsrate je
        100 000 Einwohner in Deutschland zurück.

        :return: Hospitaliserungsrate in Deutschland.
        """
        response = requests.get(
            self.api_endpoint + "/germany/history/hospitalization/1")
        data = json.loads(response.text)
        data_array = data['data']
        hospitalization_inzdenz = data_array[0]['incidence7Days']
        return hospitalization_inzdenz

    def get_incidence(self):
        """
        Gibt den aktuellen/gestrigen Wert für die Inzidenz je 100 000 Einwohner
        in Deutschland zurück.

        :return: Inzidenz in Deutschland
        """
        response = requests.get(
            self.api_endpoint + "/germany/history/incidence/1")
        data = json.loads(response.text)
        data_array = data['data']
        inzidenz = data_array[0]['weekIncidence']
        return inzidenz

    def get_max_infections(self):
        """
        Gibt den Maximalwert für Infektionen an einem Tag in Deutschland an.

        :return: Maximalwert tägliche Infektionen in Deutschland.
        """
        response = requests.get(self.api_endpoint + "/germany/history/cases")
        data = json.loads(response.text)
        data_array = data['data']
        maximalwert = 0
        date_of_max = datetime.datetime.now()
        for data_point in data_array:
            if data_point['cases'] > maximalwert:
                maximalwert = data_point['cases']
                date_of_max = data_point['date']

        datetime_of_max = datetime.datetime.strptime(date_of_max,
                                                     '%Y-%m-%dT%H:%M:%S.%fZ')
        return maximalwert, datetime_of_max

    def get_max_vaccinations(self):
        """
        Gibt den Maximalwert für Impfungen an einem Tag in Deutschland an.

        :return: Maximalwert tägliche Impfungen in Deutschland.
        """
        response = requests.get(self.api_endpoint + "/vaccinations/history")
        data = json.loads(response.text)
        data_array = data['data']['history']
        maximalwert = 0
        date_of_max = datetime.datetime.now()
        for data_point in data_array:
            if data_point['vaccinated'] > maximalwert:
                maximalwert = data_point['vaccinated']
                date_of_max = data_point['date']

        datetime_of_max = datetime.datetime.strptime(date_of_max,
                                                     '%Y-%m-%dT%H:%M:%S.%fZ')
        return maximalwert, datetime_of_max

    def get_average_vaccinations_last_x_months(self, number_of_months):
        """
        Gibt den Durchschnitt der Impfungen in Deutschland der letzten X Monate
        zurück. Ein Monat entspricht 30 Tagen.

        :param number_of_months: str
        Anzahl der Monate für die Betrachtung des Durchschnitts
        :return: Durschnitt der Impfungen der letzten X Moante.
        """
        response = requests.get(
            self.api_endpoint + "/vaccinations/history/{}".format(# pylint: disable=consider-using-f-string
                (number_of_months * 30)))
        data = json.loads(response.text)
        history_data = data['data']['history']
        total_number_of_vaccinated_people = 0
        for i in history_data:
            total_number_of_vaccinated_people += i['vaccinated']

        average = total_number_of_vaccinated_people / len(history_data)

        return average

    def get_inzidenz_in_bundesland(self, bundesland):
        """
        Gibt die 7-Tage-Inzidenz für das jeweilige Bundesland zurück.

        :param bundesland: str
        Eines der 16 Bundesländer der Bundesrepublik Deutschland.
        :return: 7-Tage-Inzidenz des jeweilgen Bundeslands oder falls kein
        korrektes Bundesland als Parameter -1
        """
        response = requests.get(self.api_endpoint + "/states")
        data = json.loads(response.text)
        data_points = data['data']

        for data_point in data_points:
            bundesland_datapoint = data_points[data_point]
            if bundesland.lower() == bundesland_datapoint['name'].lower():
                return round(bundesland_datapoint['weekIncidence'])
        return -1

    def stop(self):
        """
        Default Funktion benötigt von MyCroft.
        """
        pass # pylint: disable=unnecessary-pass


def create_skill():
    """
    Default Funktion von MyCroft zum Abrufen einer Instanz des Skills.
    :return: Instanz der Klasse.
    """
    return CovidRkiDatenabfrage()
