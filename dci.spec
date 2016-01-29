%if 0%{?fedora}
%global with_python3 1
%endif

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


%package -n dci-agents
Summary:  DCI agents

%description -n dci-agents
DCI agents


%package -n dci-feeders
Summary:  DCI feeders

%description -n dci-feeders
DCI feeders.


%package -n dci-api
Summary:        DCI control server API
BuildRequires:  iproute
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


%prep -a
%setup -qc

%build
%py2_build


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

%check -n dci-api
tox -e pep8,py27

%files -n dci-agents
%doc


%files -n dci-feeders
%doc


%files -n dci-common
%{_bindir}/dci-dbsync
%{_bindir}/dci-dbinit
%{_datarootdir}/dci-api/wsgi.py*


%files -n dci-api
%doc
%{python2_sitelib}/dci
%{python2_sitelib}/*.egg-info
%{_sysconfdir}/dci-api/settings.py


%changelog
* Mon Nov 16 2015 Yanis Guenane <yguenane@redhat.com> 0.1-1
- Initial commit
