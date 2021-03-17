from flask import current_app
from datetime import datetime
from uuid import uuid4
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from ecosante.newsletter.models import Newsletter, NewsletterDB, Inscription
from ecosante.extensions import db, sib, celery
from ecosante.utils import send_log_mail

def get_all_contacts(limit=100):
    contacts_api = sib_api_v3_sdk.ContactsApi(sib)
    contacts = []
    offset = 0
    while True:
        result = contacts_api.get_contacts(limit=100, offset=offset)
        contacts += result.contacts
        if len(result.contacts) < limit:
            break
        offset += limit
    return contacts

def get_blacklisted_contacts():
    return [c for c in get_all_contacts() if c['emailBlacklisted'] or c['smsBlacklisted']]

def deactivate_contacts():
    for contact in get_blacklisted_contacts():
        db_contact = Inscription.active_query().filter(Inscription.mail==contact['email']).first()
        if not db_contact or not db_contact.is_active:
            continue
        db_contact.unsubscribe()

def import_and_send(task, seed, preferred_reco, remove_reco):
    task.update_state(
        state='STARTED',
        meta={
            "progress": 0,
            "details": "Prise en compte de la désincription des membres"
        }
    )
    deactivate_contacts()
    task.update_state(
        state='STARTED',
        meta={
            "progress": 0,
            "details": "Suppression des anciennes listes"
        }
    )
    list_ids_to_delete = get_lists_ids_to_delete()
    contacts_api = sib_api_v3_sdk.ContactsApi(sib)
    for i, list_id in enumerate(list_ids_to_delete, 1):
        contacts_api.delete_list(list_id)
        task.update_state(
            state='STARTED',
            meta={
                "progress": 0,
                "details": f"Suppression des anciennes listes ({i}/{len(list_ids_to_delete)})"
            }
        )
    task.update_state(
        state='STARTED',
        meta={
            "progress": 0,
            "details": "Constitution de la liste"
        }
    )
    newsletters = list(
        map(
            NewsletterDB,
            Newsletter.export(
                preferred_reco=preferred_reco,
                user_seed=seed,
                remove_reco=remove_reco
            )
        )
    )
    task.update_state(
        state='STARTED',
        meta={
            "progress" :0,
            "details": "Construction des listes SIB d'envoi"
        }
    )
    result = import_(task, newsletters, 2)
    if current_app.config['ENV'] == 'production':
        send_email_api = sib_api_v3_sdk.EmailCampaignsApi(sib)
        send_email_api.send_email_campaign_now(result["email_campaign_id"])
        task.update_state(
            state='STARTED',
            meta={
                "progress": 99,
                "details": "Envoi de la liste email",
                "email_campaign_id": result['email_campaign_id'],
                "sms_campaign_id": result['sms_campaign_id']
            }
        )
        send_sms_api = sib_api_v3_sdk.SMSCampaignsApi(sib)
        send_sms_api.send_sms_campaign_now(result["sms_campaign_id"])
        task.update_state(
            state='STARTED',
            meta={
                "progress": 100,
                "details": "Envoi de la liste email",
                "email_campaign_id": result['email_campaign_id'],
                "sms_campaign_id": result['sms_campaign_id']
            }
        )
    result['progress'] = 100
    db.session.commit()
    return result

