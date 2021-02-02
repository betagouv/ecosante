from dataclasses import dataclass
from datetime import datetime
from flask.helpers import url_for
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from ecosante.inscription.blueprint import inscription
from flask import current_app
from ecosante.inscription.models import Inscription
from ecosante.recommandations.models import Recommandation
from ecosante.utils.funcs import (
    convert_boolean_to_oui_non,
    generate_line,
    oxford_comma
)
from ecosante.extensions import db
from indice_pollution import bulk, today, forecast as get_forecast, episodes as get_episodes

@dataclass
class Newsletter:
    date: datetime
    recommandation: Recommandation
    inscription: Inscription
    forecast: dict
    episodes: list
    raep: int

    def __init__(self, inscription, seed=None, preferred_reco=None, recommandations=None, forecast=None, recommandation_id=None, episodes=None, raep=None):
        recommandations = recommandations or Recommandation.shuffled(user_seed=seed, preferred_reco=preferred_reco)
        self.date = today()
        self.inscription = inscription
        try:
            self.forecast = forecast or get_forecast(self.inscription.ville_insee, self.date, True)
        except KeyError as e:
            current_app.logger.error(f'Unable to find region for {self.inscription.ville_name} ({self.inscription.ville_insee})')
            current_app.logger.error(e)
            self.forecast = dict()
        try:
            self.episodes = episodes or get_episodes(self.inscription.ville_insee, self.date)
        except KeyError as e:
            current_app.logger.error(f'Unable to find region for {self.inscription.ville_name} ({self.inscription.ville_insee})')
            current_app.logger.error(e)
            self.episodes = dict()
        if not 'label' in self.today_forecast:
            current_app.logger.error(f'No label for forecast for inscription: id: {inscription.id} insee: {inscription.ville_insee}')
        if not 'couleur' in self.today_forecast:
            current_app.logger.error(f'No couleur for forecast for inscription: id: {inscription.id} insee: {inscription.ville_insee}')
        self.polluants = [
            {
                '1': 'dioxyde_soufre',
                '5': 'particules_fines',
                '7': 'ozone',
                '8': 'dioxyde_azote',
            }.get(str(e['code_pol']), f'erreur: {e["code_pol"]}')
            for e in self.episodes['data']
            if e['etat'] != 'PAS DE DEPASSEMENT'
        ]

        self.recommandation =\
             Recommandation.query.get(recommandation_id) or\
             Recommandation.get_relevant(
                recommandations,
                inscription,
                self.qualif,
                self.polluants
            )
        self.raep = int(raep)

    @property
    def polluants_formatted(self):
        label_to_formatted_text ={
            'dioxyde_soufre': 'au dioxyde de soufre',
            'particules_fines': 'aux particules fines',
            'ozone': 'à l’ozone',
            'dioxyde_azote': 'au dioxyde d’azote'
        }
        return oxford_comma([label_to_formatted_text.get(pol) for pol in self.polluants])

    @property
    def polluants_symbols(self):
        label_to_symbols = {
            'ozone': "o3",
            'particules_fines': "pm10",
            'dioxyde_azote': "no2",
            "dioxyde_soufre": "so2"
        }
        return [label_to_symbols.get(label) for label in self.polluants]

    @classmethod
    def from_inscription_id(cls, inscription_id):
        inscription = Inscription.query.get(inscription_id)
        return cls(inscription)

    @classmethod
    def from_csv_line(cls, line):
        inscription = Inscription.query.filter_by(mail=line['MAIL']).first()
        return cls(
            inscription,
            recommandation_id=line['ID RECOMMANDATION']
        )

    @property
    def today_forecast(self):
        data = self.forecast['data']
        try:
            return next(iter([v for v in data if v['date'] == str(self.date)]), dict())
        except (TypeError, ValueError, StopIteration) as e:
            current_app.logger.error(f'Unable to get forecast for inscription: id: {self.inscription.id} insee: {self.inscription.ville_insee}')
            current_app.logger.error(e)
            return dict()

    @property
    def today_episodes(self):
        data = self.episodes['data']
        try:
            return [v for v in data if v['date'] == str(self.date)]
        except (TypeError, ValueError, StopIteration) as e:
            current_app.logger.error(f'Unable to get episodes for inscription: id: {self.inscription.id} insee: {self.inscription.ville_insee}')
            current_app.logger.error(e)
            return dict()

    @property
    def qualif(self):
        return self.today_forecast.get('indice')

    @property
    def label(self):
        return self.today_forecast.get('label')
    
    @property
    def couleur(self):
        return self.today_forecast.get('couleur')

    @property
    def get_episodes_depassements(self):
        return [e for e in self.today_episodes if e['etat'] != 'PAS DE DEPASSEMENT']

    @property
    def has_depassement(self):
        return len(self.get_depassement) > 0

    @classmethod
    def generate_csv(cls, preferred_reco=None, seed=None, remove_reco=[]):
        yield generate_line([
            'VILLE',
            'Moyens de transport',
            "Activité sportive",
            "Activité physique adaptée",
            "Activités",
            "Pathologie respiratoire",
            "Allergie aux pollens",
            "Fume",
            "Enfants",
            'MAIL',
            'FORMAT',
            'SMS',
            "Fréquence",
            "Consentement",
            "Date d'inscription",
            "QUALITE_AIR",
            "BACKGROUND_COLOR",
            "Région",
            "LIEN_AASQA",
            "RECOMMANDATION",
            "PRECISIONS",
            "ID RECOMMANDATION"
        ])
        for newsletter in cls.export(preferred_reco, seed, remove_reco):
            yield newsletter.csv_line()

    @classmethod
    def export(cls, preferred_reco=None, user_seed=None, remove_reco=[]):
        recommandations = Recommandation.shuffled(user_seed=user_seed, preferred_reco=preferred_reco, remove_reco=remove_reco)
        inscriptions = Inscription.active_query().distinct(Inscription.ville_insee)
        insee_region = {i.ville_insee: i.region_name for i in inscriptions}
        insee_forecast = bulk(insee_region, fetch_episodes=True, fetch_allergenes=True)
        for inscription in Inscription.active_query().all():
            if inscription.ville_insee not in insee_forecast:
                continue
            newsletter = cls(
                inscription,
                recommandations=recommandations,
                forecast=insee_forecast[inscription.ville_insee]["forecast"],
                episodes=insee_forecast[inscription.ville_insee]["episode"],
                raep=insee_forecast[inscription.ville_insee]["raep"]
            )
            if inscription.frequence == "pollution" and newsletter.qualif and newsletter.qualif not in ['mauvais', 'tres_mauvais', 'extrement_mauvais']:
                continue
            yield newsletter

    def csv_line(self):
        return generate_line([
            self.inscription.ville_name,
            "; ".join(self.inscription.deplacement or []),
            convert_boolean_to_oui_non(self.inscription.sport),
            "Non",
            ";".join(self.inscription.activites or []),
            convert_boolean_to_oui_non(self.inscription.pathologie_respiratoire),
            convert_boolean_to_oui_non(self.inscription.allergie_pollen),
            convert_boolean_to_oui_non(self.inscription.fumeur),
            convert_boolean_to_oui_non(self.inscription.enfants),
            self.inscription.mail,
            self.inscription.diffusion,
            self.inscription.telephone,
            self.inscription.frequence,
            "Oui",
            self.inscription.date_inscription,
            self.qualif,
            self.couleur,
            self.forecast['metadata']['region']['nom'],
            self.forecast['metadata']['region']['website'],
            self.recommandation.format(self.inscription),
            self.recommandation.precisions,
            self.recommandation.id
        ])

    @property
    def lien_recommandations_alert(self):
        population = "vulnerable" if self.inscription.personne_sensible else "generale"
        return url_for(
            "pages.recommandation_episode_pollution",
            population=population,
            polluants=self.polluants_symbols,
            _external=True)

