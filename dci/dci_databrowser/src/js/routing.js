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

require('app')
.config([
  '$stateProvider', '$urlRouterProvider',
  function($stateProvider, $urlRouterProvider) {
    var scrollTop = ['$anchorScroll',
      function ($anchorScroll) {$anchorScroll();}
    ];

    $stateProvider
    .state('auth', {
      'abstract': true,
      resolve: {
        _: ['auth', '$q', function (auth, $q) {
          if (auth.isAuthenticated()) {
            return;
          } else {
            return $q.reject(auth.state);
          }
        }]
      },
      controller: 'authCtrl',
      templateUrl: '/partials/auth.html'
    })
    .state('index', {
      url: '/',
      parent: 'auth',
      onEnter: ['$state', function ($state) {
        $state.go('jobs');
      }]
    })
    .state('jobs', {
      url: '/jobs?page',
      parent: 'auth',
      resolve: {
        page: ['$stateParams', function ($stateParams) {
          return parseInt($stateParams.page) || 1;
        }],
        jobs: ['api', 'page', function(api, page) {
          return api.getJobs(page);
        }]
      },
      onEnter: scrollTop,
      templateUrl: '/partials/jobs.html',
      controller: 'ListJobsCtrl'
    })
    .state('job', {
      url: '/jobs/:id',
      parent: 'auth',
      templateUrl: '/partials/job.html',
      resolve: {
        job: ['$stateParams', 'api', function($stateParams, api) {
          return api.getJob($stateParams.id);
        }]
      },
      controller: 'JobCtrl'
    })
    .state('jobdefinitions', {
      url: '/jobdefinitions?page',
      parent: 'auth',
      resolve: {
        page: ['$stateParams', function ($stateParams) {
          return parseInt($stateParams.page) || 1;
        }],
        jobdefinitions: ['api', 'page', function(api, page) {
          return api.getJobDefinitions(page);
        }]
      },
      templateUrl: '/partials/jobdefinitions.html',
      controller: 'ListJobDefinitionsCtrl'
    })
    .state('jobdefinition', {
      url: '/jobdefinitions/:id',
      parent: 'auth',
      resolve: {
        jobdefinition: ['$stateParams', 'api', function($stateParams, api) {
          return api.getJobDefinition($stateParams.id);
        }]
      },
      templateUrl: '/partials/jobdefinition.html',
      controller: 'JobDefinitionCtrl'
    })

    .state('remotecis', {
      url: '/remotecis?page',
      parent: 'auth',
      templateUrl: '/partials/remotecis.html',
      resolve: {
        page: ['$stateParams', function ($stateParams) {
          return parseInt($stateParams.page) || 1;
        }],
        cis: ['api', 'page', function(api, page) {
          return api.getCIs(page);
        }]
      },
      onEnter: scrollTop,
      controller: 'ListCIsCtrl'
    })
    .state('login', {
      url: '/login?next&args',
      controller: 'LoginCtrl',
      resolve: {
        next: ['$stateParams', function($stateParams) {
          return {
            state: $stateParams.next || 'index',
            args: $stateParams.args &&
              angular.fromJson(atob($stateParams.args)) || {}
          };
        }]
      },
      templateUrl: '/partials/login.html',
    });

    $urlRouterProvider.otherwise('/');
  }
])

.controller('authCtrl', [
  '$scope', '$state', 'auth', function ($scope, $state, auth) {
    $scope.isAuthenticated = auth.isAuthenticated;
    $scope.logout = function () {
      auth.logout();
      $state.go('login');
    }
  }
])

.run([
  '$rootScope', '$state', 'authStates', 'auth',
  function($rootScope, $state, authStates, auth) {
    $rootScope.$on(
      '$stateChangeError',
      function(event, toState, toParams, fromState, fromParams, error) {
        function redirect() {
          $state.go('login', {
            next: toState.name,
            args: btoa(angular.toJson(toParams))
          }, {
            reload: true
          });
        }
        if (error.status == 401) {
          auth.state = authStates.UNAUTHORIZED;
          redirect();
        }
        if (error === authStates.DISCONNECTED) {
          redirect();
        }
      }
    );
  }
]);

