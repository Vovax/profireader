from .blueprints import user_bp
from flask import jsonify, make_response, g, session, request, redirect, \
    url_for, render_template, flash
from authomatic.adapters import WerkzeugAdapter
from ..models.users import User
from db_init import db_session
from ..constants.USER_REGISTERED import REGISTERED_WITH_FLIPPED
from ..constants.SOCIAL_NETWORKS import DB_FIELDS, SOC_NET_FIELDS
from flask.ext.login import login_user, logout_user, current_user, \
    login_required
import sqlalchemy.exc as sqlalchemy_exc

from urllib.parse import quote
from ..models.users import User
from ..forms.user import LoginForm, RegistrationForm, ChangePasswordForm, \
    PasswordResetRequestForm, PasswordResetForm, ChangeEmailForm
from .errors import BadDataProvided
from ..utils.email import send_email
#from ..utils import login_required
import json

#def _session_saver():
#    session.modified = True

import re
from authomatic.adapters import WerkzeugAdapter

from flask import redirect, make_response
from flask.ext.login import login_user
from ..constants.SOCIAL_NETWORKS import SOC_NET_NONE


EMAIL_REGEX = re.compile(r'[^@]+@[^@]+\.[^@]+')


#provider_name:
# 0) profireader+
# 1) facebook +-
# 2) linkedin +
# 3) google +
# 4) twitter +
# 5) microsoft +
# 6) yahoo +


@user_bp.route('/signup/', methods=['GET', 'POST'])
def signup():
    # (Andriy) I suppose it is not necessary
    if g.user_init and g.user_init.is_authenticated():
        raise BadDataProvided

    form = RegistrationForm()
    if form.validate_on_submit():  # # pass1 == pass2
        profireader_all = SOC_NET_NONE['PROFIREADER'].copy()
        profireader_all['EMAIL'] = form.email.data
        profireader_all['NAME'] = form.displayname.data
        user = User(
            PROFIREADER_ALL=profireader_all
        )
        user.password = form.password.data  # pass is automatically hashed

        db_session.add(user)
        db_session.commit()
        token = user.generate_confirmation_token()
        send_email(user.profireader_email, 'Confirm Your Account',
                   'auth/email/confirm', user=user, token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('user.login'))
    return render_template('auth/signup.html', form=form, user=g.user_dict)


# read: flask.ext.login
# On a production server, the login route must be made available over
# secure HTTP so that the form data transmitted to the server is en‐
# crypted. Without secure HTTP, the login credentials can be intercep‐
# ted during transit, defeating any efforts put into securing passwords
# in the server.
#
# read this before push!!!: http://flask.pocoo.org/snippets/62/
@user_bp.route('/login/', methods=['GET', 'POST'])
def login():
    # (Andriy) I suppose it is not necessary
    if g.user_init and g.user_init.is_authenticated():
        flash('You are already logged in.')

    form = LoginForm()

    if form.validate_on_submit():
        user = db_session.query(User).\
            filter(User.profireader_email == form.email.data).first()

        if user and user.verify_password(form.password.data):
            login_user(user)
            return redirect(request.args.get('next') or
                            url_for('general.index'))
        flash('Invalid username or password.')
        return redirect(url_for('user.login'))
    return render_template('auth/login.html', form=form, user=g.user_dict)

@user_bp.route('/login/<soc_network_name>', methods=['GET', 'POST'])
def login_soc_network(soc_network_name):
    if g.user_init and g.user_init.is_authenticated():
        raise BadDataProvided

    response = make_response()
    try:
        result = g.authomatic.login(WerkzeugAdapter(request, response),
                                    soc_network_name)
        if result:
            if result.user:
                result.user.update()
                result_user = result.user
                db_fields = DB_FIELDS[soc_network_name.upper()]
                user = db_session.query(User).\
                    filter(getattr(User, db_fields['ID']) == result_user.id)\
                    .first()
                if not user:
                    user = User()
                    for elem in SOC_NET_FIELDS:
                        setattr(user, db_fields[elem],
                                getattr(result_user, elem.lower()))
                    db_session.add(user)
                    db_session.commit()
                session['user_id'] = user.id

                return redirect('/')  # #  http://aprofi.d.ntaxa.com/
            elif result.error:
                redirect_path = '#/?msg={}'.\
                    format(quote(soc_network_name + ' login failed.'))
                return redirect(redirect_path)

    except:
        import sys
        print(sys.exc_info())
        raise
    return response


@user_bp.route('/logout/', methods=['GET'])
@login_required   # Only logged in user can be logged out
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('general.index'))

# ************************************************************************


@user_bp.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('general.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('general.index'))


@user_bp.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('general.index'))


@user_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db_session.add(current_user)
            flash('Your password has been updated.')
            return redirect(url_for('general.index'))
        else:
            flash('Invalid password.')
    return render_template("auth/change_password.html", form=form)


@user_bp.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous():
        return redirect(url_for('general.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash('An email with instructions to reset your password has been '
              'sent to you.')
        return redirect(url_for('user.login'))
    return render_template('auth/reset_password.html', form=form)


@user_bp.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous():
        return redirect(url_for('general.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('general.index'))
        if user.reset_password(token, form.password.data):
            flash('Your password has been updated.')
            return redirect(url_for('user.login'))
        else:
            return redirect(url_for('general.index'))
    return render_template('auth/reset_password.html', form=form)


@user_bp.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your email address',
                       'auth/email/change_email',
                       user=current_user, token=token)
            flash('An email with instructions to confirm your new email '
                  'address has been sent to you.')
            return redirect(url_for('general.index'))
        else:
            flash('Invalid email or password.')
    return render_template("auth/change_email.html", form=form)


@user_bp.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('Your email address has been updated.')
    else:
        flash('Invalid request.')
    return redirect(url_for('general.index'))