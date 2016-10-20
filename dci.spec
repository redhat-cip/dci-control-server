%if 0%{?fedora}
# NOTE(Gonéri): We will trun this on when python3-swiftclient
# will be available
%global with_python3 0
%endif
%global debug_package %{nil}

Name:           dci
Version:        0.0.VERS
Release:        1%{?dist}
Summary:        DCI control server

License:        ASL 2.0
URL:            https://github.com/redhat-cip/dci-control-server
Source0:        dci-%{version}.tar.gz

BuildArch:      noarch
Autoreq: 0

%description
DCI control server

%package -n dci-api
Summary:        DCI control server API
Provides:       dci-common
BuildRequires:  elasticsearch
BuildRequires:  java-1.8.0-openjdk
BuildRequires:  net-tools
BuildRequires:  postgresql
BuildRequires:  postgresql-server
BuildRequires:  python-alembic
BuildRequires:  python-elasticsearch
BuildRequires:  python-flask
BuildRequires:  python-flask-sqlalchemy
BuildRequires:  python-lxml
BuildRequires:  python-passlib
BuildRequires:  python-psycopg2
BuildRequires:  python-requests
BuildRequires:  python-rpm-macros
BuildRequires:  python2-rpm-macros
BuildRequires:  python-setuptools
BuildRequires:  python-six
BuildRequires:  python-sqlalchemy-utils
BuildRequires:  python-voluptuous
BuildRequires:  python-werkzeug
BuildRequires:  python2-pytest
BuildRequires:  python2-swiftclient
BuildRequires:  python2-swiftclient
Requires:       python-alembic
Requires:       python-elasticsearch
Requires:       python-flask
Requires:       python-flask-sqlalchemy
Requires:       python-lxml
Requires:       python-passlib
Requires:       python-psycopg2
Requires:       python-requests
Requires:       python-six
Requires:       python-sqlalchemy-utils
Requires:       python-voluptuous
Requires:       python-werkzeug
Requires:       python2-swiftclient

%description -n dci-api
The implementation of the DCI control server API.

%if 0%{?with_python3}
%package -n dci-api-python3
Summary:        DCI control server API
Provides:       dci-common-python3
Provides:       dci-common
BuildRequires:  elasticsearch
BuildRequires:  java-1.8.0-openjdk
BuildRequires:  net-tools
BuildRequires:  postgresql
BuildRequires:  postgresql-server
BuildRequires:  python-passlib
BuildRequires:  python3-alembic
BuildRequires:  python3-elasticsearch
BuildRequires:  python3-flask
BuildRequires:  python3-flask-sqlalchemy
BuildRequires:  python3-lxml
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
Requires:       python-passlib
Requires:       python3-alembic
Requires:       python3-elasticsearch
Requires:       python3-flask
Requires:       python3-flask-sqlalchemy
Requires:       python3-lxml
Requires:       python3-psycopg2
Requires:       python3-requests
Requires:       python3-six
Requires:       python3-sqlalchemy-utils
Requires:       python3-swiftclient
Requires:       python3-voluptuous
Requires:       python3-werkzeug

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
%{_bindir}/dci-esindex
%doc
%{python2_sitelib}/dci
%{python2_sitelib}/*.egg-info
%config(noreplace) %{_sysconfdir}/dci-api/settings.py
%{_datarootdir}/dci-api/wsgi.py

%if 0%{?with_python3}
%{_bindir}/dci-dbsync
%{_bindir}/dci-dbinit
%{_bindir}/dci-esindex
%files -n dci-api-python3
%doc
%{python3_sitelib}/dci
%{python3_sitelib}/*.egg-info
%config(noreplace) %{_sysconfdir}/dci-api/settings.py
%endif

%exclude %{_sysconfdir}/dci-api/settings.py?
%exclude %{python2_sitelib}/dci/settings.py?

%changelog
* Mon Nov 16 2015 Yanis Guenane <yguenane@redhat.com> 0.1-1
- Initial commit