def import_(task, newsletters, overhead=0):
    email_campaign_id = None,
    sms_campaign_id = None
    errors = []
    
    lists = dict()
    now = datetime.now()
    total_nb_requests = 4 + len(newsletters) + overhead
    nb_requests = 0
    lists_api = sib_api_v3_sdk.ListsApi(sib)
    for format in ["sms", "mail"]:
        r = lists_api.create_list(
            sib_api_v3_sdk.CreateList(
                name=f'{now} - {format}',
                folder_id=os.getenv('SIB_FOLDERID', 5)
            )
        )
        lists[format] = r.id
        nb_requests += 1
        task.update_state(
            state='STARTED',
            meta={
                "progress": (nb_requests/total_nb_requests)*100,
                "details": f"Création de la liste {format}"
            }
        )

    contact_api = sib_api_v3_sdk.ContactsApi(sib)
    for i, nl in enumerate(newsletters):
        if nl.label is None:
            errors.append({
                "type": "no_air_quality",
                "nl": nl,
                "region": nl.inscription.cache_api_commune['region']['nom'],
                "ville": nl.inscription.ville_name,
                "insee": nl.inscription.ville_insee
            })
            current_app.logger.error(f"No qai for {nl.inscription.mail}")
        else:
            try:
                if current_app.config['ENV'] == 'production':
                    contact_api.update_contact(
                        nl.inscription.mail,
                        sib_api_v3_sdk.UpdateContact(
                            attributes=nl.attributes(),
                            list_ids=[lists[nl.inscription.diffusion]]
                        )
                    )
            except ApiException as e:
                current_app.logger.error(f"Error updating {nl.inscription.mail}")
                current_app.logger.error(e)
            current_app.logger.info(f"Mise à jour de {nl.inscription.mail}")
        nb_requests += 1
        task.update_state(
            state='STARTED',
            meta={
                "progress": (nb_requests/total_nb_requests)*100,
                "details": f"Mise à jour des contacts {i}/{len(newsletters)}"
            }
        )
        db.session.add(nl)
    db.session.commit()

    email_campaign_api = sib_api_v3_sdk.EmailCampaignsApi(sib)
    if current_app.config['ENV'] == 'production':
        r = email_campaign_api.create_email_campaign(
            sib_api_v3_sdk.CreateEmailCampaign(
                sender = sib_api_v3_sdk.CreateEmailCampaignSender(
                    name="L'équipe Recosanté",
                    email="newsletter@recosante.beta.gouv.fr"
                ),
                name = f'{now}',
                template_id = os.getenv('SIB_EMAIL_TEMPLATE_ID', 226),
                subject = "Vos recommandations Recosanté",
                reply_to = "newsletter@recosante.beta.gouv.fr",
                recipients = sib_api_v3_sdk.CreateEmailCampaignRecipients(
                    list_ids=[lists['mail']]
                ),
                header="Aujourd'hui, la qualité de l'air autour de chez vous est…"
            )
        )
        email_campaign_id = r.id
    else:
        email_campaign_id = 0
    nb_requests += 1
    task.update_state(
        state='STARTED',
        meta={
            "progress": (nb_requests/total_nb_requests)*100,
            "details": f"Création de la campagne mail",
            "email_campaign_id": email_campaign_id
        }
    )

    polluants = ""
    sms_campaign_api = sib_api_v3_sdk.SMSCampaignsApi(sib)
    if current_app.config['ENV'] == 'production':
        r = sms_campaign_api.create_sms_campaign(
            sib_api_v3_sdk.CreateSmsCampaign(
                name = f'{now}',
                sender = "Ecosante",
                content =
    """Aujourd'hui l'indice de la qualité de l'air à {VILLE} est {QUALITE_AIR}
    Plus d'information : {LIEN_AASQA}
    {RECOMMANDATION}
    STOP au [STOP_CODE]
    """ if not polluants else """Indice qualité de l’air à {VILLE} : {QUALITE_AIR}
    Épisode de pollution {POLLUANT}
    Recommandations sanitaires : {LIEN_RECOMMANDATIONS_ALERTE}
    """,
                recipients = sib_api_v3_sdk.CreateSmsCampaignRecipients(
                    list_ids = [lists['sms']]
                )
            )
        )
        sms_campaign_id = r.id
    else:
        sms_campaign_id = 0
    nb_requests += 1
    task.update_state(
        state='STARTED',
        meta={
            "progress": (nb_requests/total_nb_requests)*100,
            "details": f"Création de la campagne SMS",
            "email_campaign_id": email_campaign_id,
            "sms_campaign_id": sms_campaign_id
        }
    )
    return {
        "state": "STARTED",
        "progress": (nb_requests/total_nb_requests)*100,
        "details": "Terminé",
        "email_campaign_id": email_campaign_id,
        "sms_campaign_id": sms_campaign_id,
        "errors": errors
    }

def format_errors(errors):
    if not errors:
        return ''
    r = ''
    r2 = ''
    regions = dict()
    for error in errors:
        if error['type'] == 'no_air_quality':
            r += f"Pas de qualité de l’air pour la ville de {error['ville']} ({error['insee']}) région: '{error['region']}'\n"
            r2 += f"{error['ville']}, {error['insee']}, {error['region']}\n"
            regions.setdefault(error['region'], 0)
            regions[error['region']] += 1
    r += '\n'
    for region, i in regions.items():
        r += f'La région {region} a eu {i} erreurs\n'
    r += '\n'
    r += r2
    return r

@celery.task(bind=True)
def import_send_and_report(self):
    new_task_id = str(uuid4())
    self.update_state(
        state='STARTED',
        meta={
            "progress": 0,
            "details": f"Lancement de la tache: '{new_task_id}'",
        }
    )
    result = import_and_send(self, str(uuid4()), None, [])
    errors = format_errors(result['errors'])
    body = """
Bonjour,
Il n’y a pas eu d’erreur lors de l’envoi de la newsletter
Bonne journée !
""" if not errors else f"""
Bonjour,
Il y a eu des erreurs lors de l’envoi de la newsletter :
{errors}

Bonne journée
"""
    send_log_mail("Rapport d’envoi de la newsletter", body, name="Rapport recosante", email="rapport-envoi@recosante.beta.gouv.fr")
    self.update_state(
        state='SUCESS',
        meta={
            "progress": 100,
            "details": f"Fin",
        }
    )
    return result

def get_lists_ids_to_delete():
    api_instance = sib_api_v3_sdk.ContactsApi(sib)
    offset = 10
    api_response = api_instance.get_lists(limit=10, offset=offset)
    ids = []
    while True:
        ids = ids + [r['id'] for r in api_response.lists]
        if not api_response.lists:
            break
        offset += 10
        api_response = api_instance.get_lists(limit=10, offset=offset)
    return ids