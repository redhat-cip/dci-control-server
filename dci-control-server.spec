%if 0%{?fedora}
%global with_python3 1
%endif

Name:           dci-control-server
Version:        0.0.VERS
Release:        1%{?dist}
Summary:        DCI control server

License:        ASL 2.0
URL:            https://github.com/redhat-cip/dci-control-server
Source0:        dci-control-server-%{version}.tgz

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
BuildRequires:  python2-devel
BuildRequires:  python-setuptools

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


%package -n dci-ui
Summary:  DCI UI
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  python-simplejson
BuildRequires:  epel-release
BuildRequires:  nodejs
BuildRequires:  npm
BuildRequires:  tar
BuildRequires:  bzip2

%description -n dci-ui
The DCI UI static files


%prep -a
%setup -qc

%build
%py2_build
# NOTE(spredzy): With py2_build only the python related files
# are copied to the build dir, we need to copy along the UI
# files
cp -r dci/dci_databrowser/* build/lib/dci/dci_databrowser/
cp -r wsgi.py build/lib/dci/


%install
# NOTE(spredzy): mock needs to be able to install modules
# in its own path - not the global one.
npm config set prefix '/tmp/npm-global'
npm install -g gulp
%py2_install
install -d %{buildroot}/%{_datarootdir}/dci-api
cd %{buildroot}/%{python2_sitelib}/dci/dci_databrowser
npm install
/tmp/npm-global/bin/gulp build
# NOTE(spredzy): The following files are empty and breaks during
# nodejs.prov hence we remove them
rm /builddir/.npm/npmconf/2.1.2/package/test/fixtures/package.json
rm /builddir/.npm/npmconf/2.1.1/package/test/fixtures/package.json
rm %{buildroot}/%{python2_sitelib}/dci/dci_databrowser/node_modules/phantomjs/node_modules/npmconf/test/fixtures/package.json
rm %{buildroot}/%{python2_sitelib}/dci/dci_databrowser/node_modules/gulp-sass/node_modules/node-sass/node_modules/npmconf/test/fixtures/package.json
rm -rf /buildir/.npm
rm -rf /tmp/npm-global
rm -rf %{buildroot}/%{python2_sitelib}/dci/dci_databrowser/node_modules/
mv %{buildroot}/%{python2_sitelib}/sample %{buildroot}/%{_datarootdir}/dci-api/sample
mv %{buildroot}/%{python2_sitelib}/dci/wsgi.py %{buildroot}/%{_datarootdir}/dci-api/wsgi.py
# NOTE(spredzy): Do this trick until we can upload updated rpm
find %{buildroot}/%{python2_sitelib}/control_server* -name 'requires.txt' | xargs sed -i '2s/elasticsearch.*/elasticsearch/'
find %{buildroot}/%{python2_sitelib}/control_server* -name 'requires.txt' | xargs sed -i '11s/setuptools.*/setuptools/'
find %{buildroot}/%{python2_sitelib}/control_server* -name 'requires.txt' | xargs sed -i '12s/Werkzeug.*/Werkzeug/'

%files -n dci-ui
%doc
%{python2_sitelib}/dci/dci_databrowser/static

%files -n dci-agents
%doc


%files -n dci-feeders
%doc


%files -n dci-common
%{_bindir}/dci-dbsync
%{_bindir}/dci-openshift-dbinit
%{_datarootdir}/dci-api/sample
%{_datarootdir}/dci-api/wsgi.py
# TODO(spredzy): Find a way for those files not to be generated
%{_datarootdir}/dci-api/wsgi.pyo
%{_datarootdir}/dci-api/wsgi.pyc


%files -n dci-api
%doc
%{python2_sitelib}/dci
%{python2_sitelib}/*.egg-info


%changelog
* Mon Nov 16 2015 Yanis Guenane <yguenane@redhat.com> 0.1-1
- Initial commit
