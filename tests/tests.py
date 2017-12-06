# -*- coding: utf-8 -*-
"""
    :copyright:
        (c) 2017 by Tobias dpausp
        (c) 2016 by Armin Ronacher, Daniel Neuhäuser and contributors.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from pytz import timezone, UTC
from babel import support, Locale
import morepath
import pytest
from pytest import fixture, yield_fixture
import webob.request

import more.babel_i18n as babel_ext
from more.babel_i18n.core import BabelApp
from more.babel_i18n.request import BabelRequest

text_type = str


@fixture
def app():
    class TestApp(BabelApp):
        def test_request(self):
            environ = webob.request.BaseRequest.blank('/').environ
            request = BabelRequest(environ, self)
            return request

    babel_settings = {
        'configure_jinja': False
    }
    morepath.autoscan()
    TestApp.init_settings(dict(babel_i18n=babel_settings))
    TestApp.commit()

    app = TestApp()
    app.babel_init()
    return app


@fixture
def request(app):
    return app.test_request()


@fixture
def i18n(app):
    return app.test_request().i18n


@fixture
def babel(app):
    return app.babel


class TestDateFormatting:

    def test_basics(self, i18n):
        d = datetime(2010, 4, 12, 13, 46)
        delta = timedelta(days=6)

        assert i18n.format_datetime(d) == 'Apr 12, 2010, 1:46:00 PM'
        assert i18n.format_date(d) == 'Apr 12, 2010'
        assert i18n.format_time(d) == '1:46:00 PM'
        assert i18n.format_timedelta(delta) == '1 week'
        assert i18n.format_timedelta(delta, threshold=1) == '6 days'

    def test_basics_with_timezone(self, app, i18n):
        app.settings.babel_i18n.default_timezone = 'Europe/Vienna'
        d = datetime(2010, 4, 12, 13, 46)

        assert i18n.format_datetime(d) == 'Apr 12, 2010, 3:46:00 PM'
        assert i18n.format_date(d) == 'Apr 12, 2010'
        assert i18n.format_time(d) == '3:46:00 PM'

    def test_basics_with_timezone_and_locale(self, app, i18n):
        app.settings.babel_i18n.default_locale = 'de_DE'
        app.settings.babel_i18n.default_timezone = 'Europe/Vienna'
        d = datetime(2010, 4, 12, 13, 46)

        assert i18n.format_datetime(d, 'long') == '12. April 2010 um 15:46:00 MESZ'

    def test_custom_formats(self, app, i18n):
        app.settings.babel_i18n.default_locale = 'en_US'
        app.settings.babel_i18n.default_timezone = 'Pacific/Johnston'
        b = app.babel

        b.date_formats['datetime'] = 'long'
        b.date_formats['datetime.long'] = 'MMMM d, yyyy h:mm:ss a'

        b.date_formats['date'] = 'long'
        b.date_formats['date.short'] = 'MM d'

        d = datetime(2010, 4, 12, 13, 46)

        assert i18n.format_datetime(d) == 'April 12, 2010 3:46:00 AM'
        assert i18n._get_format('datetime') == 'MMMM d, yyyy h:mm:ss a'
        # none; returns the format
        assert i18n._get_format('datetime', 'medium') == 'medium'
        assert i18n._get_format('date', 'short') == 'MM d'

    def test_custom_locale_selector(self, app, i18n):
        d = datetime(2010, 4, 12, 13, 46)
        the_locale = 'de_DE'
        the_timezone = 'Europe/Vienna'
        b = app.babel

        @b.localeselector
        def select_locale():
            return the_locale

        @b.timezoneselector
        def select_timezone():
            return the_timezone

        assert i18n.format_datetime(d) == '12.04.2010, 15:46:00'

        i18n.refresh()
        the_timezone = 'UTC'
        the_locale = 'en_US'

        assert i18n.format_datetime(d) == 'Apr 12, 2010, 1:46:00 PM'


def test_force_locale(app, i18n):
    b = app.babel

    @b.localeselector
    def select_locale():
        return 'de_DE'

    assert str(i18n.get_locale()) == 'de_DE'
    with i18n.force_locale('en_US'):
        assert str(i18n.get_locale()) == 'en_US'
    assert str(i18n.get_locale()) == 'de_DE'


class TestNumberFormatting:

    def test_basics(self, i18n):
        n = 1099

        assert i18n.format_number(n) == u'1,099'
        assert i18n.format_decimal(Decimal('1010.99')) == u'1,010.99'
        assert i18n.format_currency(n, 'USD') == '$1,099.00'
        assert i18n.format_percent(0.19) == '19%'
        assert i18n.format_scientific(10000) == u'1E4'


class GettextTestCase(unittest.TestCase):

    def test_basics(self):
        app = flask.Flask(__name__)
        babel_ext.Babel(app, default_locale='de_DE')

        with app.test_request_context():
            assert gettext(u'Hello %(name)s!', name='Peter') == 'Hallo Peter!'
            assert ngettext(u'%(num)s Apple', u'%(num)s Apples', 3) == u'3 Äpfel'  # noqa
            assert ngettext(u'%(num)s Apple', u'%(num)s Apples', 1) == u'1 Apfel'  # noqa

            assert pgettext(u'button', u'Hello %(name)s!', name='Peter') == 'Hallo Peter!'  # noqa
            assert pgettext(u'dialog', u'Hello %(name)s!', name='Peter') == 'Hallo Peter!'  # noqa
            assert pgettext(u'button', u'Hello Guest!') == 'Hallo Gast!'
            assert npgettext(u'shop', u'%(num)s Apple', u'%(num)s Apples', 3) == u'3 Äpfel'  # noqa
            assert npgettext(u'fruits', u'%(num)s Apple', u'%(num)s Apples', 3) == u'3 Äpfel'  # noqa

    def test_template_basics(self):
        app = flask.Flask(__name__)
        babel_ext.Babel(app, default_locale='de_DE')

        def t(x):
            return flask.render_template_string('{{ %s }}' % x)

        with app.test_request_context():
            assert t("gettext('Hello %(name)s!', name='Peter')") == 'Hallo Peter!'  # noqa
            assert t("ngettext('%(num)s Apple', '%(num)s Apples', 3)") == u'3 Äpfel'  # noqa
            assert t("ngettext('%(num)s Apple', '%(num)s Apples', 1)") == u'1 Apfel'  # noqa
            assert flask.render_template_string('''
                {% trans %}Hello {{ name }}!{% endtrans %}
            ''', name='Peter').strip() == 'Hallo Peter!'
            assert flask.render_template_string('''
                {% trans num=3 %}{{ num }} Apple
                {%- pluralize %}{{ num }} Apples{% endtrans %}
            ''', name='Peter').strip() == u'3 Äpfel'

    def test_lazy_gettext(self):
        app = flask.Flask(__name__)
        babel_ext.Babel(app, default_locale='de_DE')
        yes = lazy_gettext(u'Yes')
        with app.test_request_context():
            assert text_type(yes) == 'Ja'
        app.config['BABEL_DEFAULT_LOCALE'] = 'en_US'
        with app.test_request_context():
            assert text_type(yes) == 'Yes'

    def test_no_formatting(self):
        """
        Ensure we don't format strings unless a variable is passed.
        """
        app = flask.Flask(__name__)
        babel_ext.Babel(app)

        with app.test_request_context():
            assert gettext(u'Test %s') == u'Test %s'
            assert gettext(u'Test %(name)s', name=u'test') == u'Test test'
            assert gettext(u'Test %s') % 'test' == u'Test test'

    def test_lazy_gettext_defaultdomain(self):
        app = flask.Flask(__name__)
        domain = babel_ext.Domain(domain='test')
        babel_ext.Babel(app, default_locale='de_DE', default_domain=domain)
        first = lazy_gettext('first')
        domain_first = domain.lazy_gettext('first')

        with app.test_request_context():
            assert text_type(domain_first) == 'erste'
            assert text_type(first) == 'erste'

        app.config['BABEL_DEFAULT_LOCALE'] = 'en_US'
        with app.test_request_context():
            assert text_type(first) == 'first'
            assert text_type(domain_first) == 'first'

    def test_lazy_pgettext(self):
        app = flask.Flask(__name__)
        domain = babel_ext.Domain(domain='messages')
        babel_ext.Babel(app, default_locale='de_DE')
        first = lazy_pgettext('button', 'Hello Guest!')
        domain_first = domain.lazy_pgettext('button', 'Hello Guest!')

        with app.test_request_context():
            assert text_type(domain_first) == 'Hallo Gast!'
            assert text_type(first) == 'Hallo Gast!'

        app.config['BABEL_DEFAULT_LOCALE'] = 'en_US'
        with app.test_request_context():
            assert text_type(first) == 'Hello Guest!'
            assert text_type(domain_first) == 'Hello Guest!'

    def test_no_ctx_gettext(self):
        app = flask.Flask(__name__)
        babel_ext.Babel(app, default_locale='de_DE')
        domain = babel_ext.get_domain()
        assert domain.gettext('Yes') == 'Yes'

    def test_list_translations(self):
        app = flask.Flask(__name__)
        b = babel_ext.Babel(app, default_locale='de_DE')

        # an app_context is automatically created when a request context
        # is pushed if necessary
        with app.test_request_context():
            translations = b.list_translations()
            assert len(translations) == 1
            assert str(translations[0]) == 'de'

    def test_get_translations(self):
        app = flask.Flask(__name__)
        babel_ext.Babel(app, default_locale='de_DE')
        domain = babel_ext.get_domain()  # using default domain

        # no app context
        assert isinstance(domain.get_translations(), support.NullTranslations)

    def test_domain(self):
        app = flask.Flask(__name__)
        babel_ext.Babel(app, default_locale='de_DE')
        domain = babel_ext.Domain(domain='test')

        with app.test_request_context():
            assert domain.gettext('first') == 'erste'
            assert babel_ext.gettext('first') == 'first'

    def test_as_default(self):
        app = flask.Flask(__name__)
        babel_ext.Babel(app, default_locale='de_DE')
        domain = babel_ext.Domain(domain='test')

        with app.test_request_context():
            assert babel_ext.gettext('first') == 'first'
            domain.as_default()
            assert babel_ext.gettext('first') == 'erste'

    def test_default_domain(self):
        app = flask.Flask(__name__)
        domain = babel_ext.Domain(domain='test')
        babel_ext.Babel(app, default_locale='de_DE', default_domain=domain)

        with app.test_request_context():
            assert babel_ext.gettext('first') == 'erste'

    def test_multiple_apps(self):
        app1 = flask.Flask(__name__)
        babel_ext.Babel(app1, default_locale='de_DE')

        app2 = flask.Flask(__name__)
        babel_ext.Babel(app2, default_locale='de_DE')

        with app1.test_request_context():
            assert babel_ext.gettext('Yes') == 'Ja'
            assert 'de_DE' in app1.extensions["babel"].domain.cache

        with app2.test_request_context():
            assert 'de_DE' not in app2.extensions["babel"].domain.cache


class IntegrationTestCase(unittest.TestCase):
    def test_configure_jinja(self):
        app = flask.Flask(__name__)
        babel_ext.Babel(app, configure_jinja=False)
        assert not app.jinja_env.filters.get("scientificformat")

    def test_get_state(self):
        # app = None; app.extensions = False; babel = False; silent = True;
        assert get_state(silent=True) is None

        app = flask.Flask(__name__)
        with pytest.raises(RuntimeError):
            with app.test_request_context():
                # app = app; silent = False
                # babel not in app.extensions
                get_state()

        # same as above, just silent
        with app.test_request_context():
            assert get_state(app=app, silent=True) is None

        babel_ext.Babel(app)
        with app.test_request_context():
            # should use current_app
            assert get_state(app=None, silent=True) == app.extensions['babel']

    def test_get_locale(self):
        assert babel_ext.get_locale() is None

        app = flask.Flask(__name__)
        babel_ext.Babel(app)
        with app.app_context():
            assert babel_ext.get_locale() == Locale.parse("en")

    def test_get_timezone_none(self):
        assert babel_ext.get_timezone() is None

        app = flask.Flask(__name__)
        b = babel_ext.Babel(app)

        @b.timezoneselector
        def tz_none():
            return None
        with app.test_request_context():
            assert babel_ext.get_timezone() == UTC

    def test_get_timezone_vienna(self):
        app = flask.Flask(__name__)
        b = babel_ext.Babel(app)

        @b.timezoneselector
        def tz_vienna():
            return timezone('Europe/Vienna')
        with app.test_request_context():
            assert babel_ext.get_timezone() == timezone('Europe/Vienna')

    def test_convert_timezone(self):
        app = flask.Flask(__name__)
        babel_ext.Babel(app)
        dt = datetime(2010, 4, 12, 13, 46)

        with app.test_request_context():
            dt_utc = babel_ext.to_utc(dt)
            assert dt_utc.tzinfo is None

            dt_usertz = babel_ext.to_user_timezone(dt_utc)
            assert dt_usertz is not None


if __name__ == '__main__':
    unittest.main()
