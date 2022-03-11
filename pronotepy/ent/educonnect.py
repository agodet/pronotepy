# type: ignore
from logging import getLogger, DEBUG
import typing

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from ..exceptions import *

log = getLogger(__name__)
log.setLevel(DEBUG)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'
}


@typing.no_type_check
def educonnect(url: str, session, username: str, password: str) -> requests.Response:
    payload = {
        'j_username': username,
        'j_password': password,
        '_eventId_proceed': ''
    }
    response = session.post(url, headers=HEADERS, data=payload)
    # 2nd SAML Authentication
    soup = BeautifulSoup(response.text, 'html.parser')
    input_SAMLResponse = soup.find("input", {"name": "SAMLResponse"})
    if not input_SAMLResponse:
        return

    payload = {
        "SAMLResponse": input_SAMLResponse["value"]
        }

    input_relayState = soup.find("input", {"name": "RelayState"})
    if input_relayState:
        payload["RelayState"] = input_relayState['value']

    response = session.post(soup.find("form")["action"], headers=HEADERS, data=payload)
    return response


def ac_rennes(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT ac Rennes Toutatice.fr

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    # Toutatice required URL
    toutatice_url = 'https://www.toutatice.fr/portail/auth/MonEspace'
    toutatice_login = 'https://www.toutatice.fr/wayf/Ctrl'
    toutatice_auth = 'https://www.toutatice.fr/idp/Authn/RemoteUser'

    session = requests.Session()

    response = session.get(toutatice_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    payload = {
        "entityID": soup.find("input", {"name": "entityID"})["value"],
        "return": soup.find("input", {"name": "return"})["value"],
        "_saml_idp": soup.find("input", {"name": "_saml_idp"})["value"]
        }

    log.debug(f'[ENT Toutatice] Logging in with {username}')
    response = session.post(toutatice_login, data=payload, headers=HEADERS)

    educonnect(response.url, session, username, password)

    params = {
        'conversation': parse_qs(urlparse(response.url).query)['execution'][0],
        'redirectToLoaderRemoteUser': 0,
        'sessionid': session.cookies.get('IDP_JSESSIONID')
        }

    response = session.get(toutatice_auth, headers=HEADERS, params=params)
    soup = BeautifulSoup(response.text, 'xml')

    if soup.find('erreurFonctionnelle'):
        raise(PronoteAPIError('Toutatice ENT (ac_rennes) : ', soup.find('erreurFonctionnelle').text))
    elif soup.find('erreurTechnique'):
        raise(PronoteAPIError('Toutatice ENT (ac_rennes) : ', soup.find('erreurTechnique').text))
    else:
        params = {
            'conversation': soup.find("conversation").text,
            'uidInSession': soup.find("uidInSession").text,
            'sessionid': session.cookies.get('IDP_JSESSIONID')
            }
        t = session.get(toutatice_auth, headers=HEADERS, params=params)

    return session.cookies


def occitanie_montpellier_educonnect(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for Occitanie Montpellier

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    # ENT / PRONOTE required URLs
    ent_login = 'https://cas.mon-ent-occitanie.fr/login'
    # ENT Connection
    session = requests.Session()

    params = {
        'selection': 'MONT-EDU_parent_eleve',
        'submit': 'Valider'
    }

    response = session.get(ent_login, params=params, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    payload = {
        "RelayState": soup.find("input", {"name": "RelayState"})["value"],
        "SAMLRequest": soup.find("input", {"name": "SAMLRequest"})["value"]
        }

    response = session.post(soup.find("form")['action'], data=payload, headers=HEADERS)
    log.debug(f'[ENT Occitanie] Logging in with {username}')

    educonnect(response.url, session, username, password)

    return session.cookies


def ent_auvergnerhonealpe(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for Auvergne Rhone Alpes with Educonnect

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    # ENT / PRONOTE required URLs
    ent_login_page = 'https://cas.ent.auvergnerhonealpes.fr/login?selection=EDU&submit=Valider'

    # ENT Connection
    session = requests.Session()

    # Connection URL specifying the pronote service
    response = session.get(ent_login_page, headers=HEADERS)
    educonnect(response.url, session, username, password)

    return session.cookies


def ac_orleans_tours(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for AC Orleans-Tours

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    # ENT / PRONOTE required URLs
    ent_login_page = 'https://ent.netocentre.fr/cas/login?&idpId=parentEleveEN-IdP'

    # ENT Connection
    session = requests.Session()

    # Connection URL specifying the pronote service
    response = session.get(ent_login_page, headers=HEADERS)
    educonnect(response.url, session, username, password)

    return session.cookies


def monbureaunumerique(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for MonBureauNumerique (Grand Est)

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    # ENT / PRONOTE required URLs
    ent_login_page = 'https://cas.monbureaunumerique.fr/login?selection=EDU'

    # ENT Connection
    session = requests.Session()

    # Connection URL specifying the pronote service
    response = session.get(ent_login_page, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    payload = {
        "RelayState": soup.find("input", {"name": "RelayState"})["value"],
        "SAMLRequest": soup.find("input", {"name": "SAMLRequest"})["value"],
        }

    response = session.post(soup.find("form")['action'], data=payload, headers=HEADERS)
    educonnect(response.url, session, username, password)

    return session.cookies


def ac_reims(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for AC Reims

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    return monbureaunumerique(username, password)


def ent_elyco(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    ent_login_page = 'https://cas3.e-lyco.fr/discovery/WAYF'
    session = requests.Session()

    params = {
        'entityID': 'https://cas3.e-lyco.fr/shibboleth',
        'returnX': 'https://cas3.e-lyco.fr/Shibboleth.sso/Login',
        'returnIDParam': 'entityID',
        'action': 'selection',
        'origin': 'https://educonnect.education.gouv.fr/idp'
    }

    response = session.get(ent_login_page, params=params, headers=HEADERS)
    educonnect(response.url, session, username, password)

    return session.cookies


def eclat_bfc(username: str, password: str) -> requests.cookies.RequestsCookieJar:
    """
    ENT for Eclat BFC

    Parameters
    ----------
    username : str
        username
    password : str
        password

    Returns
    -------
    cookies : cookies
        returns the ent session cookies
    """
    # ENT / PRONOTE required URLs
    ent_login = 'https://cas.eclat-bfc.fr/login'
    # ENT Connection
    session = requests.Session()

    params = {
        'selection': 'EDU',
        'submit': 'Valider'
    }

    response = session.get(ent_login, params=params, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    payload = {
        "RelayState": soup.find("input", {"name": "RelayState"})["value"],
        "SAMLRequest": soup.find("input", {"name": "SAMLRequest"})["value"]
        }

    response = session.post(soup.find("form")['action'], data=payload, headers=HEADERS)
    log.debug(f'[ENT Eclat BFC] Logging in with {username}')

    educonnect(response.url, session, username, password)

    return session.cookies
