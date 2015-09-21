// -*- coding: utf-8 -*-
//
// Copyright 2015 Red Hat, Inc.
//
// Licensed under the Apache License, Version 2.0 (the 'License'); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

'use strict';

var app = angular.module('app', ['ngRoute', 'ngCookies',
'angular-loading-bar', 'ui.router', 'googlechart', 'ngResource']);

app.factory('MyInjector', function($cookies, $q, $window) {
    var injector = {
        request: function(config) {
            config.headers.Authorization = 'Basic ' + $cookies.auth;
            return config;
        }
    };
    return injector;
});

app.config(function($stateProvider, $urlRouterProvider, $httpProvider) {
    function isAuthenticated($q, $cookies) {
        var d = $q.defer();
        if (($cookies.auth == btoa('None')) ||
             angular.isUndefined($cookies.auth)) {
            d.reject('notAuthenticated');
        } else {
            d.resolve();
        }
        return d.promise;
    }

    $stateProvider
    .state('auth', {
        abstract: true,
        resolve: {
            'auth': ['$q', '$cookies', isAuthenticated]
        },
        template: '<ui-view/>'
    }).state('jobs', {
        url: '/jobs?page',
        parent: 'auth',
        templateUrl: 'partials/jobs.html',
        controller: 'ListJobsController'
    }).state('jobdetails', {
        url: '/jobdetails/:jobId',
        parent: 'auth',
        templateUrl: 'partials/jobdetails.html',
        controller: 'JobDetailsController'
    }).state('remotecis', {
        url: '/remotecis?page',
        parent: 'auth',
        templateUrl: 'partials/remotecis.html',
        controller: 'ListRemotecisController'
    }).state('products', {
        url: '/products',
        parent: 'auth',
        templateUrl: 'partials/products.html',
        controller: 'ProductsController'
    }).state('stats', {
        url: '/stats',
        parent: 'auth',
        templateUrl: 'partials/stats.html',
        controller: 'StatsController'
    }).state('versions', {
        url: '/versions?page',
        parent: 'auth',
        templateUrl: 'partials/versions.html',
        controller: 'VersionsController'
    }).state('versiondetails', {
        url: '/versiondetails/:versionId',
        parent: 'auth',
        templateUrl: 'partials/versiondetails.html',
        controller: 'VersionDetailsController'
    }).state('signin', {
        url: '/signin',
        templateUrl: 'partials/signin.html',
        controller: 'LoginController'
    }).state('signout', {
        url: '/signout',
        templateUrl: 'partials/signout.html',
        controller: 'LogoutController'
    });

    $urlRouterProvider.otherwise('signin');
    $httpProvider.interceptors.push('MyInjector');
});

app.controller('AppCtrl', function($rootScope, $state) {
    $rootScope.$on('$routeChangeError', function(value) {
        if (value === 'notAuthenticated') {
            $state.go('signin');
        }
    });
});

app.factory('CommonCode', function($resource, $cookies, $location) {
    // jscs:disable requireCamelCaseOrUpperCaseIdentifiers

    var getRemoteCis = function($scope) {
        var targetPage = $scope.remoteciCurrentPage;
        var searchObject = $location.search();
        if (searchObject.page != undefined) {
            var totalPages = $cookies.remotecisTotalPages;
            var pageNumber = parseInt(searchObject.page);

            if ((pageNumber < ((parseInt(totalPages) + 1) | 0)) &&
                (pageNumber > 1)) {
                targetPage = parseInt(searchObject.page);
                $scope.remoteciCurrentPage = targetPage;
            }
        }
        var Remotecis = $resource('/api/remotecis').get(
            {'page': targetPage, 'sort': '-created_at'});
        Remotecis.$promise.then(function(remotecis) {
            $scope.remotecis = remotecis._items;
            $cookies.remotecisTotalPages = parseInt((
            remotecis._meta.total / remotecis._meta.max_results + 1));
            $scope.remotecisTotalPages = $cookies.remotecisTotalPages;
        });
    };

    var getJobInfo = function($scope, job_id) {
        var Job = $resource('/api/jobs/' + job_id).get(
        {'embedded': {'remoteci': 1, 'testversion': 1}});
        Job.$promise.then(function(job) {
            $scope.job = job;
            var Jobstates = $resource('/api/jobstates').get(
                {'where': {'job_id': job_id},
                 'sort': 'created_at',
                 'embedded': {'files_collection': 1}});
            Jobstates.$promise.then(function(jobstates) {
                $scope.job.jobstates = jobstates._items;
            });

            var Testversions = $resource(
                '/api/testversions/' + job.testversion.id).get(
                    {'embedded': {'version': 1, 'test': 1}});
            Testversions.$promise.then(function(testversion) {
                $scope.job.version = testversion.version.name;
                $scope.job.test = testversion.test.name;
                var Products = $resource('/api/products/' +
                    testversion.version.product_id).get();
                Products.$promise.then(
                    function(product) {
                        $scope.job.product = product.name;
                    });
            });
        });
    };

    return {'getJobInfo': getJobInfo,
            'getRemoteCis': getRemoteCis};
});

