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
BuildRequires:  systemd
BuildRequires:  zeromq
%{?systemd_requires}
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

%description
The implementation of the DCI control server API.

%prep -a
%autosetup -n %{name}-%{version}

%build
%py2_build

%install
%py2_install
install -d %{buildroot}/%{_datarootdir}/dci-api
install -d %{buildroot}%{_sysconfdir}/dci-api
# NOTE(Gonéri): Preserve the original location of the wsgi.py file
%{__ln_s} %{python2_sitelib}/dci/wsgi.py %{buildroot}/%{_datarootdir}/dci-api/wsgi.py
# NOTE(Gonéri): Preserve the content of the configuration file when we
# reinstall the package
mv %{buildroot}/%{python2_sitelib}/dci/settings.py %{buildroot}/%{_sysconfdir}/dci-api
%{__ln_s} %{_sysconfdir}/dci-api/settings.py %{buildroot}/%{python2_sitelib}/dci/settings.py
rm -rf %{buildroot}/%{python2_sitelib}/sample
install -p -D -m 644 dci/systemd/dci-worker.service %{buildroot}%{_unitdir}/dci-worker.service

%files
%{_bindir}/dci-dbsync
%{_bindir}/dci-dbinit
%{_bindir}/dci-purge-swift-components
%license LICENSE
%doc
%{python2_sitelib}/dci
%{python2_sitelib}/*.egg-info
%{_unitdir}
%config(noreplace) %{_sysconfdir}/dci-api/settings.py
%{_datarootdir}/dci-api/wsgi.py
# NOTE(Gonéri): the content of settings.py is likely to evolve.
# We don't want to end up with outdated cache on the hard drive.
%exclude %{_sysconfdir}/dci-api/settings.py?
%exclude %{python2_sitelib}/dci/settings.py?

%changelog
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
