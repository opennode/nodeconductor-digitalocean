Name: waldur-digitalocean
Summary: DigitalOcean plugin for Waldur
Group: Development/Libraries
Version: 0.11.2
Release: 1.el7
License: MIT
Url: http://waldur.com
Source0: %{name}-%{version}.tar.gz

Requires: waldur-core >= 0.151.0
Requires: python-digitalocean >= 1.5

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot

BuildRequires: python-setuptools

Obsoletes: nodeconductor-digitalocean

%description
DigitalOcean plugin for Waldur.

%prep
%setup -q -n %{name}-%{version}

%build
%{__python} setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --root=%{buildroot}

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%{python_sitelib}/*

%changelog
* Sun Jun 24 2018 Jenkins <jenkins@opennodecloud.com> - 0.11.2-1.el7
- New upstream release

* Tue May 22 2018 Jenkins <jenkins@opennodecloud.com> - 0.11.1-1.el7
- New upstream release

* Thu May 10 2018 Jenkins <jenkins@opennodecloud.com> - 0.11.0-1.el7
- New upstream release

* Fri Dec 1 2017 Jenkins <jenkins@opennodecloud.com> - 0.10.2-1.el7
- New upstream release

* Wed Nov 29 2017 Jenkins <jenkins@opennodecloud.com> - 0.10.1-1.el7
- New upstream release

* Sun Oct 29 2017 Jenkins <jenkins@opennodecloud.com> - 0.10.0-1.el7
- New upstream release

* Wed Sep 27 2017 Jenkins <jenkins@opennodecloud.com> - 0.9.0-1.el7
- New upstream release

* Sat Sep 16 2017 Jenkins <jenkins@opennodecloud.com> - 0.8.4-1.el7
- New upstream release

* Wed Jul 12 2017 Jenkins <jenkins@opennodecloud.com> - 0.8.3-1.el7
- New upstream release

* Mon Jul 3 2017 Jenkins <jenkins@opennodecloud.com> - 0.8.2-1.el7
- New upstream release
