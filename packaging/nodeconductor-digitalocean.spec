Name: nodeconductor-digitalocean
Summary: DigitalOcean plugin for NodeConductor
Group: Development/Libraries
Version: 0.5.1
Release: 1.el7
License: MIT
Url: http://nodeconductor.com
Source0: %{name}-%{version}.tar.gz

Requires: nodeconductor > 0.134.0
Requires: python-digitalocean >= 1.5

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot

BuildRequires: python-setuptools

%description
DigitalOcean plugin for NodeConductor.

%prep
%setup -q -n %{name}-%{version}

%build
python setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --root=%{buildroot}

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%{python_sitelib}/*

%changelog
* Wed Apr 12 2017 Jenkins <jenkins@opennodecloud.com> - 0.5.1-1.el7
- New upstream release

* Tue Apr 11 2017 Jenkins <jenkins@opennodecloud.com> - 0.5.0-1.el7
- New upstream release

* Fri Apr 7 2017 Jenkins <jenkins@opennodecloud.com> - 0.4.3-1.el7
- New upstream release

* Sat Apr 1 2017 Jenkins <jenkins@opennodecloud.com> - 0.4.2-1.el7
- New upstream release

* Sat Apr 1 2017 Jenkins <jenkins@opennodecloud.com> - 0.4.1-1.el7
- New upstream release

* Thu Mar 2 2017 Jenkins <jenkins@opennodecloud.com> - 0.4.0-1.el7
- New upstream release

* Mon Feb 6 2017 Jenkins <jenkins@opennodecloud.com> - 0.3.0-1.el7
- New upstream release

* Tue Jan 24 2017 Jenkins <jenkins@opennodecloud.com> - 0.2.0-1.el7
- New upstream release

* Tue Jan 17 2017 Jenkins <jenkins@opennodecloud.com> - 0.1.5-1.el7
- New upstream release

* Mon Dec 19 2016 Jenkins <jenkins@opennodecloud.com> - 0.1.4-1.el7
- New upstream release

* Mon Dec 19 2016 Jenkins <jenkins@opennodecloud.com> - 0.1.3-1.el7
- New upstream release

* Wed Dec 7 2016 Jenkins <jenkins@opennodecloud.com> - 0.1.2-1.el7
- New upstream release

* Tue Dec 6 2016 Jenkins <jenkins@opennodecloud.com> - 0.1.1-1.el7
- New upstream release

* Tue Dec 6 2016 Jenkins <jenkins@opennodecloud.com> - 0.1.0-1.el7
- New upstream release

* Wed Nov 30 2016 Dmitri Tsumak <dmitri@opennodecloud.com> - 0.1.0-1.el7
- Initial version of the package
