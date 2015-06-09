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

var app = angular.module('app', ['ngRoute', 'restangular', 'ngCookies']);

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
    });

    $httpProvider.interceptors.push('BasicAuthInjector');
});

app.factory('CommonCode', function($window, Restangular, $cookies) {
    // jscs:disable requireCamelCaseOrUpperCaseIdentifiers

    var getJobInfo = function($scope, job_id){
        Restangular.one('jobs', job_id).get({'embedded': {'remoteci':1, 'testversion':1}}).then(
        function(job){
            $scope.job = job;
            Restangular.one('jobstates').get(
                {'where': {'job_id': job_id},
                 'embedded': {'files_collection':1}}).then(
                 function(jobstates){
                     $scope.job['jobstates'] = jobstates._items;
                 });

            Restangular.one('testversions', job.testversion.id.id).get(
                {'embedded': {'version':1, 'test':1}}).then(
                function(testversion){
                    $scope.job['version'] = testversion.version.id.name;
                    $scope.job['test'] = testversion.test.id.name;
                    Restangular.one('products', testversion.version.id.product_id).get().then(
                        function(product){
                            $scope.job['product'] = product.name;
                        }
                    )});
        });
    };

    var aggregateJobInfo = function($scope, targetPage){

        Restangular.one('jobs').get({'page': targetPage, 'embedded': {'remoteci':1, 'testversion':1}}).then(
        function(jobs){
            for (var i = 0; i < jobs._items.length; i++) {
                // Get the last status and the last update date
                (function(localI) {
                    Restangular.one('jobstates').get(
                    {'where': {'job_id': jobs._items[localI].id}}).then(
                      function(jobstates){
                          length = jobstates._items.length;
                          jobs._items[localI]['updated_at'] = jobstates._items[length-1].updated_at;
                          jobs._items[localI]['status'] = jobstates._items[length-1].status;
                          jobs._items[localI]['jobstates'] = jobstates
                      });
                 })(i);

                // Get the product name, the version and the test name
                (function(localI) {
                    Restangular.one('testversions', jobs._items[localI].testversion.id.id).get(
                    {'embedded': {'version':1, 'test':1}}).then(
                        function(testversion){
                            jobs._items[localI]['version'] = testversion.version.id.name;
                            jobs._items[localI]['test'] = testversion.test.id.name;

                            Restangular.one('products', testversion.version.id.product_id).get().then(
                            function(product){
                                jobs._items[localI]['product'] = product.name;
                            }
                            )
                        }
                    );
                })(i);
            }

            $scope._meta = jobs._meta;
            $scope._link = jobs._link;
            $scope.jobs = jobs._items;
            $cookies.totalPages = $scope._meta.total / $scope._meta.max_results;
        });
    };

    return {'aggregateJobInfo': aggregateJobInfo,
            'getJobInfo': getJobInfo};
});


app.factory('BasicAuthInjector', function($cookies) {
    var injector = {
        request: function(config) {
            config.headers['Authorization'] = 'Basic ' + $cookies.auth;
            return config;
        }
    };
    return injector;
});

app.controller('ListJobsController', function($scope, $location, $cookies,
CommonCode, Restangular) {

    $scope.loadPage = function() {
        var targetPage = $scope.currentPage;
        var searchObject = $location.search();
        if (searchObject.page != undefined) {
            var totalPages = $cookies.totalPages;

            if ((searchObject.page < ((parseInt(totalPages) + 1) | 0)) ||
                ($cookies.currentPage > 1)) {
                targetPage = parseInt(searchObject.page);
            }
        }

        CommonCode.aggregateJobInfo($scope, targetPage);
    };

    $scope.nextPage = function() {
        if ($scope.currentPage <
            ($scope._meta.total / $scope._meta.max_results)) {
            $scope.currentPage++;
            $location.path('/jobs').search({page:$scope.currentPage});
        }
    }

    $scope.previousPage = function() {
        if ($scope.currentPage > 1) {
            $scope.currentPage--;
            $location.path('/jobs').search({page:$scope.currentPage});
        }
    }

    $scope.loadPage();
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

    CommonCode.getJobInfo($scope, $scope.job_id);
});

app.controller('LoginController', ['$scope', '$location', '$cookies',
    function($scope, $location, $cookies) {
        $scope.submit = function() {
            var loginb64 = btoa($scope.username.concat(':', $scope.password));
            $cookies.auth = loginb64;
            $location.path('/jobs')
        };
    }
]);

app.controller('LogoutController', ['$scope', '$location', '$templateCache',
'$cookies',
  function($scope, $location, $templateCache, $cookies) {
      $templateCache.removeAll();
      $cookies.auth = btoa('None');
      $location.path('/login')
  }
]);

app.controller('MainController', function($scope, $route, $routeParams,
$location) {
    $scope.currentPage = 1;
    $scope.$route = $route;
    $scope.$location = $location;
    $scope.$routeParams = $routeParams;
});
