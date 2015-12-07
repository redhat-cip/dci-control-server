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
      url: '/jobs?status&remoteci&page',
      parent: 'auth',
      onEnter: scrollTop,
      templateUrl: '/partials/jobs.html',
      controller: 'ListJobsCtrl',
      resolve: {
        page: ['$stateParams', function($stateParams) {
          return parseInt($stateParams.page) || 1;
        }],
        jobs: [
          '$stateParams', 'api', 'page', function($stateP, api, page) {
            var remoteci = $stateP.remoteci;
            var status = $stateP.status;

            $stateP.remoteci = remoteci = remoteci ? remoteci.split(',') : [];
            $stateP.status = status = status ? status.split(',') : [];

            if (remoteci.length || status.length) {
              return api.searchJobs(remoteci, status);
            } else {
              return api.getJobs(page);
            }
          }
        ],
        remotecis: ['api', function(api) {
          return api.getRemoteCIS();
        }]
      }
    })
    .state('job', {
      url: '/jobs/:id',
      parent: 'auth',
      controller: 'JobCtrl',
      templateUrl: '/partials/job.html',
      resolve: {
        job: ['$stateParams', 'api', function($stateParams, api) {
          return api.getJob($stateParams.id);
        }]
      }
    })
    .state('login', {
      url: '/login',
      controller: 'LoginCtrl',
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
        if (error.status == 401) {
          auth.state = authStates.UNAUTHORIZED;
          $state.go('login');
        }
        if (error === authStates.DISCONNECTED) {
          $state.go('login', {}, {reload: true});
        }
      }
    );
  }
]);
