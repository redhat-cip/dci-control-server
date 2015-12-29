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
          if (!auth.isAuthenticated()) {
            return $q.reject({status: 401});
          }
        }]
      },
      controller: 'authCtrl',
      templateUrl: '/partials/auth.html'
    })
    .state('authAdmin', {
      'abstract': true,
      parent: 'auth',
      template: '<ui-view></ui-view>',
      resolve: {
        _: ['auth', '$q', function(auth, $q) {
          if (!auth.isAdmin()) {
            return $q.reject({status: 401});
          }
        }]
      }
    })
    .state('index', {
      url: '/',
      parent: 'auth',
      resolve: {
        _: ['$q', function($q) {
          return $q.reject({status: 301})
        }]
      }
    })
    .state('jobs', {
      parent: 'auth',
      url: '/jobs?status&remoteci&page',
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
      parent: 'auth',
      url: '/jobs/:id',
      controller: 'JobCtrl',
      templateUrl: '/partials/job.html',
      resolve: {
        job: ['$stateParams', 'api', function($stateParams, api) {
          return api.getJob($stateParams.id);
        }]
      }
    })
    .state('administrate', {
      parent: 'authAdmin',
      url: '/administrate',
      controller: 'AdminCtrl',
      templateUrl: '/partials/admin.html',
      resolve: {
        teams: ['api', function(api) {
          return api.getTeams();
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
    // currently just create roles and user when admin
    $scope.admin = auth.isAdmin();

    $scope.logout = function () {
      auth.logout();
      $state.go('login');
    }
  }
])

.run([
  '$rootScope', '$state', '$log', function($rootScope, $state, $log) {
    $rootScope.$on('$stateChangeError', function(e, tS, tPs, fS, fPs, err) {
      if (err.status === 401) {
        $state.go('login', {}, {reload: true});
      } else if (err.status == 301) {
        $state.go('jobs', {}, {reload: true, inherit: false});
      } else {
        $log.error(err);
      }
    });
  }
]);
