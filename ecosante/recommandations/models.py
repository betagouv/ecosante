from .. import db
import sqlalchemy.types as types
import uuid
import random

class CustomBoolean(types.TypeDecorator):
    impl = db.Boolean

    def process_bind_param(self, value, dialect):
        return 'x' in value.lower()

class Recommandation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recommandabilite = db.Column(db.String)
    recommandation = db.Column(db.String)
    precisions = db.Column(db.String)
    recommandation_format_SMS = db.Column(db.String)
    qa_mauvaise = db.Column(CustomBoolean)
    menage = db.Column(CustomBoolean)
    bricolage = db.Column(CustomBoolean)
    chauffage_a_bois = db.Column(CustomBoolean)
    jardinage = db.Column(CustomBoolean)
    balcon_terasse = db.Column(CustomBoolean)
    velo_trott_skate = db.Column(CustomBoolean)
    transport_en_commun = db.Column(CustomBoolean)
    voiture = db.Column(CustomBoolean)
    activite_physique = db.Column(CustomBoolean)
    allergies = db.Column(CustomBoolean)
    enfants = db.Column(CustomBoolean)
    personnes_sensibles = db.Column(CustomBoolean)
    niveau_difficulte = db.Column(db.String)
    autres_conditions = db.Column(db.String)
    sources = db.Column(db.String)
    categorie = db.Column(db.String)
    objectif = db.Column(db.String)


    def is_relevant(self, inscription, qai):
        if not inscription.voiture and self.voiture:
            return False

        if not inscription.sport and self.activite_physique:
            return False

        if not inscription.bricolage and self.bricolage:
            return False

        #Quand la qualité de l'air est mauvaise
        if qai and (qai < 8) and self.qa_mauvaise:
            return False

        return True

    def format(self, inscription):
        return self.recommandation if inscription.diffusion == 'mail' else self.recommandation_format_SMS

    @classmethod
    def shuffled(cls, random_uuid, preferred_reco):
        recommandations = cls.query.filter_by(recommandabilite="Utilisable").all()
        random.shuffle(
            recommandations,
            lambda: 1/(uuid.UUID(random_uuid, version=4).int) if random_uuid else random.random()
        )
        if preferred_reco:
            recommandations = [cls.query.get(preferred_reco)] + recommandations
        return recommandations

    @classmethod
    def get_revelant(cls, recommandations, inscription, qai):
        return next(filter(lambda r: r.is_relevant(inscription, qai), recommandations))