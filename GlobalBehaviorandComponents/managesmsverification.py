import logging

# import functions
from flask import render_template, url_for, redirect, session, request, json
from flask import Blueprint

from utils.okta import OktaAdmin
from utils.okta import OktaAuth
from utils.udp import SESSION_INSTANCE_SETTINGS_KEY, get_app_vertical, apply_remote_config
from utils.email import Email

from GlobalBehaviorandComponents.validation import is_authenticated, get_userinfo

logger = logging.getLogger(__name__)

# set blueprint
gbac_managesmsverification_bp = Blueprint('gbac_managesmsverification_bp', __name__, template_folder='templates', static_folder='static', static_url_path='static')


# Required for Registration Page
@gbac_managesmsverification_bp.route("/managesmsverification")
@apply_remote_config
@is_authenticated
def managesmsverification_bp():
    logger.debug("managesmsverification")
    user_info = get_userinfo()
    return render_template(
        "/managesmsverification.html",
        templatename=get_app_vertical(),
        user_info=get_userinfo(),
        config=session[SESSION_INSTANCE_SETTINGS_KEY],
        _scheme=session[SESSION_INSTANCE_SETTINGS_KEY]["app_scheme"])


@gbac_managesmsverification_bp.route("/send-user", methods=["POST"])
@apply_remote_config
def gbac_senduser_completion():
    logger.debug("gbac_senduser_completion()")

    firstName = request.form.get('firstname')
    lastName = request.form.get('lastname')

    okta_admin = OktaAdmin(session[SESSION_INSTANCE_SETTINGS_KEY])
    user_response = ""
    message = ""
    email = ""
    login = ""

    user_response = okta_admin.get_user_list_by_search("profile.firstName eq \"" + firstName + "\" and profile.lastName eq \"" + lastName + "\" &limit=1")

    if user_response:
        logger.debug("*********************************")
        login = user_response[0]['profile']['login']
        user_id = user_response[0]['id']
        logger.debug("*********************************")
        logger.debug(user_id)
        factors = okta_admin.list_enrolled_factors(user_id)
        logger.debug("*********************************")
        logger.debug(factors)
        factor_id = factors[0]['id']
        logger.debug("*********************************")
        logger.debug(factor_id)
        logger.debug("*********************************")
        okta_admin.send_push(user_id, factor_id)
        
        #okta_admin.verify_push(user_id, factor_id)

        recipients = []
        recipients.append({"address": user_response[0]["profile"]["email"]})
        logger.debug(user_response)

        emailLogin(recipients, login)

        #message = "The requested username was found and an SMS message is being sent to: " + user_response[0]["profile"]["firstName"] + " " + user_response[0]["profile"]["lastName"] + " at the following phone number: " + user_response[0]["profile"]["mobilePhone"]
        message = "The requested username " + user_response[0]["profile"]["email"] + " was found and a push message is being sent to: " + user_response[0]["profile"]["firstName"] + " " + user_response[0]["profile"]["lastName"] + " on their registered device"
    else:
        message = "The requested username was not found. Please try again."

    return redirect(
        url_for(
            "gbac_managesmsverification_bp.managesmsverification_bp",
            _external="True",
            _scheme=session[SESSION_INSTANCE_SETTINGS_KEY]["app_scheme"],
            email=email,
            message=message))


def emailLogin(recipient, username):
    logger.debug("emailRegistration()")

    subject = "Verification code"

    message = """
        Support has requested and SMS code be sent to you for verification. <br /><br /><br />Your SMS code is: {username}
        <br /><br /><br />If you did not request to retrieve
         your username, please contact us at your earliest convenience.
        """.format(username=username)

    test = Email.send_mail(subject=subject, message=message, recipients=recipient)
    logger.debug(test)


