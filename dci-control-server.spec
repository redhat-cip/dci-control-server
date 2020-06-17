%if 0%{?rhel} && 0%{?rhel} < 8
%global with_python2 1
%global python_sitelib %{python2_sitelib}
%else
%global with_python3 1
%global python_sitelib %{python3_sitelib}
%endif

Name:           dci-control-server
Version:        0.3.1
Release:        2.VERS%{?dist}
Summary:        DCI control server
License:        ASL 2.0
URL:            https://github.com/redhat-cip/dci-control-server
Source0:        dci-control-server-%{version}.tar.gz
BuildArch:      noarch


Conflicts:      dci-common < %{version}
Obsoletes:      dci-common
Obsoletes:      dci-api < 0.2.2.2
BuildRequires:  net-tools
%if 0%{?with_python2}
BuildRequires:  python2-devel
BuildRequires:  rh-postgresql96-postgresql-devel
BuildRequires:  rh-postgresql96
BuildRequires:  pyOpenSSL
BuildRequires:  python-alembic
BuildRequires:  python-flask
BuildRequires:  python-passlib
BuildRequires:  python-psycopg2
BuildRequires:  python-requests
BuildRequires:  python-rpm-macros
BuildRequires:  python-setuptools
BuildRequires:  python-six
BuildRequires:  python2-sqlalchemy
BuildRequires:  python-sqlalchemy-utils
BuildRequires:  python-tornado
BuildRequires:  python-werkzeug
BuildRequires:  python-zmq
BuildRequires:  python-jwt
BuildRequires:  python-dciauth
BuildRequires:  python2-pytest
BuildRequires:  python2-rpm-macros
BuildRequires:  python2-swiftclient
BuildRequires:  python2-jsonschema
%else
BuildRequires:  python3-devel
BuildRequires:  postgresql-devel
BuildRequires:  postgresql-server
BuildRequires:  python3-pyOpenSSL
BuildRequires:  python3-alembic
BuildRequires:  python3-flask
BuildRequires:  python3-passlib
BuildRequires:  python3-psycopg2
BuildRequires:  python3-requests
BuildRequires:  python3-rpm-macros
BuildRequires:  python3-setuptools
BuildRequires:  python3-six
BuildRequires:  python3-sqlalchemy
BuildRequires:  python3-sqlalchemy-utils
BuildRequires:  python3-tornado
BuildRequires:  python3-werkzeug
BuildRequires:  python3-zmq
BuildRequires:  python3-jwt
BuildRequires:  python3-dciauth
BuildRequires:  python3-pytest
BuildRequires:  python3-rpm-macros
BuildRequires:  python3-swiftclient
BuildRequires:  python3-jsonschema
%endif
BuildRequires:  systemd
BuildRequires:  zeromq
%if 0%{?with_python2}
Requires:       pyOpenSSL
Requires:       python-alembic
Requires:       python-flask
Requires:       python-passlib
Requires:       python-psycopg2
Requires:       python-requests
Requires:       python-six
Requires:       python2-sqlalchemy
Requires:       python-sqlalchemy-utils
Requires:       python-tornado
Requires:       python-werkzeug
Requires:       python-zmq
Requires:       python-jwt
Requires:       python-dciauth
Requires:       python2-swiftclient
Requires:       python2-jsonschema
Requires:       pytz
Requires:       zeromq
%else
Requires:       python3-pyOpenSSL
Requires:       python3-alembic
Requires:       python3-flask
Requires:       python3-passlib
Requires:       python3-psycopg2
Requires:       python3-requests
Requires:       python3-six
Requires:       python3-sqlalchemy
Requires:       python3-sqlalchemy-utils
Requires:       python3-tornado
Requires:       python3-werkzeug
Requires:       python3-zmq
Requires:       python3-jwt
Requires:       python3-dciauth
Requires:       python3-swiftclient
Requires:       python3-jsonschema
Requires:       python3-pytz
%endif
Requires:       zeromq
%{?systemd_requires}

%description
The implementation of the DCI control server API.

%prep -a
%autosetup -n %{name}-%{version}
sed -i "s/==/>=/g" requirements.txt

%build
%if 0%{?with_python2}
%py2_build
%else
%py3_build
%endif

%install
%if 0%{?with_python2}
%py2_install
%else
%py3_install
%endif
install -d %{buildroot}/%{_datarootdir}/dci-api
install -d %{buildroot}%{_sysconfdir}/dci-api
# NOTE(Gonéri): Preserve the original location of the wsgi.py file
%{__ln_s} %{python_sitelib}/dci/wsgi.py %{buildroot}/%{_datarootdir}/dci-api/wsgi.py
# NOTE(Gonéri): Preserve the content of the configuration file when we
# reinstall the package
mv %{buildroot}/%{python_sitelib}/dci/settings.py %{buildroot}/%{_sysconfdir}/dci-api
%{__ln_s} %{_sysconfdir}/dci-api/settings.py %{buildroot}/%{python_sitelib}/dci/settings.py
rm -rf %{buildroot}/%{python_sitelib}/sample
install -p -D -m 644 dci/systemd/dci-worker.service %{buildroot}%{_unitdir}/dci-worker.service

%files
%{_bindir}/dci-dbsync
%{_bindir}/dci-dbinit
%{_bindir}/dci-purge-swift-components
%license LICENSE
%{python_sitelib}/dci
%{python_sitelib}/*.egg-info
%{_unitdir}/dci-worker.service
%config(noreplace) %{_sysconfdir}/dci-api/settings.py
%{_datarootdir}/dci-api/wsgi.py
# NOTE(Gonéri): the content of settings.py is likely to evolve.
# We don't want to end up with outdated cache on the hard drive.
%exclude %{_sysconfdir}/dci-api/settings.py?
%exclude %{python_sitelib}/dci/settings.py?

%changelog
* Mon Jun 15 2020 Haïkel Guémar <hguemar@fedoraproject.org> - 0.3.1-2
- Add EL8 support

* Wed Sep 18 2019 Guillaume Vincent <gvincent@redhat.com> 0.3.1-1
- Use rh-postgresql96

* Mon May 20 2019 Guillaume Vincent <gvincent@redhat.com> 0.3.0-1
- Use python-jsonschema instead of python-voluptuous

* Mon Feb 11 2019 Haïkel Guémar <hguemar@fedoraproject.org> - 0.2.2-2
- Rename dci-api to dci-control-server
- Drop python3 variant subpackage
- Fix systemd requirements

* Tue Jun 12 2018 Guillaume Vincent <gvincent@redhat.com> 0.2.2-1
- Use python-sqlalchemy instead of python-flask-sqlalchemy

* Wed Apr 18 2018 Guillaume Vincent <gvincent@redhat.com> 0.2.1-1
- Use rh-postgresql94 to mimic the db production version

* Fri Mar 2 2018 Yassine Lamgarchal <ylamgarc@redhat.com> 0.2.0-4
- Remove all Elasticsearch related components

* Fri Dec 1 2017 Yassine Lamgarchal <ylamgarc@redhat.com> 0.2.0-3
- Replace dci-esindex by dci-essync

* Thu Oct 05 2017 Yassine Lamgarchal <ylamgarc@redhat.com> 0.2.0-2
- Adding jwt dependency.

* Wed May 10 2017 Yanis Guenane <yguenane@redhat.com> 0.2.0-1
- Bumping to 0.2.0 for CI purposes

* Mon Nov 16 2015 Yanis Guenane <yguenane@redhat.com> 0.1-1
- Initial commit
