from ecosante.extensions import db
from ecosante.utils.funcs import generate_line
from sqlalchemy.dialects import postgresql
from sqlalchemy import func
from datetime import (
    date,
    timedelta
)
from dataclasses import dataclass
from typing import List
import requests
from datetime import date
from sqlalchemy import text, or_
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.attributes import flag_modified

@dataclass
class Inscription(db.Model):
    ville_insee: str
    sport: bool


    id: int = db.Column(db.Integer, primary_key=True)
    uid: str = db.Column(
        db.String(),
        server_default=text("generate_random_id('public', 'inscription', 'uid', 8)")
    )
    ville_entree: str = db.Column(db.String)
    ville_name: str = db.Column(db.String)
    _ville_insee: str = db.Column("ville_insee", db.String)
    diffusion: str = db.Column("diffusion", db.Enum("sms", "mail", name="diffusion_enum"), default="mail")
    _telephone: str = db.Column("telephone", db.String)
    mail: str = db.Column(db.String)
    frequence: str = db.Column(db.Enum("quotidien", "pollution", name="frequence_enum"), default="quotidien")
    #Habitudes
    deplacement: str = db.Column(postgresql.ARRAY(db.String))
    _sport: bool = db.Column("sport", db.Boolean)
    apa: bool = db.Column(db.Boolean)
    activites: List[str] = db.Column(postgresql.ARRAY(db.String))
    enfants: str = db.Column("enfants", db.String)
    chauffage: List[str] = db.Column(postgresql.ARRAY(db.String))
    animaux_domestiques: List[str] = db.Column(postgresql.ARRAY(db.String))
    #Sante
    population: List[str] = db.Column(postgresql.ARRAY(db.String))
    #Misc
    deactivation_date: date = db.Column(db.Date)
    connaissance_produit: List[str] = db.Column(postgresql.ARRAY(db.String))

    date_inscription = db.Column(db.Date())
    _cache_api_commune = db.Column("cache_api_commune", db.JSON())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.date_inscription = date.today()

    def has_deplacement(self, deplacement):
        return self.deplacement and deplacement in self.deplacement

    @property
    def voiture(self):
        return self.has_deplacement("voiture")

    @property
    def velo(self):
        return self.has_deplacement("velo")

    @property
    def transport_en_commun(self):
        return self.has_deplacement("tec")

    def has_activite(self, activite):
        return self.activites and activite in self.activites

    @property
    def criteres(self):
        liste_criteres = ["menage", "bricolage", "jardinage", "velo", "transport_en_commun",
            "voiture", "sport"]
        return set([critere for critere in liste_criteres
                if getattr(self, critere)])

    @property
    def bricolage(self):
        return self.has_activite("bricolage")

    @property
    def menage(self):
        return self.has_activite("menage")

    @property
    def jardinage(self):
        return self.has_activite("jardinage")

    @property
    def sport(self):
        return self.has_activite("sport")

    @property
    def personne_sensible(self):
        if type(self.population) != list:
            return False
        return "pathologie_respiratoire" in self.population\
                or "allergie_pollens" in self.population\
                or self.has_enfants

    @hybrid_property
    def allergie_pollens(self):
        return type(self.population) == list and "allergie_pollens" in self.population
    @allergie_pollens.setter
    def allergie_pollens(self, value):
        if not type(self.population) == list:
            self.population = []
        if value and not "allergie_pollens" in self.population:
            self.population.append("allergie_pollens")
        elif not value and "allergie_pollens" in self.population:
            self.population.remove("allergie_pollens")
        flag_modified(self, 'population')

    @hybrid_property
    def pathologie_respiratoire(self):
        return type(self.population) == list and "pathologie_respiratoire" in self.population
    @pathologie_respiratoire.setter
    def pathologie_respiratoire(self, value):
        if not type(self.population) == list:
            self.population = []
        if value and not "pathologie_respiratoire" in self.population:
            self.population += ["pathologie_respiratoire"]
        elif not value and "pathologie_respiratoire" in self.population:
            self.population.remove("pathologie_respiratoire")
        flag_modified(self, 'population')

    @property
    def has_enfants(self):
        return self.enfants == 'oui'

    def set_cache_api_commune(self):
        if not self.ville_insee:
            return
        r = requests.get(f'https://geo.api.gouv.fr/communes/{self.ville_insee}',
            params={
                "fields": "nom,centre,region,codesPostaux,departement",
                "format": "json",
                "geometry": "centre"
            }
        )
        self._cache_api_commune = r.json()
        db.session.add(self)
        db.session.commit()

    @property
    def cache_api_commune(self):
        if not self.ville_insee:
            return {}
        if not self._cache_api_commune:
            self.set_cache_api_commune()
        return self._cache_api_commune

    def cache_api_commune_get(self, key, default_value=None):
        if self._cache_api_commune and not key in self._cache_api_commune:
            self._cache_api_commune = None
        return self.cache_api_commune.get(key, default_value)

    @hybrid_property
    def ville_insee(self):
        return self._ville_insee
    @ville_insee.setter
    def ville_insee(self, value):
        self._ville_insee = value
        self.set_cache_api_commune()

    @property
    def ville_centre(self):
        return self.cache_api_commune_get('centre')

    @property
    def ville_nom(self):
        return self.cache_api_commune_get('nom')

    @property
    def ville_codes_postaux(self):
        return self.cache_api_commune_get('codesPostaux')

    @property
    def region_name(self):
        return self.cache_api_commune_get('region', {}).get('nom')

    @property
    def departement(self):
        return self.cache_api_commune_get('departement', {})

    @property
    def is_active(self):
        return self.deactivation_date is None or self.deactivation_date > date.today()

    def last_month_newsletters(self):
        from ecosante.newsletter.models import NewsletterDB

        last_month = date.today() - timedelta(days=30)

        query_sent_nl = db.session\
            .query(func.max(NewsletterDB.id))\
            .filter(
                NewsletterDB.date>=last_month,
                NewsletterDB.inscription_id==self.id
            )\
            .group_by(
                NewsletterDB.date
            ).order_by(
                NewsletterDB.date.desc()
            )
        return db.session\
            .query(NewsletterDB)\
            .filter(NewsletterDB.id.in_(query_sent_nl))\
            .all()

    @classmethod
    def active_query(cls):
        return db.session.query(cls)\
            .filter(or_(Inscription.deactivation_date == None, Inscription.deactivation_date > date.today()))\
            .filter(Inscription.ville_insee.isnot(None))

    def unsubscribe(self):
        from ecosante.inscription.tasks.send_unsubscribe import send_unsubscribe, send_unsubscribe_error
        self.deactivation_date = date.today()
        db.session.add(self)
        db.session.commit()
        send_unsubscribe.apply_async(
            (self.mail,),
            link_error=send_unsubscribe_error.s()
        )

    @classmethod
    def generate_csv(cls):
        yield generate_line([
            'region',
            'ville',
            'deplacement',
            'activites',
            'pathologie_respiratoire',
            'allergie_pollens',
            'enfants',
            'diffusion',
            'mail',
            'frequence',
            'date_inscription',
            'deactivation_date'
        ])
        for inscription in cls.active_query().all():
            yield inscription.csv_line()
    
    def csv_line(self):
        return generate_line([
            self.region_name,
            self.ville_nom,
            self.deplacement,
            self.activites,
            self.pathologie_respiratoire,
            self.allergie_pollens,
            self.enfants,
            self.diffusion,
            self.mail,
            self.frequence,
            self.date_inscription,
            self.deactivation_date
        ])

    @classmethod
    def export_geojson(cls):
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": [],
                    "geometry": i.ville_centre
                }
                for i in cls.active_query().all()
            ]
        }

    @classmethod
    def query_inactive_accounts(cls):
        return db.session.query(cls)\
            .filter(
                cls.deactivation_date != None,
                cls.deactivation_date <= (date.today() - timedelta(days=30))
            )

    @classmethod
    def deactivate_accounts(cls):
        r = cls.query_inactive_accounts()\
            .filter(cls.mail != None)\
            .update({"mail": None})
        db.session.commit()
        return r