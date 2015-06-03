// -*- coding: utf-8 -*-
//
// Copyright 2015 Red Hat, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

'use strict';

var app = angular.module('app', ['ngRoute', 'restangular']);

app.value('currentAuthBA', {value: 'None'});

// Configure the application
app.config(function(RestangularProvider) {
    RestangularProvider.setBaseUrl(
        '/api');
    // https://github.com/mgonto/restangular#my-response-is-actually-wrapped-with-some-metadata-how-do-i-get-the-data-in-that-case
    RestangularProvider.addResponseInterceptor(function(
    data, operation, what, url, response, deferred) {
        var extractedData = [];
        if (operation === 'getList') {
            extractedData._items = data._items;
            extractedData._meta = data._meta;
        } else {
            extractedData = data;
        }
        return extractedData;
    });
});

app.config(function($routeProvider, $locationProvider, $parseProvider,
$httpProvider) {
    $routeProvider
    .when('/login', {
        templateUrl: 'view/login.html',
        controller: 'LoginController'
    }).
    when('/logout', {
        templateUrl: 'view/logout.html',
        controller: 'LogoutController'
    }).
    when('/jobs', {
        templateUrl: 'view/jobs.html',
        controller: 'ListJobsController'
    }).
    when('/remotecis', {
        templateUrl: 'view/remotecis.html',
        controller: 'ListRemotecisController'
    })
    .when('/jobs/:job_id', {
        templateUrl: 'view/jobdetails.html',
        controller: 'JobDetailsController'
    })
    .otherwise({redirectTo: '/jobs'});

    $httpProvider.interceptors.push('BasicAuthInjector');
});

app.factory('CommonCode', function($window, Restangular) {
    // jscs:disable requireCamelCaseOrUpperCaseIdentifiers

    var version;
    return {
    'aggregateJobInfo': function(job) {
        return Restangular.one('testversions', job.testversion_id).get().then(
        function(testVersion) {
            Restangular.one('remotecis', job.remoteci_id).get().
            then(function(data) {job['remoteci'] = data;});
            Restangular.one('tests', testVersion.test_id).get().
            then(function(data) {job['test'] = data;});
            Restangular.one('versions', testVersion.version_id).get().
            then(function(data) {
                job['version'] = data;
                Restangular.one('products', job['version']['product_id']).get().
                then(function(data) {job['product'] = data;});
            });
            Restangular.all('jobstates').getList({'where': {'job_id': job.id}
                // TODO(Gonéri): to uncomment as soon as
                // https://github.com/RedTurtle/eve-sqlalchemy/pull/41 is accepted
                //, "sort": "created_at"
            }).then(
            function(data) {
                job['jobstates'] = data._items;
                for (var i = 0; i < job.jobstates.length; i++) {
                    (function(localI) {
                     Restangular.all('files').getList(
                         {'where': {'jobstate_id': job.jobstates[i].id},
                          'embedded': {'jobstates_collection':1}
                  }).then(function(data) {
                    job.jobstates[localI].files = data._items;});
                 })(i);
                }
            });
        });
    }};
});

app.factory('BasicAuthInjector', function(currentAuthBA) {
    var injector = {
        request: function(config) {
            config.headers['Authorization'] = 'Basic ' + currentAuthBA.value;
            return config;
        }
    };
    return injector;
});

app.controller('ListJobsController', function($scope, $location, CommonCode,
Restangular) {
    var searchObject = $location.search();
    var base = Restangular.all('jobs');

    base.getList({'page': searchObject.page}).then(
    function(jobs) {
        for (var i = 0; i < jobs._items.length; i++) {
            CommonCode.aggregateJobInfo(jobs._items[i]);
        }

        $scope._meta = jobs._meta;
        $scope._link = jobs._link;
        $scope.jobs = jobs._items;
    });
});

app.controller('ListRemotecisController', function(
    $scope, $location, CommonCode, Restangular) {
    var searchObject = $location.search();
    var base = Restangular.all('remotecis');

    base.getList({'page': searchObject.page}).then(
    function(remotecis) {
        for (var i = 0; i < remotecis._items.length; i++) {
            CommonCode.aggregateJobInfo(remotecis._items[i]);
        }

        $scope._meta = remotecis._meta;
        $scope._link = remotecis._link;
        $scope.remotecis = remotecis._items;
    });
});

app.controller('JobDetailsController', function(
    $scope, $routeParams, CommonCode, Restangular) {
    $scope.job_id = $routeParams.job_id;

    Restangular.one('jobs', $scope.job_id).get().then(
        function(job) {
            $scope.job = job;
            CommonCode.aggregateJobInfo(job);
        }
    );
});

app.controller('LoginController', ['$scope', '$location', 'currentAuthBA',
    function($scope, $location, currentAuthBA) {
        $scope.submit = function() {
            var loginb64 = btoa($scope.username.concat(':', $scope.password));
            currentAuthBA.value = loginb64;
            $location.path('/jobs')
        };
    }
]);

app.controller('LogoutController', ['$scope', '$location', '$templateCache',
'currentAuthBA',
  function($scope, $location, $templateCache, currentAuthBA) {
      $templateCache.removeAll();
      currentAuthBA.value = btoa('None');
      $location.path('/login')
  }
]);

app.controller('MainController', function($scope, $route, $routeParams,
$location) {
    $scope.$route = $route;
    $scope.$location = $location;
    $scope.$routeParams = $routeParams;
});
