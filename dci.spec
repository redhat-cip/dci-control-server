%if 0%{?fedora}
%global with_python3 1
%endif
%global debug_package %{nil}

Name:           dci
Version:        0.0.VERS
Release:        1%{?dist}
Summary:        DCI control server

License:        ASL 2.0
URL:            https://github.com/redhat-cip/dci-control-server
Source0:        dci-%{version}.tgz

%description
DCI control server

%package -n dci-common
Summary:  DCI Common commands

%description -n dci-common
DCI common commands.

%if 0%{?with_python3}
%package -n dci-common-python3
Summary:  DCI Common commands

%description -n dci-common-python3
DCI common commands.
%endif


%package -n dci-api
Summary:        DCI control server API
BuildRequires:  net-tools
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  postgresql
BuildRequires:  postgresql-devel
BuildRequires:  postgresql-server
BuildRequires:  python-psycopg2
BuildRequires:  python-tox
BuildRequires:  python-alembic
BuildRequires:  python-flask
BuildRequires:  python-requests
BuildRequires:  python-six
BuildRequires:  python-passlib
BuildRequires:  gcc
BuildRequires:  java-1.8.0-openjdk
BuildRequires:  elasticsearch

Requires:       python-alembic
Requires:       python-elasticsearch
Requires:       python-flask
Requires:       python-flask-sqlalchemy
Requires:       python-passlib
Requires:       python-psycopg2
Requires:       python-requests
Requires:       python-six
Requires:       python-sqlalchemy
Requires:       python-sqlalchemy-utils
Requires:       python-voluptuous
Requires:       python-werkzeug

%description -n dci-api
The implementation of the DCI control server API.

%if 0%{?with_python3}
%package -n dci-api-python3
Summary:        DCI control server API
BuildRequires:  net-tools
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  postgresql
BuildRequires:  postgresql-devel
BuildRequires:  postgresql-server
BuildRequires:  python3-psycopg2
BuildRequires:  python-tox
BuildRequires:  python3-alembic
BuildRequires:  python3-flask
BuildRequires:  python3-requests
BuildRequires:  python3-six
BuildRequires:  python-passlib
BuildRequires:  gcc
BuildRequires:  java-1.8.0-openjdk
BuildRequires:  elasticsearch

Requires:       python3-alembic
Requires:       python3-elasticsearch
Requires:       python3-flask
Requires:       python3-flask-sqlalchemy
Requires:       python-passlib
Requires:       python3-psycopg2
Requires:       python3-requests
Requires:       python3-six
Requires:       python3-sqlalchemy
Requires:       python3-sqlalchemy-utils
Requires:       python3-voluptuous
Requires:       python3-werkzeug

%description -n dci-api-python3
The implementation of the DCI control server API.
%endif


%prep -a
%setup -qc

%build
%py2_build
%if 0%{?with_python3}
%py3_build
%endif


%install
%py2_install
install -d %{buildroot}/%{_datarootdir}/dci-api
install -d %{buildroot}%{_sysconfdir}/dci-api
mv wsgi.py %{buildroot}/%{_datarootdir}/dci-api/wsgi.py
%{__ln_s} %{python2_sitelib}/dci/settings.py %{buildroot}%{_sysconfdir}/dci-api/settings.py
rm -rf %{buildroot}/%{python2_sitelib}/sample
# NOTE(spredzy): Do this trick until we can upload updated rpm
find %{buildroot}/%{python2_sitelib}/*.egg-info -name 'requires.txt' | xargs sed -i '2s/elasticsearch.*/elasticsearch/'
find %{buildroot}/%{python2_sitelib}/*.egg-info -name 'requires.txt' | xargs sed -i '11s/setuptools.*/setuptools/'
find %{buildroot}/%{python2_sitelib}/*.egg-info -name 'requires.txt' | xargs sed -i '12s/Werkzeug.*/Werkzeug/'
%if 0%{?with_python3}
%py3_install
rm -rf %{buildroot}/%{python3_sitelib}/sample
find %{buildroot}/%{python3_sitelib}/*.egg-info -name 'requires.txt' | xargs sed -i '2s/elasticsearch.*/elasticsearch/'
find %{buildroot}/%{python3_sitelib}/*.egg-info -name 'requires.txt' | xargs sed -i '11s/setuptools.*/setuptools/'
find %{buildroot}/%{python3_sitelib}/*.egg-info -name 'requires.txt' | xargs sed -i '12s/Werkzeug.*/Werkzeug/'
%endif


sed -i '2s/elasticsearch.*/elasticsearch/' requirements.txt
sed -i '11s/setuptools.*/setuptools/' requirements.txt
sed -i '12s/Werkzeug.*/Werkzeug/' requirements.txt


%check -n dci-api
%{__python2} setup.py test
%if 0%{?with_python3}
%{__python3} setup.py test
%endif


%files -n dci-common
%{_bindir}/dci-dbsync
%{_bindir}/dci-dbinit
%{_datarootdir}/dci-api/wsgi.py*

%if 0%{?with_python3}
%files -n dci-common-python3
%{_bindir}/dci-dbsync
%{_bindir}/dci-dbinit
%{_datarootdir}/dci-api/wsgi.py*
%endif

%files -n dci-api
%doc
%{python2_sitelib}/dci
%{python2_sitelib}/*.egg-info
%{_sysconfdir}/dci-api/settings.py

%if 0%{?with_python3}
%files -n dci-api-python3
%doc
%{python3_sitelib}/dci
%{python3_sitelib}/*.egg-info
%{_sysconfdir}/dci-api/settings.py
%endif

%changelog
* Mon Nov 16 2015 Yanis Guenane <yguenane@redhat.com> 0.1-1
- Initial commit