app.controller('ListJobsController', function($scope, $cookies, $resource,
$location, $state, CommonCode) {

    var loadPage = function() {
        var targetPage = $scope.jobCurrentPage;
        var searchObject = $location.search();
        if (searchObject.page != undefined) {
            var totalPages = $cookies.jobsTotalPages;
            var pageNumber = parseInt(searchObject.page);

            if ((pageNumber < ((parseInt(totalPages) + 1) | 0)) &&
                (pageNumber > 1)) {
                targetPage = parseInt(searchObject.page);
                $scope.jobCurrentPage = targetPage;
            }
        }
        var Jobs = $resource('/api/jobs').get({'page': targetPage,
                                               'extra_data': 1,
                                               'sort': '-created_at'});
        Jobs.$promise.then(function(jobs) {
            $scope.jobs = jobs._items;
            $cookies.jobsTotalPages = parseInt((jobs._meta.total /
                jobs._meta.max_results + 1));
            $scope.jobsTotalPages = $cookies.jobsTotalPages;

        });
    };

    $scope.jobsNextPage = function() {
        if ($scope.jobCurrentPage < $cookies.jobsTotalPages) {
            $scope.jobCurrentPage++;
            $state.go('jobs', {page: $scope.jobCurrentPage});
        }
    };

    $scope.jobsPreviousPage = function() {
        if ($scope.jobCurrentPage > 1) {
            $scope.jobCurrentPage--;
            $state.go('jobs', {page: $scope.jobCurrentPage});
        }
    };

    if ($scope.jobCurrentPage == undefined) {
        $scope.jobCurrentPage = 1;
    }

    loadPage();
});

app.controller('ListRemotecisController', function($scope, $location,
$cookies, $state, CommonCode) {

    $scope.remotecisNextPage = function() {
        if ($scope.remoteciCurrentPage < $cookies.remotecisTotalPages) {
            $scope.remoteciCurrentPage++;
            $state.go('remotecis', {page: $scope.remoteciCurrentPage});
        }
    };

    $scope.remotecisPreviousPage = function() {
        if ($scope.remoteciCurrentPage > 1) {
            $scope.remoteciCurrentPage--;
            $state.go('remotecis', {page: $scope.remoteciCurrentPage});
        }
    };

    if ($scope.remoteciCurrentPage == undefined) {
        $scope.remoteciCurrentPage = 1;
    }

    CommonCode.getRemoteCis($scope);
});

app.controller('JobDetailsController', function($scope, $stateParams,
$cookies, $state, CommonCode) {
    if ($stateParams.jobId) {
        CommonCode.getJobInfo($scope, $stateParams.jobId);
    }
});

app.controller('ProductsController', function($scope, $resource, $cookies,
$state, CommonCode) {
    var Products = $resource('/api/products').get();
    Products.$promise.then(function(products) {
        $scope.products = products._items;
        $scope.currentProduct = products._items[0];
    });

    $scope.$watch('currentProduct', function(currentProduct, previousProduct) {
        if (currentProduct != undefined) {
            var Version = $resource('/api/versions').get(
            {'where': {'product_id': currentProduct.id}, 'extra_data': 1});
            Version.$promise.then(function(versions) {
                $scope.versions_status = versions._items;
            });
        }
    });
});

app.controller('StatsController', function($scope, $stateParams, $resource,
$cookies, $state, CommonCode) {
    var Products = $resource('/api/products').get();
    Products.$promise.then(function(products) {
        $scope.products = products._items;
        $scope.currentProduct = products._items[0];

        var Versions = $resource('/api/versions').get(
            {'where': {'product_id': $scope.currentProduct.id}});
        Versions.$promise.then(function(versions) {
            $scope.versions = versions._items;
            $scope.currentVersion = versions._items[0];
        });
    });

    var getRate = function(product_id, version_id) {
        var Remotecis = $resource('/api/remotecis').
        get({'extra_data': 1, 'version_id': version_id});
        Remotecis.$promise.then(function(remotecis) {
        $scope.chart = {
            'type': 'PieChart',
            'data': [],
            'options': {
            'displayExactValues': true,
            'width': 600,
            'height': 400,
            'chartArea': {
                'left': 10,
                'top': 10,
                'bottom': 0,
                'height': '100%'
            }
        },
            'formatters': {},
            'displayed': true
        };

        $scope.chart.data = [
        [
          'Status',
          'rate'
        ],
        [
          'Success',
          remotecis.extra_data.success
        ],
        [
          'Failure',
          remotecis.extra_data.failure
        ],
        [
          'Ongoing',
          remotecis.extra_data.ongoing
        ],
        [
          'Not started',
          remotecis.extra_data.not_started
        ]];
    });};

    $scope.$watch('currentProduct', function(currentProduct, previousProduct) {
        if (angular.isUndefined(currentProduct)) {
            return;
        }

        var Versions = $resource('/api/versions').get(
            {'where': {'product_id': currentProduct.id}});
        Versions.$promise.then(function(versions) {
            $scope.versions = versions._items;
            $scope.currentVersion = versions._items[0];
        });
    });

    $scope.$watch('currentVersion', function(currentversion, previousversion) {
        if (angular.isundefined(currentversion) ||
            angular.isundefined($scope.currentproduct)) {
            return;
        }
        getrate($scope.currentproduct.id, currentversion.id);
    });
});

app.controller('VersionsController', function($scope, $resource, $cookies,
$state, CommonCode) {
    var versions = $resource('/api/versions').get();
    versions.$promise.then(function(versions) {
        $scope.versions = versions._items;
    });
});

app.controller('VersionDetailsController', function($scope, $resource,
$stateParams, $cookies, $state, CommonCode) {
    var version = $resource('/api/versions/' + $stateParams.versionId).get(
        {'embedded': {'testversions_collection': 1}});
    version.$promise.then(function(version) {
        $scope.version = version;
    });
});

app.controller('LoginController', ['$scope', '$cookies', '$state',
    function($scope, $cookies, $state) {
        $scope.submit = function() {
            var loginb64 = btoa($scope.username.concat(':', $scope.password));
            $cookies.auth = loginb64;
            $state.go('jobs');
        };
    }
]);

app.controller('LogoutController', ['$scope', '$templateCache',
'$cookies', '$state',
  function($scope, $templateCache, $cookies, $state) {
      $templateCache.removeAll();
      $cookies.auth = btoa('None');
      $state.go('signin');
  }
]);
