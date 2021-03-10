from . import FormInscription, FormPersonnalisation
from ecosante.utils.form import BaseForm, MultiCheckboxField
from wtforms import ValidationError
import requests

class FormPremiereEtape(BaseForm):
    class Meta:
        csrf = False
    mail = FormInscription.mail


class FormDeuxiemeEtape(BaseForm):
    class Meta:
        csrf = False

    ville_insee = FormInscription.ville_insee
    deplacement = FormPersonnalisation.deplacement
    activites = MultiCheckboxField(
        choices=[('jardinage', ''), ('bricolage', ''), ('menage', ''), ('sport', ''), ('aucun', '')]
    )
    pathologie_respiratoire =  FormPersonnalisation.pathologie_respiratoire
    allergie_pollen = FormPersonnalisation.allergie_pollen
    animaux_domestiques = MultiCheckboxField(choices=[('chat', ''), ('chien', ''), ('aucun', '')])
    chauffage = MultiCheckboxField(choices=[('bois', ''), ('fioul', ''), ('appoint', ''), ('aucun', '')])
    connaissance_produit = MultiCheckboxField(
        choices=[
            ('medecin', ''),
            ('association', ''),
            ('reseaux_sociaux', ''),
            ('publicitie', ''),
            ('ami', ''),
            ('autrement', '')
    ])

    def validate_ville_insee(form, field):
        r = requests.get(f'https://geo.api.gouv.fr/communes/{field.data}')
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            raise ValidationError("Unable to get ville")