class NewsletterDB(db.Model, Newsletter):
    __tablename__ = "newsletter"
    id = db.Column(db.Integer, primary_key=True)
    short_id = db.Column(
        db.String(),
        server_default=text("generate_random_id('public', 'newsletter', 'short_id', 8)")
    )
    inscription_id = db.Column(db.Integer, db.ForeignKey('inscription.id'))
    inscription = db.relationship("Inscription", backref="inscription")
    recommandation_id = db.Column(db.Integer, db.ForeignKey('recommandation.id'))
    recommandation = db.relationship("Recommandation")
    date = db.Column(db.Date())
    qai = db.Column(db.Integer())
    qualif = db.Column(db.String())
    appliquee = db.Column(db.Boolean())
    avis = db.Column(db.String())
    polluants = db.Column(postgresql.ARRAY(db.String()))
    raep = db.Column(db.Integer())

    def __init__(self, newsletter):
        self.inscription = newsletter.inscription
        self.inscription_id = newsletter.inscription.id
        self.recommandation = newsletter.recommandation
        self.recommandation_id = newsletter.recommandation.id
        self.date = newsletter.date
        self.qualif = newsletter.qualif
        self.forecast = newsletter.forecast
        self.episodes = newsletter.episodes
        self.polluants = newsletter.polluants
        self.raep = newsletter.raep

    def attributes(self):
        to_return = {
            'FORMAT': self.inscription.diffusion,
            'QUALITE_AIR': self.label,
            'LIEN_AASQA': self.forecast['metadata']['region']['website'],
            'RECOMMANDATION': self.recommandation.format(self.inscription),
            'PRECISIONS': self.recommandation.precisions,
            'VILLE': self.inscription.ville_name,
            'BACKGROUND_COLOR': self.couleur,
            'SHORT_ID': self.short_id,
            'POLLUANTS': self.polluants_formatted,
            'LIEN_RECOMMANDATIONS_ALERTE': self.lien_recommandations_alert,
        }
        if self.inscription.telephone and len(self.inscription.telephone) == 12:
            to_return['SMS'] = self.inscription.telephone
        return to_return
