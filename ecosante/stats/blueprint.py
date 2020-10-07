from flask import current_app, render_template, Blueprint
from ecosante.inscription.models import Inscription, db
from ecosante.avis.models import Avis
from ecosante.avis.forms import Form
from sqlalchemy import func
from calendar import month_name, different_locale
import json

def get_month_name(month_no, locale):
    with different_locale(locale):
        return month_name[month_no]


bp = Blueprint("stats", __name__, template_folder='templates', url_prefix='/stats')

@bp.route('/')
def stats():
    g = func.date_trunc('month', Inscription.date_inscription)
    subscriptions = {
        f"{get_month_name(v[0].month, 'fr_FR.utf8')} {v[0].year}": v[1]
        for v in
        db.session.query(g, func.count(Inscription.id)).group_by(g).order_by(g).all()
    }
    decouverte_labels = {v[0]: v[1] for v in Form.decouverte.kwargs["choices"]}
    decouverte_unnest_query = db.session.query(func.unnest(Avis.decouverte).label('d')).subquery()
    decouverte_col = decouverte_unnest_query.c.d

    decouverte = {
        decouverte_labels[v[0]]: v[1]
        for v in
        db.session.query(decouverte_col, func.count('*')).group_by(decouverte_col).order_by(decouverte_col).all()
    }
    nb_reponses = Avis.query.count()
    nb_satisfaits = Avis.query.filter(Avis.recommandabilite > 8).count()
    return render_template(
        'stats.html', 
        actifs=Inscription.query.count(),
        subscriptions=json.dumps(subscriptions),
        media=json.dumps({
            "SMS": Inscription.query.filter_by(diffusion='sms').count(),
            "Mail": Inscription.query.filter_by(diffusion='mail').count()
        }),
        frequence=json.dumps({
            'Tous les jours': Inscription.query.filter_by(frequence='quotidien').count(),
            "Lorsque la qualité de l'air est mauvaise": Inscription.query.filter_by(frequence='pollution').count()
        }),
        nb_reponses=nb_reponses,
        nb_satisfaits=nb_satisfaits,
        decouverte=json.dumps(decouverte)
    )

