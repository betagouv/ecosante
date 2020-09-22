from wtforms import BooleanField, StringField, validators
from wtforms.fields.html5 import EmailField, TelField

from ecosante.utils.form import MultiCheckboxField, OuiNonField, RadioField, BaseForm

class FormInscription(BaseForm):
    ville_entree = StringField('Dans quelle ville vivez-vous', [validators.DataRequired()])
    mail = EmailField(
        'Adresse email',
        [validators.DataRequired(), validators.Email()],
        description='(attention, les mails Ecosanté peut se retrouver dans vos SPAM ou dans le dossier "Promotions" de votre boîte mail !)'
    )
    diffusion = RadioField(
        'Souhaitez-vous recevoir les recommandations par ?',
        [validators.DataRequired()],
        choices=[('mail', 'Email'), ('sms', 'SMS')]
    )
    telephone = TelField(
        'Numéro de téléphone',
        description="(si vous avez choisi l'option d'envoi par SMS)"
    )
    frequence = RadioField(
        'À quelle fréquence souhaitez-vous recevoir les informations ?',
        [validators.DataRequired()],
        description="En selectionnant «lorsque la qualité de l'air est mauvaise» il est possible que vous ne receviez peu ou pas d'alerte Ecosanté. C'est une bonne nouvelle, cela signifie que la qualité de l'air n'est pas mauvaise dans votre région.",
        choices=[
            ('quotidien',  'Tous les jours'),
            ('pollution',  "Lorsque la qualité de l'air est mauvaise")
        ]
    )

class FormPersonnalisation(BaseForm):
    deplacement = MultiCheckboxField(
        'Quel(s) moyen(s) de transport utilisez-vous principalement pour vos déplacements ?',
        choices={
            ('velo', 'Vélo'),
            ('tec', 'Transport en commun'),
            ('voiture', 'Voiture')
        }
    )
    activites = MultiCheckboxField(
        'Pratiquez-vous au moins une fois par semaine les activités suivantes ?',
        choices=[
            ('jardinage', 'Jardinage'),
            ('bricolage', 'Bricolage'),
            ('menage', 'Ménage'),
            ('sport', 'Activité sportive')
        ]
    )
    enfants = OuiNonField('Vivez-vous avec des enfants ?')
    pathologie_respiratoire = OuiNonField('Vivez-vous avec une pathologie respiratoire ?')
    allergie_pollen = OuiNonField('Êtes-vous allergique aux pollens ?')
    fumeur = OuiNonField('Êtes-vous fumeur.euse ?')