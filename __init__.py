import json
import datetime
from adapt.intent import IntentBuilder
import requests
from mycroft import MycroftSkill, intent_handler
from mycroft.util.parse import extract_number


class CovidRkiDatenabfrage(MycroftSkill):

    def __init__(self):
        MycroftSkill.__init__(self)
        self.maximalwerte_options = ['Infektionen', 'Impfungen']
        self.api_endpoint = 'https://api.corona-zahlen.org'

    @intent_handler(IntentBuilder('Impfungen.intent').require('ImpfungenKeyword'))
    def handle_impfungen_intent(self, message):
        number_of_vaccinations = self.getVaccinations('1')
        if number_of_vaccinations > 0:
            self.speak('Gestern gab es {} neue Impfungen.'.format(number_of_vaccinations))
        else:
            self.speak_dialog('Fehler')

    @intent_handler(IntentBuilder('Inzidenz').require('InzidenzKeyword').require('AktuellKeyword'))
    def handle_inzidenz_aktuell_intent(self, message):
        incidence = round(self.getIncidence())
        self.speak(
            'Die Inzidenz beträgt deutschlandweit aktuell {} Neuinfektionen je 100000 Einwohner.'.format(incidence))

    @intent_handler(IntentBuilder('Hospitalisierungsrate').require('Hospitalisierungsrate').require('AktuellKeyword'))
    def handle_hospitalisierungsrate_aktuell_intent(self, message):
        number_of_hospitalization = self.getHospitalization()
        self.speak(
            'Die Hospitalisierungsrate beträgt aktuell {} je 100000 Einwohner.'.format(number_of_hospitalization))

    @intent_handler(IntentBuilder('InfektionenAktuell').require('Infektionen').require('AktuellKeyword'))
    def handle_infektionen_aktuell_intent(self, message):
        number_of_infections = self.getInfections('1')
        self.speak('Es gab gestern {} gemeldete Infektionen.'.format(number_of_infections))

    @intent_handler(IntentBuilder('InfektionenZeitraum.intent').require('Infektionen'))
    def handle_infektionen_x_tage_intent(self, message):
        anzahl_tage = extract_number(message.data.get('utterance')) or 1
        neue_infektionen = self.getInfections(str(anzahl_tage))
        self.speak('Es gab in den letzten {} Tagen insgesamt {} gemeldete Infektionen.'.format(round(anzahl_tage),
                                                                                               neue_infektionen))

    @intent_handler(IntentBuilder('MaximalwerteDialog.intent').require('Corona').require('Maximalwerte'))
    def handle_maximalwerte_dialog_intent(self, message):
        self.speak('Ich kann dir folgende Maximalwerte anbieten:')
        auswahl = self.ask_selection(self.maximalwerte_options)
        if auswahl == 'Infektionen':
            max_infections, date_of_max = self.getMaxInfections()
            self.speak('Der Rekord liegt bei {} gemeldeten Infektionen an einem Tag und wurde am {} erzielt.'.format(
                max_infections, date_of_max.strftime("%d.%m.%Y")))
        elif auswahl == 'Impfungen':
            max_vaccinations, date_of_max = self.getMaxVaccinations()
            self.speak('Der Rekord liegt bei {} durchgeführten Impfungen an einem Tag und wurde am {} erzielt.'.format(
                max_vaccinations, date_of_max.strftime("%d.%m.%Y")))
        else:
            self.speak_dialog('Fehler')
            return

    @intent_handler(IntentBuilder('MaximalwertImpfungen.intent').require('Maximalwerte').require('ImpfungenKeyword'))
    def handle_maximalwert_impfungen_intent(self, message):
        max_vaccinations, date_of_max = self.getMaxVaccinations()
        self.speak('Der Rekord liegt bei {} durchgeführten Impfungen an einem Tag und wurde am {} erzielt.'.format(
            max_vaccinations, date_of_max.strftime("%d.%m.%Y")))


    @intent_handler(IntentBuilder('MaximalwertInfektionen.intent').require('Maximalwerte').require('Infektionen'))
    def handle_maximalwert_infektionen_intent(self, message):
        max_infections, date_of_max = self.getMaxInfections()
        self.speak('Der Rekord liegt bei {} gemeldeten Infektionen an einem Tag und wurde am {} erzielt.'.format(
            max_infections, date_of_max.strftime("%d.%m.%Y")))


    @intent_handler(IntentBuilder('DurchschnittImpfungen.intent').require('ImpfungenKeyword').require('Durchschnitt'))
    def handle_durchschnittMonat_impfungen_intent(self, message):
        average_vaccinations_last_month = round(self.getAverageVaccinationsLastMonth())
        self.speak('Im Durchschnitt wurden im letzten Monat etwa {} Menschen pro Tag geimpft.'.format(
            average_vaccinations_last_month))

    @intent_handler(IntentBuilder('ErsterFall.intent').require('Corona'))
    def handle_first_case_intent(self, message):
        self.speak(
            'Die erste Corona-Infektion in Deutschland wurde am 27.01.2020 in Bayern gemeldet.')  # Fester Wert, deshalb kein API-Aufruf notwendig.

    @intent_handler(IntentBuilder('InzidenzBundesland.intent').require('InzidenzKeyword').require('Bundesland'))
    def handle_inzidenz_Bundesland_intent(self, message):
        bundesland = message.data.get('Bundesland')  # 'Baden-Württemberg'
        inzidenz = self.getInzidenzInBundesland(bundesland)
        if inzidenz >= 0:
            self.speak('In {} beträgt die Inzidenz aktuell {}'.format(bundesland, inzidenz))
        else:
            self.speak_dialog('Fehler')

    def getVaccinations(self, numberOfDays):
        response = requests.get(self.api_endpoint + "/vaccinations/history/" + numberOfDays)
        data = json.loads(response.text)
        history_data = data['data']['history']
        total_number_of_vaccinated_people = 0
        for i in history_data:
            total_number_of_vaccinated_people += i['vaccinated']

        return total_number_of_vaccinated_people

    def getInfections(self, numberOfDays):
        response = requests.get(self.api_endpoint + "/germany/history/cases/" + numberOfDays)
        data = json.loads(response.text)
        data_array = data['data']
        total_number_of_new_Infections = 0
        for i in data_array:
            total_number_of_new_Infections += i['cases']

        return total_number_of_new_Infections

    def getHospitalization(self):
        response = requests.get(self.api_endpoint + "/germany/history/hospitalization/1")
        data = json.loads(response.text)
        data_array = data['data']
        hospitalization_inzdenz = data_array[0]['incidence7Days']
        return hospitalization_inzdenz

    def getIncidence(self):
        response = requests.get(self.api_endpoint + "/germany/history/incidence/1")
        data = json.loads(response.text)
        data_array = data['data']
        inzidenz = data_array[0]['weekIncidence']
        return inzidenz

    def getMaxInfections(self):
        response = requests.get(self.api_endpoint + "/germany/history/cases")
        data = json.loads(response.text)
        data_array = data['data']
        maximalwert = 0
        date_of_max = datetime.datetime.now()
        for data_point in data_array:
            if data_point['cases'] > maximalwert:
                maximalwert = data_point['cases']
                date_of_max = data_point['date']

        datetime_of_max = datetime.datetime.strptime(date_of_max, '%Y-%m-%dT%H:%M:%S.%fZ')
        return maximalwert, datetime_of_max

    def getMaxVaccinations(self):
        response = requests.get(self.api_endpoint + "/vaccinations/history")
        data = json.loads(response.text)
        data_array = data['data']['history']
        maximalwert = 0
        date_of_max = datetime.datetime.now()
        for data_point in data_array:
            if data_point['vaccinated'] > maximalwert:
                maximalwert = data_point['vaccinated']
                date_of_max = data_point['date']

        datetime_of_max = datetime.datetime.strptime(date_of_max, '%Y-%m-%dT%H:%M:%S.%fZ')
        return maximalwert, datetime_of_max

    def getAverageVaccinationsLastMonth(self):
        response = requests.get(self.api_endpoint + "/vaccinations/history/30")
        data = json.loads(response.text)
        history_data = data['data']['history']
        total_number_of_vaccinated_people = 0
        for i in history_data:
            total_number_of_vaccinated_people += i['vaccinated']

        average = total_number_of_vaccinated_people / len(history_data)

        return average

    def getInzidenzInBundesland(self, bundesland):
        response = requests.get(self.api_endpoint + "/states")
        data = json.loads(response.text)
        data_points = data['data']

        for data_point in data_points:
            bundesland_datapoint = data_points[data_point]
            if bundesland.lower() == bundesland_datapoint['name'].lower():
                return round(bundesland_datapoint['weekIncidence'])
        return -1

    def stop(self):
        pass


def create_skill():
    return CovidRkiDatenabfrage()
