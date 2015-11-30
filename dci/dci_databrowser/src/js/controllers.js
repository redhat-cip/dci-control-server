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
.controller('LoginCtrl', [
  '$scope', '$state', 'auth', 'authStates',
  function($scope, $state, auth, authStates) {
    $scope.authenticate = function(credentials) {
      auth.login(credentials.username, credentials.password);
      $state.go('index');
    }
    $scope.unauthorized = auth.state == authStates.UNAUTHORIZED;
  }
])

.controller('ListJobsCtrl', [
  '$injector', '$scope', 'jobs', 'remotecis', 'page',
  function($injector, $scope, jobs, remotecis, page) {
    var _ = $injector.get('_');
    var $state = $injector.get('$state');
    var statuses = ['failure', 'success', 'ongoing', 'new',
                    'initializing', 'killed', 'unfinished'];
    $scope.page = page;
    $scope.jobs = jobs.jobs;
    $scope.remotecis = {};
    $scope.status = {};
    _.each(statuses, function(status) {
      this[status] = _.contains($state.params.status, status);
    }, $scope.status);

    _.each(remotecis, function(remoteci) {
      var remoteci = remoteci.name;
      this[remoteci] = _.contains($state.params.remoteci, remoteci);
    }, $scope.remotecis);

    $scope.search = function () {
      var params = {
        'status': _($scope.status).pick(_.identity).keys().join(','),
        'remoteci': _($scope.remotecis).pick(_.identity).keys().join(',')
      }
      $state.go('jobs', params);
    }

    if (!$state.params.status.length && !$state.params.remoteci.length) {
      var total = $scope.total = Math.ceil(jobs._meta.count / 20);
      var go = function(page) {
        return function () {
          $state.go('jobs', {
            'page': page > total && total || page > 0 && page || 1
          });
        }
      }

      $scope.previous = go(page - 1);
      $scope.next = go(page + 1);
    }
  }
])
.controller('JobCtrl', ['$scope', 'job', function($scope, job) {
  $scope.job = job;
}])
.controller('JobRecheckCtrl', [
  '$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.recheck = function(job) {
      api.recheckJob(job).then(function(job) {
        $state.go('job', {'id': job.id});
      });
    }
  }
]);
