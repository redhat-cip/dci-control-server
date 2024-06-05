Name:           dci-control-server
Version:        0.3.4
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
BuildRequires:  python3-jsonschema
BuildRequires:  python3-pyparsing
BuildRequires:  systemd
BuildRequires:  zeromq
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
Requires:       python3-jsonschema
Requires:       python3-pytz
Requires:       python3-boto3
Requires:       python3-pyparsing
Requires:       zeromq
%{?systemd_requires}

%description
The implementation of the DCI control server API.

%prep -a
%autosetup -n %{name}-%{version}
sed -i "s/==/>=/g" requirements.txt

%build
%py3_build

%install
%py3_install
install -d %{buildroot}/%{_datarootdir}/dci-api
install -d %{buildroot}%{_sysconfdir}/dci-api
# NOTE(Gonéri): Preserve the original location of the wsgi.py file
%{__ln_s} %{python3_sitelib}/dci/wsgi.py %{buildroot}/%{_datarootdir}/dci-api/wsgi.py
# NOTE(Gonéri): Preserve the content of the configuration file when we
# reinstall the package
mv %{buildroot}/%{python3_sitelib}/dci/settings.py %{buildroot}/%{_sysconfdir}/dci-api
%{__ln_s} %{_sysconfdir}/dci-api/settings.py %{buildroot}/%{python3_sitelib}/dci/settings.py
rm -rf %{buildroot}/%{python3_sitelib}/sample
install -p -D -m 644 dci/systemd/dci-worker.service %{buildroot}%{_unitdir}/dci-worker.service

%files
%{_bindir}/dci-dbsync
%{_bindir}/dci-dbinit
%license LICENSE
%{python3_sitelib}/dci
%{python3_sitelib}/*.egg-info
%{_unitdir}/dci-worker.service
%config(noreplace) %{_sysconfdir}/dci-api/settings.py
%{_datarootdir}/dci-api/wsgi.py
# NOTE(Gonéri): the content of settings.py is likely to evolve.
# We don't want to end up with outdated cache on the hard drive.
%exclude %{_sysconfdir}/dci-api/settings.py?
%exclude %{python3_sitelib}/dci/settings.py?

%changelog
* Wed Jun 05 2024 Guillaume Vincent <gvincent@redhat.com> - 0.3.4-2
- Drop python 2 support

* Tue Feb 21 2023 Yassine Lamgarchal <ylamgarc@redhat.com> - 0.3.4-1
- Add pyparsing dependency

* Tue Aug 30 2022 Cedric Lecomte <clecomte@redhat.com> - 0.3.3-1
- Remove all swift dependencies

* Thu Jul 07 2022 Guillaume Vincent <gvincent@redhat.com> - 0.3.2-1
- Remove unused dci-purge-swift-components

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
