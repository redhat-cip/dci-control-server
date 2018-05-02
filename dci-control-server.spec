%if 0%{?fedora}
# NOTE(Gonéri): We will trun this on when python3-swiftclient
# will be available
%global with_python3 0
%endif

Name:           dci
Version:        0.2.1
Release:        1.VERS%{?dist}
Summary:        DCI control server
License:        ASL 2.0
URL:            https://github.com/redhat-cip/dci-control-server
Source0:        dci-%{version}.tar.gz
BuildArch:      noarch

%description
DCI control server

%package -n dci-api
Summary:        DCI control server API
Conflicts:      dci-common < %{version}
Obsoletes:      dci-common
BuildRequires:  net-tools
BuildRequires:  rh-postgresql94-postgresql-devel
BuildRequires:  rh-postgresql94
BuildRequires:  pyOpenSSL
BuildRequires:  python-alembic
BuildRequires:  python-flask < 1:1.0.0
BuildRequires:  python-flask-sqlalchemy
BuildRequires:  python-lxml
BuildRequires:  python-passlib
BuildRequires:  python-psycopg2
BuildRequires:  python-requests
BuildRequires:  python-rpm-macros
BuildRequires:  python-setuptools
BuildRequires:  python-six
BuildRequires:  python-sqlalchemy-utils
BuildRequires:  python-tornado
BuildRequires:  python-voluptuous
BuildRequires:  python-werkzeug
BuildRequires:  python-zmq
BuildRequires:  python-jwt
BuildRequires:  python-dciauth
BuildRequires:  python2-pytest
BuildRequires:  python2-rpm-macros
BuildRequires:  python2-swiftclient
BuildRequires:  systemd
BuildRequires:  systemd-units
Requires:       pyOpenSSL
Requires:       python-alembic
Requires:       python-flask < 1:1.0.0
Requires:       python-flask-sqlalchemy
Requires:       python-lxml
Requires:       python-passlib
Requires:       python-psycopg2
Requires:       python-requests
Requires:       python-six
Requires:       python-sqlalchemy-utils
Requires:       python-tornado
Requires:       python-voluptuous
Requires:       python-werkzeug
Requires:       python-zmq
Requires:       python-jwt
Requires:       python-dciauth
Requires:       python2-swiftclient
Requires:       pytz

%description -n dci-api
The implementation of the DCI control server API.

%if 0%{?with_python3}
%package -n dci-api-python3
Summary:        DCI control server API
Conflicts:      dci-common-python3 < %{version}
Obsoletes:      dci-common-python3
BuildRequires:  net-tools
BuildRequires:  rh-postgresql94-postgresql-devel
BuildRequires:  rh-postgresql94
BuildRequires:  pyOpenSSL
BuildRequires:  python3-alembic
BuildRequires:  python3-flask < 1:1.0.0
BuildRequires:  python3-flask-sqlalchemy
BuildRequires:  python3-lxml
BuildRequires:  python3-passlib
BuildRequires:  python3-psycopg2
BuildRequires:  python3-pytest
BuildRequires:  python3-requests
BuildRequires:  python3-rpm-macros
BuildRequires:  python3-setuptools
BuildRequires:  python3-six
BuildRequires:  python3-sqlalchemy-utils
BuildRequires:  python3-swiftclient
BuildRequires:  python3-voluptuous
BuildRequires:  python3-werkzeug
BuildRequires:  python3-zmq
BuildRequires:  python-jwt
BuildRequires:  python3-dciauth
BuildRequires:  systemd
BuildRequires:  systemd-units
Requires:       pyOpenSSL
Requires:       python3-alembic
Requires:       python3-flask < 1:1.0.0
Requires:       python3-flask-sqlalchemy
Requires:       python3-lxml
Requires:       python3-passlib
Requires:       python3-psycopg2
Requires:       python3-pytz
Requires:       python3-requests
Requires:       python3-six
Requires:       python3-sqlalchemy-utils
Requires:       python3-swiftclient
Requires:       python3-voluptuous
Requires:       python3-werkzeug
Requires:       python3-zmq
Requires:       python-jwt
Requires:       python3-dciauth


%description -n dci-api-python3
The implementation of the DCI control server API.
%endif


%prep -a
%autosetup -n %{name}-%{version}

%build
%py2_build
%if 0%{?with_python3}
%py3_build
%endif


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
%if 0%{?with_python3}
%py3_install
%endif


%check -n dci-api
%{__python2} setup.py test
%if 0%{?with_python3}
%{__python3} setup.py test
%endif


%files -n dci-api
%{_bindir}/dci-dbsync
%{_bindir}/dci-dbinit
%license LICENSE
%doc
%{python2_sitelib}/dci
%{python2_sitelib}/*.egg-info
%{_unitdir}
%config(noreplace) %{_sysconfdir}/dci-api/settings.py
%{_datarootdir}/dci-api/wsgi.py

%if 0%{?with_python3}
%{_bindir}/dci-dbsync
%{_bindir}/dci-dbinit
%files -n dci-api-python3
%doc
%{python3_sitelib}/dci
%{python3_sitelib}/*.egg-info
%config(noreplace) %{_sysconfdir}/dci-api/settings.py
%endif

# NOTE(Gonéri): the content of settings.py is likely to evolve.
# We don't want to end up with outdated cache on the hard drive.
%exclude %{_sysconfdir}/dci-api/settings.py?
%exclude %{python2_sitelib}/dci/settings.py?

%changelog
* Wed Apr 18  2018 Guillaume Vincent <gvincent@redhat.com> 0.2.1-1
- Use rh-postgresql94 to mimic the db production version

* Fri Mar 1  2018 Yassine Lamgarchal <ylamgarc@redhat.com> 0.2.0-4
- Remove all Elasticsearch related components

* Fri Dec 1  2017 Yassine Lamgarchal <ylamgarc@redhat.com> 0.2.0-3
- Replace dci-esindex by dci-essync

* Thu Oct 05 2017 Yassine Lamgarchal <ylamgarc@redhat.com> 0.2.0-2
- Adding jwt dependency.

* Wed May 10 2017 Yanis Guenane <yguenane@redhat.com> 0.2.0-1
- Bumping to 0.2.0 for CI purposes

* Mon Nov 16 2015 Yanis Guenane <yguenane@redhat.com> 0.1-1
- Initial commit
